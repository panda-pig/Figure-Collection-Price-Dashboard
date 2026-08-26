# フィギュア商品比較・コレクション価格管理システム

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

Flask + SQLite/PostgreSQL で構築した、フィギュア商品情報・所有状況・購入計画・価格記録を管理する Web アプリです。

デモ: https://figure-dashboard-deploy.vercel.app

## 概要

Figure Collection & Price Dashboard は、フィギュア収集を小さなデータ管理・可視化システムにまとめたものです。商品検索、所有状況の管理、店舗ごとの価格履歴に加え、ブランド分布・発売カレンダー・価格帯・購入金額・価格変動をダッシュボードで表示します。

## 機能

- ダッシュボードの指標カードと ECharts による可視化
- 商品一覧をキーワード・ブランド・作品・メーカー・発売月・状態・価格・限定・可動で絞り込み
- 商品の追加・編集・削除（専用ダイアログ付き）
- コレクション用ダイアログ（状態・購入価格・購入店舗・購入日・展示場所・開封状態・メモ）
- 商品詳細ページ（商品情報・コレクション情報・価格推移・価格記録）
- 価格変動バッジ（初回記録・上昇・下落・変化なし）。SQL のウィンドウ関数で算出するため、絞り込みやページングをしても正しく表示されます
- 一覧系 API はすべてページング対応
- 商品・価格記録・コレクションの CSV インポート
- ローカルは SQLite、本番は `DATABASE_URL` で PostgreSQL
- 中国語・日本語・英語の切り替え（表示中の言語辞書のみ読み込み）

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

## ローカル実行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run
```

ブラウザで開きます:

```txt
http://127.0.0.1:5000
```

`flask --app app init-db` を省略しても、最初のリクエスト時に `database.db` が作成されサンプル CSV が取り込まれます。

### データベースコマンド

| コマンド | 動作 |
|---|---|
| `flask --app app init-db` | 不足しているテーブルを作成し、空の場合のみサンプルデータを投入します。**既存データは削除しません**。何度実行しても安全です。 |
| `flask --app app reset-db` | 全テーブルを削除して再作成し、サンプルデータを再投入します。**既存データはすべて失われます。** |

## 永続データベース

ローカル開発では既定で SQLite を使用します:

```txt
database.db
```

本番でデータを永続化する場合は `DATABASE_URL` に PostgreSQL を指定します:

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
flask --app app init-db
flask --app app run
```

Vercel では Project Settings → Environment Variables で `DATABASE_URL` を追加します。Neon、Supabase、Render Postgres などの標準的な PostgreSQL サービスが利用できます。

> **注意:** Vercel で `DATABASE_URL` を設定しない場合、`/tmp` 配下の一時的な SQLite にフォールバックします。このデータベースはコールドスタートのたびに作り直されるため、書き込んだデータは残りません。永続化するには `DATABASE_URL` の設定が必須です。

## 書き込み権限

参照系 API は常に公開です。書き込み系（POST / PUT / DELETE）は以下のルールに従います:

| 環境 | `FIGURE_DASHBOARD_TOKEN` | 書き込み |
|---|---|---|
| ローカル開発 | 未設定 | そのまま許可（設定不要） |
| デプロイ環境（`VERCEL=1`） | 未設定 | 読み取り専用。書き込みは 403 |
| すべて | 設定済み | `X-Auth-Token` ヘッダーが必要。無い場合は 401 |

設定方法:

```bash
export FIGURE_DASHBOARD_TOKEN="your-long-random-token"
```

ブラウザではサイドバー下部に「書き込み権限」パネルが表示されます。「ロック解除」からトークンを入力すると `localStorage` に保存されます。ロック中は追加・編集・削除のボタンは表示されません。

## 主な API

```txt
GET    /api/config
GET    /api/dashboard
GET    /api/options
GET    /api/figures              # ページング
GET    /api/figures/<id>
POST   /api/figures
PUT    /api/figures/<id>
DELETE /api/figures/<id>
GET    /api/collection           # ページング
POST   /api/collection
PUT    /api/collection/<id>      # 部分更新
DELETE /api/collection/<id>
GET    /api/prices               # ページング
GET    /api/prices/<figure_id>
POST   /api/prices
DELETE /api/prices/<id>
```

一覧系 API は `page` と `per_page`（既定 50、最大 200）を受け取り、次の形式で返します:

```json
{ "items": [], "total": 0, "page": 1, "per_page": 50, "pages": 1 }
```

`PUT /api/collection/<id>` と `PUT /api/figures/<id>` はリクエストボディに含まれるフィールドのみ更新し、含まれないフィールドは元の値を保持します。

## 開発

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
```

CI では SQLite と実際の PostgreSQL の両方で同じテストを実行するため、片方の方言でしか動かない SQL は本番ではなく CI で失敗します。

## CSV インポート

データベース初期化後、追加の CSV データを取り込めます:

```bash
python scripts/import_figures.py data/figures.csv
python scripts/import_prices.py data/price_records.csv
python scripts/import_collection.py data/collection.csv
```

MVP では手作業で整理した CSV を使い、外部サイト構造の変化や高頻度スクレイピングへの依存を避けています。

## 今後の改善

- 画像アップロード
- 価格アラート
- 発売日リマインダー
- マルチユーザーログイン
- React でのフロントエンド刷新
- Docker 対応
- 低頻度の公式商品データ取り込み
