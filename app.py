from __future__ import annotations

import csv
import hashlib
import logging
import math
import os
import secrets
from collections.abc import Callable
from datetime import date
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Flask, g, jsonify, render_template, request
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Row
from werkzeug.exceptions import HTTPException

BASE_DIR = Path(__file__).resolve().parent
IS_SERVERLESS = bool(os.environ.get("VERCEL"))
DEFAULT_DB_PATH = Path("/tmp/figure_dashboard.db") if IS_SERVERLESS else BASE_DIR / "database.db"
DATABASE_FILE = Path(os.environ.get("FIGURE_DASHBOARD_DB", DEFAULT_DB_PATH))
RAW_DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASE_URL = RAW_DATABASE_URL or f"sqlite:///{DATABASE_FILE}"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
DB_KIND = "postgres" if DATABASE_URL.startswith("postgresql") else "sqlite"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
_schema_ready = False

# Writes are open with zero config for local development, but a public
# deployment stays read-only until FIGURE_DASHBOARD_TOKEN is configured.
WRITE_TOKEN = os.environ.get("FIGURE_DASHBOARD_TOKEN", "").strip()
WRITES_OPEN = not WRITE_TOKEN and not IS_SERVERLESS

DEFAULT_PER_PAGE = 50
MAX_PER_PAGE = 200
SEED_LOCK_KEY = 8621340117

app = Flask(__name__)
logger = logging.getLogger(__name__)


class ApiError(Exception):
    """A client-visible error carrying an HTTP status code."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def asset_version() -> str:
    """Content hash of the static bundle, used to bust immutable CDN caches."""
    digest = hashlib.sha256()
    static_dir = BASE_DIR / "static"
    for path in sorted(static_dir.rglob("*")):
        if path.is_file():
            digest.update(path.name.encode("utf-8"))
            digest.update(str(path.stat().st_mtime_ns).encode("utf-8"))
    return digest.hexdigest()[:12]


ASSET_VERSION = asset_version()


@app.context_processor
def inject_asset_version() -> dict[str, str]:
    return {"asset_version": ASSET_VERSION}


def get_db() -> Connection:
    if "db" not in g:
        g.db = engine.connect()
        if DB_KIND == "sqlite":
            g.db.execute(text("PRAGMA foreign_keys = ON"))
    return g.db


@app.teardown_appcontext
def close_db(_: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def prepare_sql(sql: str, params: tuple[Any, ...] | list[Any] | dict[str, Any] | None = None) -> tuple[Any, dict[str, Any]]:
    if params is None:
        return text(sql), {}
    if isinstance(params, dict):
        return text(sql), params
    bind_params: dict[str, Any] = {}
    prepared = sql
    for index, value in enumerate(params):
        name = f"p{index}"
        prepared = prepared.replace("?", f":{name}", 1)
        bind_params[name] = value
    return text(prepared), bind_params


def execute_db(db: Connection, sql: str, params: tuple[Any, ...] | list[Any] | dict[str, Any] | None = None):
    statement, bind_params = prepare_sql(sql, params)
    return db.execute(statement, bind_params)


def row_to_dict(row: Row[Any] | Any | None) -> dict[str, Any] | None:
    if row is None:
        return None
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    return dict(row)


def row_value(row: Row[Any] | Any, key: str) -> Any:
    return row_to_dict(row)[key]


def result_insert_id(result) -> int | None:
    if result.returns_rows:
        row = result.fetchone()
        if row is not None:
            return int(row_value(row, "id"))
    return int(result.lastrowid) if result.lastrowid is not None else None


def int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ApiError("expected an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ApiError(f"expected an integer, got {value!r}") from error
    if isinstance(value, float) and parsed != value:
        raise ApiError("expected a whole number")
    if not -2147483648 <= parsed <= 2147483647:
        raise ApiError("integer is outside the supported range")
    return parsed


def nonnegative_int_or_none(value: Any) -> int | None:
    parsed = int_or_none(value)
    if parsed is not None and parsed < 0:
        raise ApiError("value must not be negative")
    return parsed


def bool_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    normalized = str(value).lower()
    if normalized in {"1", "true", "yes", "on"}:
        return 1
    if normalized in {"0", "false", "no", "off"}:
        return 0
    raise ApiError("expected a boolean")


def text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ApiError("expected text")
    value = value.strip()
    return value or None


def date_or_none(value: Any, allow_month: bool = False) -> str | None:
    value = text_or_none(value)
    if value is None:
        return None
    candidate = f"{value}-01" if allow_month and len(value) == 7 else value
    try:
        parsed = date.fromisoformat(candidate)
    except ValueError as error:
        raise ApiError("expected a valid ISO date") from error
    if parsed.isoformat() != candidate:
        raise ApiError("expected YYYY-MM-DD")
    return value


def release_date_or_none(value: Any) -> str | None:
    return date_or_none(value, allow_month=True)


OWNERSHIP_STATUSES = ("欲しい", "予約済み", "所持", "売却済み", "見送り", "高すぎる")


def ownership_status(value: Any) -> str:
    value = required_text(value)
    if value not in OWNERSHIP_STATUSES:
        raise ApiError("invalid ownership status")
    return value


def required_text(value: Any) -> str:
    cleaned = text_or_none(value)
    if cleaned is None:
        raise ApiError("value must not be empty")
    return cleaned


def int_arg(name: str, default: int | None = None, minimum: int | None = None, maximum: int | None = None) -> int | None:
    """Read an integer query parameter, rejecting junk with 400 instead of 500."""
    raw = request.args.get(name)
    if raw in (None, ""):
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ApiError(f"'{name}' must be an integer") from error
    if minimum is not None and value < minimum:
        raise ApiError(f"'{name}' must be >= {minimum}")
    if maximum is not None and value > maximum:
        value = maximum
    return value


def json_body() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("request body must be a JSON object")
    return data


def like_pattern(value: str) -> str:
    """Escape LIKE wildcards so a literal % or _ does not match everything."""
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped.lower()}%"


def write_guard(view: Callable) -> Callable:
    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any):
        if WRITES_OPEN:
            return view(*args, **kwargs)
        if not WRITE_TOKEN:
            raise ApiError(
                "this deployment is read-only; set FIGURE_DASHBOARD_TOKEN to enable writes",
                status=403,
            )
        supplied = request.headers.get("X-Auth-Token", "")
        if not supplied or not secrets.compare_digest(supplied, WRITE_TOKEN):
            raise ApiError("a valid X-Auth-Token header is required", status=401)
        return view(*args, **kwargs)

    return wrapper


@app.errorhandler(ApiError)
def handle_api_error(error: ApiError):
    return jsonify({"error": error.message}), error.status


@app.errorhandler(HTTPException)
def handle_http_exception(error: HTTPException):
    if request.path.startswith("/api/"):
        return jsonify({"error": error.description}), error.code or 500
    return error.get_response()


@app.errorhandler(Exception)
def handle_unexpected(error: Exception):
    logger.exception("unhandled error on %s %s", request.method, request.path)
    if app.debug or app.testing:
        raise error
    if request.path.startswith("/api/"):
        return jsonify({"error": "internal server error"}), 500
    return "Internal Server Error", 500


def run_sql_script(db: Connection, sql: str) -> None:
    for statement in sql.split(";"):
        if statement.strip():
            execute_db(db, statement)


def drop_tables(db: Connection) -> None:
    for table_name in ("collection", "price_records", "figures"):
        execute_db(db, f"DROP TABLE IF EXISTS {table_name}")


def init_database(seed: bool = True, reset: bool = False) -> None:
    """Create the schema if missing. `reset=True` destroys existing data."""
    schema_name = "schema_postgres.sql" if DB_KIND == "postgres" else "schema.sql"
    schema = (BASE_DIR / schema_name).read_text(encoding="utf-8")
    with engine.begin() as db:
        if DB_KIND == "sqlite":
            execute_db(db, "PRAGMA foreign_keys = ON")
        else:
            # Serialise concurrent cold starts so seeding cannot run twice.
            execute_db(db, "SELECT pg_advisory_xact_lock(:key)", {"key": SEED_LOCK_KEY})
        if reset:
            drop_tables(db)
        run_sql_script(db, schema)
        if seed and table_count(db, "figures") == 0:
            import_figures(db, BASE_DIR / "data" / "figures.csv")
            import_prices(db, BASE_DIR / "data" / "price_records.csv")
            import_collection(db, BASE_DIR / "data" / "collection.csv")


def table_count(db: Connection, table_name: str) -> int:
    row = execute_db(db, f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    return int(row_value(row, "count"))


def import_figures(db: Connection, csv_path: Path) -> None:
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            execute_db(
                db,
                """
                INSERT INTO figures (
                    name, brand, series_title, manufacturer, release_date,
                    official_price, height_mm, scale, is_articulated, is_limited,
                    status, product_url, image_url, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["name"],
                    row.get("brand"),
                    row.get("series_title"),
                    row.get("manufacturer"),
                    row.get("release_date"),
                    int_or_none(row.get("official_price")),
                    int_or_none(row.get("height_mm")),
                    row.get("scale"),
                    bool_int(row.get("is_articulated")),
                    bool_int(row.get("is_limited")),
                    row.get("status"),
                    row.get("product_url"),
                    row.get("image_url"),
                    row.get("source"),
                ),
            )


def figure_id_by_name(db: Connection, name: str) -> int:
    row = execute_db(db, "SELECT id FROM figures WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise ValueError(f"Figure not found: {name}")
    return int(row_value(row, "id"))


def import_prices(db: Connection, csv_path: Path) -> None:
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            execute_db(
                db,
                """
                INSERT INTO price_records (
                    figure_id, shop_name, price, condition, stock_status,
                    checked_date, product_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    figure_id_by_name(db, row["figure_name"]),
                    row["shop_name"],
                    int(row["price"]),
                    row.get("condition"),
                    row.get("stock_status"),
                    row["checked_date"],
                    row.get("product_url"),
                ),
            )


def import_collection(db: Connection, csv_path: Path) -> None:
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            execute_db(
                db,
                """
                INSERT INTO collection (
                    figure_id, ownership_status, purchase_price, purchase_shop,
                    purchase_date, is_opened, display_location, memo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    figure_id_by_name(db, row["figure_name"]),
                    row["ownership_status"],
                    int_or_none(row.get("purchase_price")),
                    row.get("purchase_shop") or None,
                    row.get("purchase_date") or None,
                    bool_int(row.get("is_opened")),
                    row.get("display_location") or None,
                    row.get("memo") or None,
                ),
            )


def ensure_database() -> None:
    global _schema_ready
    if _schema_ready:
        return
    init_database(seed=True, reset=False)
    _schema_ready = True


@app.before_request
def before_request() -> None:
    ensure_database()


def paged_response(
    db: Connection,
    columns: str,
    from_where: str,
    params: list[Any],
    order_by: str,
) -> Any:
    """Run a filtered query as `{items, total, page, per_page, pages}`."""
    page = int_arg("page", default=1, minimum=1) or 1
    per_page = int_arg("per_page", default=DEFAULT_PER_PAGE, minimum=1, maximum=MAX_PER_PAGE) or DEFAULT_PER_PAGE

    total_row = execute_db(db, f"SELECT COUNT(*) AS count {from_where}", params).fetchone()
    total = int(row_value(total_row, "count"))
    pages = max(1, math.ceil(total / per_page))
    page = min(page, pages)

    rows = execute_db(
        db,
        f"SELECT {columns} {from_where} {order_by} LIMIT ? OFFSET ?",
        [*params, per_page, (page - 1) * per_page],
    ).fetchall()

    return jsonify(
        {
            "items": [row_to_dict(row) for row in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }
    )


@app.route("/")
def dashboard_page() -> str:
    return render_template("index.html", page="dashboard")


@app.route("/figures")
def figures_page() -> str:
    return render_template("figures.html", page="figures")


@app.route("/figures/<int:figure_id>")
def figure_detail_page(figure_id: int) -> str:
    if execute_db(get_db(), "SELECT id FROM figures WHERE id = ?", (figure_id,)).fetchone() is None:
        raise ApiError("figure not found", status=404)
    return render_template("figure_detail.html", page="figures", figure_id=figure_id)


@app.route("/collection")
def collection_page() -> str:
    return render_template("collection.html", page="collection")


@app.route("/prices")
def prices_page() -> str:
    return render_template("prices.html", page="prices")


@app.get("/api/config")
def api_config():
    """Lets the UI know whether it should offer write controls."""
    return jsonify({"writes_open": WRITES_OPEN, "auth_required": bool(WRITE_TOKEN)})


FIGURE_FIELDS: dict[str, Callable[[Any], Any]] = {
    "name": required_text,
    "brand": text_or_none,
    "series_title": text_or_none,
    "manufacturer": text_or_none,
    "release_date": release_date_or_none,
    "official_price": nonnegative_int_or_none,
    "height_mm": nonnegative_int_or_none,
    "scale": text_or_none,
    "is_articulated": bool_int,
    "is_limited": bool_int,
    "status": text_or_none,
    "product_url": text_or_none,
    "image_url": text_or_none,
    "source": text_or_none,
}

COLLECTION_FIELDS: dict[str, Callable[[Any], Any]] = {
    "ownership_status": ownership_status,
    "purchase_price": nonnegative_int_or_none,
    "purchase_shop": text_or_none,
    "purchase_date": date_or_none,
    "is_opened": bool_int,
    "display_location": text_or_none,
    "memo": text_or_none,
}


def parse_fields(data: dict[str, Any], schema: dict[str, Callable[[Any], Any]]) -> dict[str, Any]:
    """Coerce only the keys the caller actually sent, so PATCH stays partial."""
    parsed: dict[str, Any] = {}
    for key, parser in schema.items():
        if key in data:
            try:
                parsed[key] = parser(data[key])
            except ApiError as error:
                raise ApiError(f"{key}: {error.message}") from error
    return parsed


@app.get("/api/figures")
def get_figures():
    from_where = "FROM figures WHERE 1=1"
    params: list[Any] = []

    exact_filters = {
        "brand": "brand",
        "series_title": "series_title",
        "manufacturer": "manufacturer",
        "release_date": "release_date",
        "is_limited": "is_limited",
        "is_articulated": "is_articulated",
        "status": "status",
    }
    for arg, column in exact_filters.items():
        value = request.args.get(arg)
        if value not in (None, ""):
            from_where += f" AND {column} = ?"
            params.append(value)

    release_month = request.args.get("release_month")
    if release_month:
        from_where += " AND substr(release_date, 1, 7) = ?"
        params.append(release_month)

    keyword = request.args.get("keyword")
    if keyword:
        from_where += r"""
            AND (
                LOWER(name) LIKE ? ESCAPE '\'
                OR LOWER(COALESCE(brand, '')) LIKE ? ESCAPE '\'
                OR LOWER(COALESCE(series_title, '')) LIKE ? ESCAPE '\'
                OR LOWER(COALESCE(manufacturer, '')) LIKE ? ESCAPE '\'
            )
        """
        like = like_pattern(keyword)
        params.extend([like, like, like, like])

    min_price = int_arg("min_price")
    max_price = int_arg("max_price")
    if min_price is not None:
        from_where += " AND official_price >= ?"
        params.append(min_price)
    if max_price is not None:
        from_where += " AND official_price <= ?"
        params.append(max_price)

    order_by = "ORDER BY (release_date IS NULL), release_date, brand, name"
    return paged_response(get_db(), "*", from_where, params, order_by)


@app.get("/api/figures/<int:figure_id>")
def get_figure(figure_id: int):
    row = execute_db(get_db(), "SELECT * FROM figures WHERE id = ?", (figure_id,)).fetchone()
    if row is None:
        raise ApiError("figure not found", status=404)
    return jsonify(row_to_dict(row))


@app.post("/api/figures")
@write_guard
def create_figure():
    data = json_body()
    if not text_or_none(data.get("name")):
        raise ApiError("name is required")
    values = parse_fields(data, FIGURE_FIELDS)
    values.setdefault("is_articulated", 0)
    values.setdefault("is_limited", 0)
    values.setdefault("source", "manual")

    columns = ", ".join(values)
    placeholders = ", ".join(f":{key}" for key in values)
    result = execute_db(
        get_db(),
        f"INSERT INTO figures ({columns}) VALUES ({placeholders}) RETURNING id",
        values,
    )
    figure_id = result_insert_id(result)
    get_db().commit()
    return jsonify({"id": figure_id}), 201


@app.put("/api/figures/<int:figure_id>")
@write_guard
def update_figure(figure_id: int):
    data = json_body()
    existing = execute_db(get_db(), "SELECT id FROM figures WHERE id = ?", (figure_id,)).fetchone()
    if existing is None:
        raise ApiError("figure not found", status=404)
    values = parse_fields(data, FIGURE_FIELDS)
    if not values:
        raise ApiError("no updatable fields supplied")

    assignments = ", ".join(f"{key} = :{key}" for key in values)
    execute_db(
        get_db(),
        f"UPDATE figures SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = :figure_id",
        {**values, "figure_id": figure_id},
    )
    get_db().commit()
    return jsonify({"status": "updated"})


@app.delete("/api/figures/<int:figure_id>")
@write_guard
def delete_figure(figure_id: int):
    result = execute_db(get_db(), "DELETE FROM figures WHERE id = ?", (figure_id,))
    get_db().commit()
    if result.rowcount == 0:
        raise ApiError("figure not found", status=404)
    return jsonify({"status": "deleted"})


@app.get("/api/collection")
def get_collection():
    from_where = """
        FROM collection c
        JOIN figures f ON f.id = c.figure_id
        WHERE 1=1
    """
    params: list[Any] = []
    figure_id = int_arg("figure_id")
    ownership_status = request.args.get("ownership_status")
    brand = request.args.get("brand")
    if figure_id is not None:
        from_where += " AND c.figure_id = ?"
        params.append(figure_id)
    if ownership_status:
        from_where += " AND c.ownership_status = ?"
        params.append(ownership_status)
    if brand:
        from_where += " AND f.brand = ?"
        params.append(brand)

    columns = """
        c.*,
        f.name,
        f.brand,
        f.series_title,
        f.manufacturer,
        f.release_date,
        f.official_price,
        f.status AS figure_status
    """
    return paged_response(get_db(), columns, from_where, params, "ORDER BY c.updated_at DESC, c.id DESC")


@app.post("/api/collection")
@write_guard
def create_collection():
    data = json_body()
    figure_id = int_or_none(data.get("figure_id"))
    if figure_id is None:
        raise ApiError("figure_id is required")
    figure = execute_db(get_db(), "SELECT id FROM figures WHERE id = ?", (figure_id,)).fetchone()
    if figure is None:
        raise ApiError("figure not found", status=404)

    values = parse_fields(data, COLLECTION_FIELDS)
    updatable = list(values)
    values.setdefault("ownership_status", "欲しい")
    values.setdefault("is_opened", 0)
    values["figure_id"] = figure_id

    columns = ", ".join(values)
    placeholders = ", ".join(f":{key}" for key in values)
    assignments = ", ".join([*(f"{key} = excluded.{key}" for key in updatable), "updated_at = CURRENT_TIMESTAMP"])
    result = execute_db(
        get_db(),
        f"""
        INSERT INTO collection ({columns})
        VALUES ({placeholders})
        ON CONFLICT(figure_id) DO UPDATE SET
            {assignments}
        RETURNING id
        """,
        values,
    )
    collection_id = result_insert_id(result)
    get_db().commit()
    return jsonify({"id": collection_id, "status": "saved"}), 201


@app.put("/api/collection/<int:collection_id>")
@write_guard
def update_collection(collection_id: int):
    data = json_body()
    existing = execute_db(get_db(), "SELECT id FROM collection WHERE id = ?", (collection_id,)).fetchone()
    if existing is None:
        raise ApiError("collection record not found", status=404)

    values = parse_fields(data, COLLECTION_FIELDS)
    if not values:
        raise ApiError("no updatable fields supplied")

    assignments = ", ".join(f"{key} = :{key}" for key in values)
    execute_db(
        get_db(),
        f"""
        UPDATE collection
        SET {assignments}, updated_at = CURRENT_TIMESTAMP
        WHERE id = :collection_id
        """,
        {**values, "collection_id": collection_id},
    )
    get_db().commit()
    return jsonify({"status": "updated"})


@app.delete("/api/collection/<int:collection_id>")
@write_guard
def delete_collection(collection_id: int):
    result = execute_db(get_db(), "DELETE FROM collection WHERE id = ?", (collection_id,))
    get_db().commit()
    if result.rowcount == 0:
        raise ApiError("collection record not found", status=404)
    return jsonify({"status": "deleted"})


# `prev_price` is resolved in SQL so the up/down badge stays correct no matter
# how the client filters or paginates the result.
PRICE_HISTORY_SOURCE = """
    FROM (
        SELECT
            p.id,
            p.figure_id,
            p.shop_name,
            p.price,
            p.condition,
            p.stock_status,
            p.checked_date,
            p.product_url,
            p.created_at,
            f.name,
            f.brand,
            f.series_title,
            LAG(p.price) OVER (
                PARTITION BY p.figure_id, p.shop_name
                ORDER BY p.checked_date, p.id
            ) AS prev_price
        FROM price_records p
        JOIN figures f ON f.id = p.figure_id
        {inner_where}
    ) AS history
    WHERE 1=1
"""


@app.get("/api/prices")
def get_all_prices():
    figure_id = int_arg("figure_id")
    params: list[Any] = []
    # Filtering by figure inside the window is safe: the partition is already
    # scoped per figure, and it keeps the scan small.
    inner_where = ""
    if figure_id is not None:
        inner_where = "WHERE p.figure_id = ?"
        params.append(figure_id)

    from_where = PRICE_HISTORY_SOURCE.format(inner_where=inner_where)
    return paged_response(get_db(), "*", from_where, params, "ORDER BY history.checked_date DESC, history.id DESC")


@app.get("/api/prices/<int:figure_id>")
def get_prices_for_figure(figure_id: int):
    from_where = PRICE_HISTORY_SOURCE.format(inner_where="WHERE p.figure_id = ?")
    rows = execute_db(
        get_db(),
        f"SELECT * {from_where} ORDER BY history.checked_date, history.shop_name",
        [figure_id],
    ).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.post("/api/prices")
@write_guard
def create_price():
    data = json_body()
    figure_id = int_or_none(data.get("figure_id"))
    shop_name = text_or_none(data.get("shop_name"))
    price = nonnegative_int_or_none(data.get("price"))
    checked_date = date_or_none(data.get("checked_date"))

    missing = [
        name
        for name, value in (
            ("figure_id", figure_id),
            ("shop_name", shop_name),
            ("price", price),
            ("checked_date", checked_date),
        )
        if value is None
    ]
    if missing:
        raise ApiError(f"missing fields: {', '.join(missing)}")
    if price < 0:
        raise ApiError("price must not be negative")

    figure = execute_db(get_db(), "SELECT id FROM figures WHERE id = ?", (figure_id,)).fetchone()
    if figure is None:
        raise ApiError("figure not found", status=404)

    result = execute_db(
        get_db(),
        """
        INSERT INTO price_records (
            figure_id, shop_name, price, condition, stock_status, checked_date, product_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        RETURNING id
        """,
        (
            figure_id,
            shop_name,
            price,
            text_or_none(data.get("condition")),
            text_or_none(data.get("stock_status")),
            checked_date,
            text_or_none(data.get("product_url")),
        ),
    )
    price_id = result_insert_id(result)
    get_db().commit()
    return jsonify({"id": price_id}), 201


@app.delete("/api/prices/<int:price_id>")
@write_guard
def delete_price(price_id: int):
    result = execute_db(get_db(), "DELETE FROM price_records WHERE id = ?", (price_id,))
    get_db().commit()
    if result.rowcount == 0:
        raise ApiError("price record not found", status=404)
    return jsonify({"status": "deleted"})


@app.get("/api/dashboard")
def dashboard_data():
    db = get_db()
    cards = execute_db(
        db,
        """
        SELECT
            (SELECT COUNT(*) FROM figures) AS total_figures,
            (SELECT COUNT(*) FROM collection WHERE ownership_status = '所持') AS owned_count,
            (SELECT COUNT(*) FROM collection WHERE ownership_status = '欲しい') AS wishlist_count,
            (SELECT COUNT(*) FROM collection WHERE ownership_status = '予約済み') AS reserved_count,
            (SELECT COALESCE(SUM(purchase_price), 0) FROM collection WHERE ownership_status = '所持') AS total_purchase_amount,
            (SELECT COUNT(*) FROM figures WHERE is_limited = 1) AS limited_count
        """
    ).fetchone()

    # MIN() keeps this valid under Postgres' strict GROUP BY and resolves ties
    # on the same date to the cheapest shop, which is what a budget wants.
    latest_prices = """
        SELECT pr.figure_id, MIN(pr.price) AS price
        FROM price_records pr
        JOIN (
            SELECT figure_id, MAX(checked_date) AS checked_date
            FROM price_records
            GROUP BY figure_id
        ) latest ON latest.figure_id = pr.figure_id AND latest.checked_date = pr.checked_date
        GROUP BY pr.figure_id
    """
    wishlist_budget_row = execute_db(
        db,
        f"""
        SELECT COALESCE(SUM(COALESCE(lp.price, f.official_price, 0)), 0) AS total
        FROM collection c
        JOIN figures f ON f.id = c.figure_id
        LEFT JOIN ({latest_prices}) lp ON lp.figure_id = f.id
        WHERE c.ownership_status = '欲しい'
        """
    ).fetchone()
    wishlist_budget = row_value(wishlist_budget_row, "total")
    reserved_budget_row = execute_db(
        db,
        """
        SELECT COALESCE(SUM(COALESCE(c.purchase_price, f.official_price, 0)), 0) AS total
        FROM collection c
        JOIN figures f ON f.id = c.figure_id
        WHERE c.ownership_status = '予約済み'
        """
    ).fetchone()
    reserved_budget = row_value(reserved_budget_row, "total")
    month_sql = (
        "SELECT COUNT(*) AS count FROM figures WHERE substr(release_date, 1, 7) = strftime('%Y-%m', 'now')"
        if DB_KIND == "sqlite"
        else "SELECT COUNT(*) AS count FROM figures WHERE substr(release_date, 1, 7) = to_char(CURRENT_DATE, 'YYYY-MM')"
    )
    monthly_release_row = execute_db(db, month_sql).fetchone()
    monthly_release_count = row_value(monthly_release_row, "count")

    brand_distribution = execute_db(
        db,
        """
        SELECT COALESCE(brand, '未分類') AS brand, COUNT(*) AS count
        FROM figures
        GROUP BY COALESCE(brand, '未分類')
        ORDER BY count DESC, brand
        """
    ).fetchall()
    ownership_distribution = execute_db(
        db,
        """
        SELECT ownership_status AS status, COUNT(*) AS count
        FROM collection
        GROUP BY ownership_status
        ORDER BY count DESC, ownership_status
        """
    ).fetchall()
    monthly_releases = execute_db(
        db,
        """
        SELECT substr(release_date, 1, 7) AS month, COUNT(*) AS count
        FROM figures
        WHERE release_date IS NOT NULL AND release_date != ''
        GROUP BY substr(release_date, 1, 7)
        ORDER BY month
        """
    ).fetchall()
    # The derived table needs an explicit alias for Postgres, and rows without
    # a price must be excluded or NULL would silently land in the top bucket.
    price_buckets = execute_db(
        db,
        """
        SELECT bucket, COUNT(*) AS count
        FROM (
            SELECT CASE
                WHEN official_price < 5000 THEN '0-4,999'
                WHEN official_price < 10000 THEN '5,000-9,999'
                WHEN official_price < 20000 THEN '10,000-19,999'
                ELSE '20,000+'
            END AS bucket
            FROM figures
            WHERE official_price IS NOT NULL
        ) AS price_bands
        GROUP BY bucket
        ORDER BY CASE bucket
            WHEN '0-4,999' THEN 1
            WHEN '5,000-9,999' THEN 2
            WHEN '10,000-19,999' THEN 3
            ELSE 4
        END
        """
    ).fetchall()
    purchase_by_brand = execute_db(
        db,
        """
        SELECT COALESCE(f.brand, '未分類') AS brand, COALESCE(SUM(c.purchase_price), 0) AS amount
        FROM collection c
        JOIN figures f ON f.id = c.figure_id
        WHERE c.ownership_status = '所持'
        GROUP BY COALESCE(f.brand, '未分類')
        ORDER BY amount DESC, brand
        """
    ).fetchall()

    first_tracked_figure = execute_db(
        db,
        """
        SELECT f.id, f.name
        FROM figures f
        JOIN price_records p ON p.figure_id = f.id
        GROUP BY f.id, f.name
        HAVING COUNT(p.id) >= 2
        ORDER BY COUNT(p.id) DESC, f.id
        LIMIT 1
        """
    ).fetchone()

    payload = row_to_dict(cards) or {}
    payload.update(
        {
            "wishlist_budget": wishlist_budget,
            "reserved_budget": reserved_budget,
            "monthly_release_count": monthly_release_count,
            "brand_distribution": [row_to_dict(row) for row in brand_distribution],
            "ownership_distribution": [row_to_dict(row) for row in ownership_distribution],
            "monthly_releases": [row_to_dict(row) for row in monthly_releases],
            "price_buckets": [row_to_dict(row) for row in price_buckets],
            "purchase_by_brand": [row_to_dict(row) for row in purchase_by_brand],
            "default_trend_figure": row_to_dict(first_tracked_figure),
        }
    )
    return jsonify(payload)


@app.get("/api/options")
def options():
    db = get_db()
    fields = {
        "brands": "brand",
        "series": "series_title",
        "manufacturers": "manufacturer",
        "statuses": "status",
    }
    result: dict[str, Any] = {}
    for key, column in fields.items():
        rows = execute_db(
            db,
            f"SELECT DISTINCT {column} AS value FROM figures WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}"
        ).fetchall()
        result[key] = [row_value(row, "value") for row in rows]
    release_rows = execute_db(
        db,
        """
        SELECT DISTINCT substr(release_date, 1, 7) AS value
        FROM figures
        WHERE release_date IS NOT NULL AND release_date != ''
        ORDER BY value
        """,
    ).fetchall()
    result["release_months"] = [row_value(row, "value") for row in release_rows]
    result["ownership_statuses"] = list(OWNERSHIP_STATUSES)
    # Ships the id/name pairs the dropdowns need, so pages no longer pull the
    # whole figures table just to populate a <select>.
    figure_rows = execute_db(db, "SELECT id, name FROM figures ORDER BY name").fetchall()
    result["figures"] = [row_to_dict(row) for row in figure_rows]
    return jsonify(result)


@app.cli.command("init-db")
def init_db_command() -> None:
    """Create any missing tables and seed sample data on an empty database."""
    init_database(seed=True, reset=False)
    print(f"Initialized {DATABASE_URL}")


@app.cli.command("reset-db")
def reset_db_command() -> None:
    """Drop every table and re-seed. Destroys all existing data."""
    init_database(seed=True, reset=True)
    print(f"Reset {DATABASE_URL}")


if __name__ == "__main__":
    ensure_database()
    app.run(debug=True)
