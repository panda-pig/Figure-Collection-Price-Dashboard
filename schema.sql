PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS collection;
DROP TABLE IF EXISTS price_records;
DROP TABLE IF EXISTS figures;

CREATE TABLE figures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand TEXT,
    series_title TEXT,
    manufacturer TEXT,
    release_date TEXT,
    official_price INTEGER,
    height_mm INTEGER,
    scale TEXT,
    is_articulated INTEGER DEFAULT 0,
    is_limited INTEGER DEFAULT 0,
    status TEXT,
    product_url TEXT,
    image_url TEXT,
    source TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE price_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    figure_id INTEGER NOT NULL,
    shop_name TEXT NOT NULL,
    price INTEGER NOT NULL,
    condition TEXT,
    stock_status TEXT,
    checked_date TEXT NOT NULL,
    product_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (figure_id) REFERENCES figures(id) ON DELETE CASCADE
);

CREATE TABLE collection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    figure_id INTEGER NOT NULL,
    ownership_status TEXT NOT NULL,
    purchase_price INTEGER,
    purchase_shop TEXT,
    purchase_date TEXT,
    is_opened INTEGER DEFAULT 0,
    display_location TEXT,
    memo TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (figure_id) REFERENCES figures(id) ON DELETE CASCADE,
    UNIQUE (figure_id)
);

CREATE INDEX idx_figures_brand ON figures(brand);
CREATE INDEX idx_figures_release_date ON figures(release_date);
CREATE INDEX idx_price_records_figure_date ON price_records(figure_id, checked_date);
CREATE INDEX idx_collection_status ON collection(ownership_status);
