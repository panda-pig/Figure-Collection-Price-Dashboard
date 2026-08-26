# Figure Collection & Price Dashboard

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

A Flask + SQLite/PostgreSQL web app for managing figure product data, ownership status, purchase plans, and price history.

Live demo: https://figure-dashboard-deploy.vercel.app

## Overview

Figure Collection & Price Dashboard turns figure collecting into a small data management and visualisation system. It covers product search, an ownership workflow, price history across shops, and dashboard charts for brand mix, release calendar, price bands, collection spend, and price movement.

## Features

- Dashboard metric cards and ECharts visualisations
- Figure list filtered by keyword, brand, series, manufacturer, release month, status, price, limited, and articulation
- Full figure CRUD with create/edit dialogs
- Collection dialog for status, purchase price, shop, date, display location, opened state, and memo
- Figure detail page with product info, ownership record, price trend, and price history
- Price movement badges: first record, up, down, flat — computed with a SQL window function, so they stay correct under filtering and pagination
- All list endpoints are paginated instead of returning whole tables
- CSV import for figures, price records, and collection rows
- SQLite locally, PostgreSQL in production via `DATABASE_URL`
- Chinese / Japanese / English UI, loading only the active language dictionary

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
├── requirements-dev.txt
├── pyproject.toml
├── vercel.json
├── data/
│   ├── figures.csv
│   ├── price_records.csv
│   └── collection.csv
├── scripts/
│   ├── import_figures.py
│   ├── import_prices.py
│   └── import_collection.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_i18n.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── figures.html
│   ├── figure_detail.html
│   ├── collection.html
│   └── prices.html
└── static/
    ├── css/style.css
    ├── i18n/{zh,ja,en}.json
    └── js/
        ├── app.js
        ├── dashboard.js
        ├── figures.js
        ├── figure-detail.js
        ├── collection.js
        └── prices.js
```

## Running Locally

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

Skipping `flask --app app init-db` is fine — the app creates `database.db` and imports the sample CSVs on the first request.

### Database commands

| Command | Behaviour |
|---|---|
| `flask --app app init-db` | Creates missing tables and seeds sample data when the database is empty. **Never drops existing data**, safe to re-run. |
| `flask --app app reset-db` | Drops every table, rebuilds, and re-seeds. **Destroys all data.** |

## Persistent Database

Local development uses SQLite by default:

```txt
database.db
```

For persistent production data, point `DATABASE_URL` at PostgreSQL:

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
flask --app app init-db
flask --app app run
```

On Vercel, add `DATABASE_URL` under Project Settings → Environment Variables. Neon, Supabase, Render Postgres, or any standard PostgreSQL service works.

> **Note:** without `DATABASE_URL`, a Vercel deployment falls back to a temporary SQLite database under `/tmp`. That database is rebuilt on every cold start, so writes do not survive. Configure `DATABASE_URL` for real persistence.

## Write Access

Read endpoints are always public. Writes (POST / PUT / DELETE) follow these rules:

| Environment | `FIGURE_DASHBOARD_TOKEN` | Write behaviour |
|---|---|---|
| Local development | unset | Allowed, zero config |
| Deployment (`VERCEL=1`) | unset | Read-only, writes return 403 |
| Any | set | Requires an `X-Auth-Token` header, otherwise 401 |

Set it with:

```bash
export FIGURE_DASHBOARD_TOKEN="your-long-random-token"
```

In the browser a "Write access" panel appears at the bottom of the sidebar; click Unlock and paste the token, which is kept in `localStorage`. While locked, create/edit/delete controls stay hidden.

## Main API

```txt
GET    /api/config
GET    /api/dashboard
GET    /api/options
GET    /api/figures              # paginated
GET    /api/figures/<id>
POST   /api/figures
PUT    /api/figures/<id>
DELETE /api/figures/<id>
GET    /api/collection           # paginated
POST   /api/collection
PUT    /api/collection/<id>      # partial update
DELETE /api/collection/<id>
GET    /api/prices               # paginated
GET    /api/prices/<figure_id>
POST   /api/prices
DELETE /api/prices/<id>
```

List endpoints accept `page` and `per_page` (default 50, max 200) and respond with:

```json
{ "items": [], "total": 0, "page": 1, "per_page": 50, "pages": 1 }
```

`PUT /api/collection/<id>` and `PUT /api/figures/<id>` update only the fields present in the request body; omitted fields keep their current value.

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
```

CI runs the same suite against SQLite and against a real PostgreSQL service, so SQL that only works on one dialect fails in CI rather than on the deployed site.

## CSV Import

After initialising the database you can import more CSV data:

```bash
python scripts/import_figures.py data/figures.csv
python scripts/import_prices.py data/price_records.csv
python scripts/import_collection.py data/collection.csv
```

The MVP uses hand-curated CSV data to avoid depending on unstable external site structures or frequent scraping.

## Roadmap

- Image upload
- Price alerts
- Release-date reminders
- Multi-user login
- React frontend rewrite
- Docker packaging
- Low-frequency official product data import
