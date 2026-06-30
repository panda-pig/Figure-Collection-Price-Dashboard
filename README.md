# Figure Collection & Price Dashboard

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

A Flask + SQLite/PostgreSQL web app for managing figure product data, collection status, purchase plans, and price records.

Live demo: https://figure-dashboard-deploy.vercel.app

## Overview

Figure Collection & Price Dashboard turns figure collecting into a small data management and visualization system. It supports product search, collection workflow management, price history tracking, and dashboard charts for brand distribution, release months, price bands, purchase amount, and price movement.

## Features

- Dashboard with KPI cards and ECharts visualizations
- Product list with keyword, brand, series, manufacturer, release month, status, price, limited, and articulation filters
- Collection workflow with a modal form for status, purchase price, shop, date, display location, opened state, and memo
- Figure detail page with product facts, collection facts, price trend, and price records
- Price records with movement labels: first record, up, down, or unchanged
- CSV import scripts for figures, price records, and collection records
- Local SQLite support and production PostgreSQL support through `DATABASE_URL`
- Chinese, Japanese, and English UI language switcher

## Tech Stack

- Python
- Flask
- SQLAlchemy
- SQLite / PostgreSQL
- HTML / CSS
- JavaScript
- ECharts
- Vercel

## Project Structure

```txt
.
├── api/
│   └── index.py
├── app.py
├── schema.sql
├── schema_postgres.sql
├── requirements.txt
├── vercel.json
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
│   ├── figure_detail.html
│   ├── collection.html
│   └── prices.html
└── static/
    ├── css/style.css
    └── js/
        ├── app.js
        ├── dashboard.js
        ├── figures.js
        ├── figure-detail.js
        ├── collection.js
        └── prices.js
```

## How to Run Locally

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

If you skip `flask --app app init-db`, the app creates `database.db` automatically on first request and seeds it with the sample CSV data.

## Persistent Database

Local development uses SQLite by default:

```txt
database.db
```

For production persistence, set a PostgreSQL connection string with `DATABASE_URL`:

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
flask --app app init-db
flask --app app run
```

On Vercel, add `DATABASE_URL` in Project Settings → Environment Variables. Neon, Supabase, Render Postgres, or any standard PostgreSQL service works. If `DATABASE_URL` is not set on Vercel, the app falls back to a temporary SQLite demo database.

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

## Future Improvements

- Image upload
- Price alerts
- Release date reminders
- User authentication
- React frontend rewrite
- Docker setup
- Low-frequency official site data import
