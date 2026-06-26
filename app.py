from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

from flask import Flask, g, jsonify, render_template, request
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Row


BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = Path(os.environ.get("FIGURE_DASHBOARD_DB", "/tmp/figure_dashboard.db" if os.environ.get("VERCEL") else BASE_DIR / "database.db"))
RAW_DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASE_URL = RAW_DATABASE_URL or f"sqlite:///{DATABASE_FILE}"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
DB_KIND = "postgres" if DATABASE_URL.startswith("postgresql") else "sqlite"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
_schema_ready = False

app = Flask(__name__)


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
    return int(value)


def bool_int(value: Any) -> int:
    return 1 if str(value).lower() in {"1", "true", "yes", "on"} else 0


def run_sql_script(db: Connection, sql: str) -> None:
    for statement in sql.split(";"):
        if statement.strip():
            execute_db(db, statement)


def init_database(seed: bool = True, reset: bool = True) -> None:
    schema_name = "schema_postgres.sql" if DB_KIND == "postgres" else "schema.sql"
    schema = (BASE_DIR / schema_name).read_text(encoding="utf-8")
    with engine.begin() as db:
        if DB_KIND == "sqlite":
            execute_db(db, "PRAGMA foreign_keys = ON")
        if reset or DB_KIND == "postgres":
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
    if DB_KIND == "sqlite":
        if not DATABASE_FILE.exists():
            init_database(seed=True)
        return
    if not _schema_ready:
        init_database(seed=True, reset=False)
        _schema_ready = True


@app.before_request
def before_request() -> None:
    ensure_database()


@app.route("/")
def dashboard_page() -> str:
    return render_template("index.html", page="dashboard")


@app.route("/figures")
def figures_page() -> str:
    return render_template("figures.html", page="figures")


@app.route("/figures/<int:figure_id>")
def figure_detail_page(figure_id: int) -> str:
    return render_template("figure_detail.html", page="figures", figure_id=figure_id)


@app.route("/collection")
def collection_page() -> str:
    return render_template("collection.html", page="collection")


@app.route("/prices")
def prices_page() -> str:
    return render_template("prices.html", page="prices")


@app.get("/api/figures")
def get_figures():
    query = "SELECT * FROM figures WHERE 1=1"
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
            query += f" AND {column} = ?"
            params.append(value)

    release_month = request.args.get("release_month")
    if release_month:
        query += " AND substr(release_date, 1, 7) = ?"
        params.append(release_month)

    keyword = request.args.get("keyword")
    if keyword:
        query += """
            AND (
                name LIKE ? OR brand LIKE ? OR series_title LIKE ?
                OR manufacturer LIKE ?
            )
        """
        like = f"%{keyword}%"
        params.extend([like, like, like, like])

    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    if min_price:
        query += " AND official_price >= ?"
        params.append(int(min_price))
    if max_price:
        query += " AND official_price <= ?"
        params.append(int(max_price))

    query += " ORDER BY release_date IS NULL, release_date, brand, name"
    rows = execute_db(get_db(), query, params).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.get("/api/figures/<int:figure_id>")
def get_figure(figure_id: int):
    row = execute_db(get_db(), "SELECT * FROM figures WHERE id = ?", (figure_id,)).fetchone()
    if row is None:
        return jsonify({"error": "figure not found"}), 404
    return jsonify(row_to_dict(row))


@app.post("/api/figures")
def create_figure():
    data = request.get_json(force=True)
    if not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    result = execute_db(
        get_db(),
        """
        INSERT INTO figures (
            name, brand, series_title, manufacturer, release_date, official_price,
            height_mm, scale, is_articulated, is_limited, status, product_url,
            image_url, source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING id
        """,
        (
            data["name"],
            data.get("brand"),
            data.get("series_title"),
            data.get("manufacturer"),
            data.get("release_date"),
            int_or_none(data.get("official_price")),
            int_or_none(data.get("height_mm")),
            data.get("scale"),
            bool_int(data.get("is_articulated")),
            bool_int(data.get("is_limited")),
            data.get("status"),
            data.get("product_url"),
            data.get("image_url"),
            data.get("source", "manual"),
        ),
    )
    figure_id = result_insert_id(result)
    get_db().commit()
    return jsonify({"id": figure_id}), 201


@app.get("/api/collection")
def get_collection():
    query = """
        SELECT
            c.*,
            f.name,
            f.brand,
            f.series_title,
            f.manufacturer,
            f.release_date,
            f.official_price,
            f.status AS figure_status
        FROM collection c
        JOIN figures f ON f.id = c.figure_id
        WHERE 1=1
    """
    params: list[Any] = []
    figure_id = request.args.get("figure_id")
    ownership_status = request.args.get("ownership_status")
    brand = request.args.get("brand")
    if figure_id:
        query += " AND c.figure_id = ?"
        params.append(int(figure_id))
    if ownership_status:
        query += " AND c.ownership_status = ?"
        params.append(ownership_status)
    if brand:
        query += " AND f.brand = ?"
        params.append(brand)
    query += " ORDER BY c.updated_at DESC, c.id DESC"
    rows = execute_db(get_db(), query, params).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.post("/api/collection")
def create_collection():
    data = request.get_json(force=True)
    if not data.get("figure_id"):
        return jsonify({"error": "figure_id is required"}), 400
    ownership_status = data.get("ownership_status", "欲しい")
    result = execute_db(
        get_db(),
        """
        INSERT INTO collection (
            figure_id, ownership_status, purchase_price, purchase_shop,
            purchase_date, is_opened, display_location, memo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(figure_id) DO UPDATE SET
            ownership_status = excluded.ownership_status,
            purchase_price = excluded.purchase_price,
            purchase_shop = excluded.purchase_shop,
            purchase_date = excluded.purchase_date,
            is_opened = excluded.is_opened,
            display_location = excluded.display_location,
            memo = excluded.memo,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id
        """,
        (
            data["figure_id"],
            ownership_status,
            int_or_none(data.get("purchase_price")),
            data.get("purchase_shop"),
            data.get("purchase_date"),
            bool_int(data.get("is_opened")),
            data.get("display_location"),
            data.get("memo"),
        ),
    )
    collection_id = result_insert_id(result)
    get_db().commit()
    return jsonify({"id": collection_id, "status": "saved"}), 201


@app.put("/api/collection/<int:collection_id>")
def update_collection(collection_id: int):
    data = request.get_json(force=True)
    existing = execute_db(get_db(), "SELECT id FROM collection WHERE id = ?", (collection_id,)).fetchone()
    if existing is None:
        return jsonify({"error": "collection record not found"}), 404
    execute_db(
        get_db(),
        """
        UPDATE collection
        SET ownership_status = ?,
            purchase_price = ?,
            purchase_shop = ?,
            purchase_date = ?,
            is_opened = ?,
            display_location = ?,
            memo = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            data.get("ownership_status", "欲しい"),
            int_or_none(data.get("purchase_price")),
            data.get("purchase_shop"),
            data.get("purchase_date"),
            bool_int(data.get("is_opened")),
            data.get("display_location"),
            data.get("memo"),
            collection_id,
        ),
    )
    get_db().commit()
    return jsonify({"status": "updated"})


@app.delete("/api/collection/<int:collection_id>")
def delete_collection(collection_id: int):
    execute_db(get_db(), "DELETE FROM collection WHERE id = ?", (collection_id,))
    get_db().commit()
    return jsonify({"status": "deleted"})


@app.get("/api/prices")
def get_all_prices():
    figure_id = request.args.get("figure_id")
    params: list[Any] = []
    query = """
        SELECT p.*, f.name, f.brand, f.series_title
        FROM price_records p
        JOIN figures f ON f.id = p.figure_id
        WHERE 1=1
    """
    if figure_id:
        query += " AND p.figure_id = ?"
        params.append(int(figure_id))
    query += " ORDER BY p.checked_date DESC, p.id DESC"
    rows = execute_db(get_db(), query, params).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.get("/api/prices/<int:figure_id>")
def get_prices_for_figure(figure_id: int):
    rows = execute_db(
        get_db(),
        """
        SELECT p.*, f.name, f.brand
        FROM price_records p
        JOIN figures f ON f.id = p.figure_id
        WHERE p.figure_id = ?
        ORDER BY p.checked_date, p.shop_name
        """,
        (figure_id,),
    ).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.post("/api/prices")
def create_price():
    data = request.get_json(force=True)
    required = ["figure_id", "shop_name", "price", "checked_date"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400
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
            data["figure_id"],
            data["shop_name"],
            int(data["price"]),
            data.get("condition"),
            data.get("stock_status"),
            data["checked_date"],
            data.get("product_url"),
        ),
    )
    price_id = result_insert_id(result)
    get_db().commit()
    return jsonify({"id": price_id}), 201


@app.delete("/api/prices/<int:price_id>")
def delete_price(price_id: int):
    execute_db(get_db(), "DELETE FROM price_records WHERE id = ?", (price_id,))
    get_db().commit()
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

    latest_prices = """
        SELECT pr.figure_id, pr.price
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
    monthly_release_row = execute_db(
        db,
        month_sql,
    ).fetchone()
    monthly_release_count = row_value(monthly_release_row, "count")

    brand_distribution = execute_db(
        db,
        """
        SELECT COALESCE(brand, '未分類') AS brand, COUNT(*) AS count
        FROM figures
        GROUP BY COALESCE(brand, '未分類')
        ORDER BY count DESC
        """
    ).fetchall()
    ownership_distribution = execute_db(
        db,
        """
        SELECT ownership_status AS status, COUNT(*) AS count
        FROM collection
        GROUP BY ownership_status
        ORDER BY count DESC
        """
    ).fetchall()
    monthly_releases = execute_db(
        db,
        """
        SELECT substr(release_date, 1, 7) AS month, COUNT(*) AS count
        FROM figures
        WHERE release_date IS NOT NULL
        GROUP BY substr(release_date, 1, 7)
        ORDER BY month
        """
    ).fetchall()
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
        )
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
        SELECT f.brand, COALESCE(SUM(c.purchase_price), 0) AS amount
        FROM collection c
        JOIN figures f ON f.id = c.figure_id
        WHERE c.ownership_status = '所持'
        GROUP BY f.brand
        ORDER BY amount DESC
        """
    ).fetchall()

    first_tracked_figure = execute_db(
        db,
        """
        SELECT f.id, f.name
        FROM figures f
        JOIN price_records p ON p.figure_id = f.id
        GROUP BY f.id
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
    result: dict[str, list[str]] = {}
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
    result["ownership_statuses"] = ["欲しい", "予約済み", "所持", "売却済み", "見送り", "高すぎる"]
    return jsonify(result)


@app.cli.command("init-db")
def init_db_command() -> None:
    init_database(seed=True)
    print(f"Initialized {DATABASE_URL}")


if __name__ == "__main__":
    ensure_database()
    app.run(debug=True)
