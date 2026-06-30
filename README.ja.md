# フィギュア商品比較・コレクション管理ダッシュボード

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

Flask + SQLite/PostgreSQL で作成した Web アプリケーションです。フィギュアの商品情報、コレクション状況、購入予定、価格履歴を管理できます。

デモ：https://figure-dashboard-deploy.vercel.app

## 概要

Figure Collection & Price Dashboard は、フィギュア収集を小さなデータ管理・可視化システムとして整理するアプリです。商品検索、コレクション管理、価格履歴の記録、ブランド分布、発売月、価格帯、購入金額、価格変動の可視化に対応しています。

## 機能

- ダッシュボードの KPI カードと ECharts による可視化
- 商品一覧でキーワード、ブランド、作品、メーカー、発売月、商品状態、価格、限定、可動を絞り込み
- コレクション追加モーダルで、所有状態、購入価格、購入店舗、購入日、展示場所、開封状態、メモを登録
- 商品詳細ページで、商品情報、コレクション情報、価格推移、価格記録を表示
- 価格記録に初回記録、上昇、下落、変化なしのラベルを表示
- 商品、価格記録、コレクション記録を CSV からインポート
- ローカルは SQLite、本番環境は `DATABASE_URL` で PostgreSQL に対応
- UI は中国語、日本語、英語の切り替えに対応

## 技術スタック

- Python
- Flask
- SQLAlchemy
- SQLite / PostgreSQL
- HTML / CSS
- JavaScript
- ECharts
- Vercel

## ディレクトリ構成

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

## ローカル実行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run
```

起動後、次の URL を開きます。

```txt
http://127.0.0.1:5000
```

`flask --app app init-db` を実行しない場合でも、初回リクエスト時に `database.db` が自動作成され、サンプル CSV データが投入されます。

## 永続化データベース

ローカル開発では SQLite を使用します。

```txt
database.db
```

本番環境でデータを永続化する場合は、`DATABASE_URL` に PostgreSQL の接続文字列を設定します。

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
flask --app app init-db
flask --app app run
```

Vercel では Project Settings → Environment Variables に `DATABASE_URL` を追加します。Neon、Supabase、Render Postgres など標準的な PostgreSQL サービスを利用できます。`DATABASE_URL` が未設定の場合、Vercel 上では一時的な SQLite デモデータベースにフォールバックします。

## 主な API

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

## CSV インポート

データベース初期化後、追加 CSV をインポートできます。

```bash
python scripts/import_figures.py data/figures.csv
python scripts/import_prices.py data/price_records.csv
python scripts/import_collection.py data/collection.csv
```

MVP では手動整理した CSV データを利用し、不安定な外部サイト構造や高頻度スクレイピングに依存しない方針にしています。

## 今後の改善

- 画像アップロード
- 価格アラート
- 発売日リマインダー
- ユーザー認証
- React によるフロントエンド再構築
- Docker 対応
- 公式商品データの低頻度インポート
