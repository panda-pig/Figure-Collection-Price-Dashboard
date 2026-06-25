from __future__ import annotations

import csv
import os
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, g, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("FIGURE_DASHBOARD_DB", "/tmp/figure_dashboard.db" if os.environ.get("VERCEL") else BASE_DIR / "database.db"))

app = Flask(__name__)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def bool_int(value: Any) -> int:
    return 1 if str(value).lower() in {"1", "true", "yes", "on"} else 0


def init_database(seed: bool = True) -> None:
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    schema = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")
    db.executescript(schema)
    if seed:
        import_figures(db, BASE_DIR / "data" / "figures.csv")
        import_prices(db, BASE_DIR / "data" / "price_records.csv")
        import_collection(db, BASE_DIR / "data" / "collection.csv")
    db.commit()
    db.close()


def import_figures(db: sqlite3.Connection, csv_path: Path) -> None:
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            db.execute(
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


def figure_id_by_name(db: sqlite3.Connection, name: str) -> int:
    row = db.execute("SELECT id FROM figures WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise ValueError(f"Figure not found: {name}")
    return int(row["id"])


def import_prices(db: sqlite3.Connection, csv_path: Path) -> None:
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            db.execute(
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


def import_collection(db: sqlite3.Connection, csv_path: Path) -> None:
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            db.execute(
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
    if not DATABASE.exists():
        init_database(seed=True)


@app.before_request
def before_request() -> None:
    ensure_database()


@app.route("/")
def dashboard_page() -> str:
    return render_template("index.html", page="dashboard")


@app.route("/figures")
def figures_page() -> str:
    return render_template("figures.html", page="figures")


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
    rows = get_db().execute(query, params).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.get("/api/figures/<int:figure_id>")
def get_figure(figure_id: int):
    row = get_db().execute("SELECT * FROM figures WHERE id = ?", (figure_id,)).fetchone()
    if row is None:
        return jsonify({"error": "figure not found"}), 404
    return jsonify(row_to_dict(row))


@app.post("/api/figures")
def create_figure():
    data = request.get_json(force=True)
    if not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    cursor = get_db().execute(
        """
        INSERT INTO figures (
            name, brand, series_title, manufacturer, release_date, official_price,
            height_mm, scale, is_articulated, is_limited, status, product_url,
            image_url, source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    get_db().commit()
    return jsonify({"id": cursor.lastrowid}), 201


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
    ownership_status = request.args.get("ownership_status")
    brand = request.args.get("brand")
    if ownership_status:
        query += " AND c.ownership_status = ?"
        params.append(ownership_status)
    if brand:
        query += " AND f.brand = ?"
        params.append(brand)
    query += " ORDER BY c.updated_at DESC, c.id DESC"
    rows = get_db().execute(query, params).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.post("/api/collection")
def create_collection():
    data = request.get_json(force=True)
    if not data.get("figure_id"):
        return jsonify({"error": "figure_id is required"}), 400
    ownership_status = data.get("ownership_status", "欲しい")
    cursor = get_db().execute(
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
    get_db().commit()
    return jsonify({"id": cursor.lastrowid, "status": "saved"}), 201


@app.put("/api/collection/<int:collection_id>")
def update_collection(collection_id: int):
    data = request.get_json(force=True)
    existing = get_db().execute("SELECT id FROM collection WHERE id = ?", (collection_id,)).fetchone()
    if existing is None:
        return jsonify({"error": "collection record not found"}), 404
    get_db().execute(
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
    get_db().execute("DELETE FROM collection WHERE id = ?", (collection_id,))
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
    rows = get_db().execute(query, params).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.get("/api/prices/<int:figure_id>")
def get_prices_for_figure(figure_id: int):
    rows = get_db().execute(
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
    cursor = get_db().execute(
        """
        INSERT INTO price_records (
            figure_id, shop_name, price, condition, stock_status, checked_date, product_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
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
    get_db().commit()
    return jsonify({"id": cursor.lastrowid}), 201


@app.delete("/api/prices/<int:price_id>")
def delete_price(price_id: int):
    get_db().execute("DELETE FROM price_records WHERE id = ?", (price_id,))
    get_db().commit()
    return jsonify({"status": "deleted"})


@app.get("/api/dashboard")
def dashboard_data():
    db = get_db()
    cards = db.execute(
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
    wishlist_budget = db.execute(
        f"""
        SELECT COALESCE(SUM(COALESCE(lp.price, f.official_price, 0)), 0) AS total
        FROM collection c
        JOIN figures f ON f.id = c.figure_id
        LEFT JOIN ({latest_prices}) lp ON lp.figure_id = f.id
        WHERE c.ownership_status = '欲しい'
        """
    ).fetchone()["total"]
    reserved_budget = db.execute(
        """
        SELECT COALESCE(SUM(COALESCE(c.purchase_price, f.official_price, 0)), 0) AS total
        FROM collection c
        JOIN figures f ON f.id = c.figure_id
        WHERE c.ownership_status = '予約済み'
        """
    ).fetchone()["total"]
    monthly_release_count = db.execute(
        "SELECT COUNT(*) AS count FROM figures WHERE substr(release_date, 1, 7) = strftime('%Y-%m', 'now')"
    ).fetchone()["count"]

    brand_distribution = db.execute(
        """
        SELECT COALESCE(brand, '未分類') AS brand, COUNT(*) AS count
        FROM figures
        GROUP BY COALESCE(brand, '未分類')
        ORDER BY count DESC
        """
    ).fetchall()
    ownership_distribution = db.execute(
        """
        SELECT ownership_status AS status, COUNT(*) AS count
        FROM collection
        GROUP BY ownership_status
        ORDER BY count DESC
        """
    ).fetchall()
    monthly_releases = db.execute(
        """
        SELECT substr(release_date, 1, 7) AS month, COUNT(*) AS count
        FROM figures
        WHERE release_date IS NOT NULL
        GROUP BY substr(release_date, 1, 7)
        ORDER BY month
        """
    ).fetchall()
    price_buckets = db.execute(
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
    purchase_by_brand = db.execute(
        """
        SELECT f.brand, COALESCE(SUM(c.purchase_price), 0) AS amount
        FROM collection c
        JOIN figures f ON f.id = c.figure_id
        WHERE c.ownership_status = '所持'
        GROUP BY f.brand
        ORDER BY amount DESC
        """
    ).fetchall()

    first_tracked_figure = db.execute(
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
        rows = db.execute(
            f"SELECT DISTINCT {column} AS value FROM figures WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}"
        ).fetchall()
        result[key] = [row["value"] for row in rows]
    result["ownership_statuses"] = ["欲しい", "予約済み", "所持", "売却済み", "見送り", "高すぎる"]
    return jsonify(result)


@app.cli.command("init-db")
def init_db_command() -> None:
    init_database(seed=True)
    print(f"Initialized {DATABASE}")


if __name__ == "__main__":
    ensure_database()
    app.run(debug=True)
