# Figure Collection & Price Dashboard

A Flask + SQLite web app for managing figure product data, collection status, purchase plans, and price records.

## Overview

This project turns figure collecting into a small data management and visualization system. It supports product search, ownership status management, price history tracking, and dashboard charts for brand distribution, release months, price bands, and purchase amount.

Japanese name: フィギュア商品比較・コレクション管理ダッシュボード

## Features

- Dashboard with KPI cards and ECharts visualizations
- Product list with keyword, brand, series, price, limited, and articulation filters
- Collection management for 欲しい / 予約済み / 所持 / 売却済み / 見送り / 高すぎる
- Price record input for multiple shops and conditions
- CSV import scripts for figures, price records, and collection records
- SQLite schema with `figures`, `price_records`, and `collection`

## Tech Stack

- Python
- Flask
- SQLite
- HTML / CSS
- JavaScript
- ECharts

## Project Structure

```txt
.
├── app.py
├── schema.sql
├── requirements.txt
├── data/
│   ├── figures.csv
│   ├── price_records.csv
│   └── collection.csv
├── scripts/
│   ├── import_figures.py
│   ├── import_prices.py
│   └── import_collection.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── figures.html
│   ├── collection.html
│   └── prices.html
└── static/
    ├── css/style.css
    └── js/
        ├── app.js
        ├── dashboard.js
        ├── figures.js
        ├── collection.js
        └── prices.js
```

## How to Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run
```

Then open:

```txt
http://127.0.0.1:5000
```

If you skip `flask --app app init-db`, the app will create `database.db` automatically on first request and seed it with the sample CSV data.

## Main API Endpoints

```txt
GET    /api/dashboard
GET    /api/options
GET    /api/figures
GET    /api/figures/<id>
POST   /api/figures
GET    /api/collection
POST   /api/collection
PUT    /api/collection/<id>
DELETE /api/collection/<id>
GET    /api/prices
GET    /api/prices/<figure_id>
POST   /api/prices
DELETE /api/prices/<id>
```

## CSV Import

After initializing the database, you can import additional CSV files:

```bash
python scripts/import_figures.py data/figures.csv
python scripts/import_prices.py data/price_records.csv
python scripts/import_collection.py data/collection.csv
```

The MVP uses manual CSV data to avoid relying on unstable external sites or high-frequency scraping.

## Portfolio Summary

フィギュア商品情報、価格履歴、所有状況を SQLite で管理し、Flask API と JavaScript/ECharts によって検索・分析・可視化できる個人向け Web アプリケーションです。

## Future Improvements

- Product detail page
- Image upload
- Price alerts
- Release date reminders
- React frontend rewrite
- Docker setup
- Low-frequency official site data import
