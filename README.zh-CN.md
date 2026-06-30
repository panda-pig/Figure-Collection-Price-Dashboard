# 模型/手办商品比较与收藏价格管理系统

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

一个使用 Flask + SQLite/PostgreSQL 构建的 Web 应用，用于管理模型/手办商品信息、收藏状态、购买计划和价格记录。

线上演示：https://figure-dashboard-deploy.vercel.app

## 项目概述

Figure Collection & Price Dashboard 将模型/手办收藏场景做成一个小型数据管理与可视化系统。它支持商品搜索、收藏流程管理、价格历史记录，以及品牌分布、发售月份、价格区间、收藏金额和价格涨跌等仪表盘图表。

## 功能

- 仪表盘指标卡片与 ECharts 可视化
- 商品列表支持关键字、品牌、作品、厂商、发售月份、商品状态、价格、限定、可动筛选
- 收藏弹窗表单，支持状态、购买价格、购买平台、购买日期、展示位置、开封状态和备注
- 商品详情页，展示商品信息、收藏信息、价格趋势和价格记录
- 价格记录支持涨跌标签：首次记录、上涨、下降、持平
- 支持从 CSV 导入商品、价格记录和收藏记录
- 本地使用 SQLite，生产环境可通过 `DATABASE_URL` 使用 PostgreSQL
- 前端支持中文、日文、英文切换

## 技术栈

- Python
- Flask
- SQLAlchemy
- SQLite / PostgreSQL
- HTML / CSS
- JavaScript
- ECharts
- Vercel

## 项目结构

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

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run
```

然后打开：

```txt
http://127.0.0.1:5000
```

如果跳过 `flask --app app init-db`，应用会在第一次请求时自动创建 `database.db`，并导入示例 CSV 数据。

## 持久化数据库

本地开发默认使用 SQLite：

```txt
database.db
```

生产环境如果需要持久化数据，可以通过 `DATABASE_URL` 配置 PostgreSQL：

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
flask --app app init-db
flask --app app run
```

在 Vercel 中，可以在 Project Settings → Environment Variables 添加 `DATABASE_URL`。Neon、Supabase、Render Postgres 或标准 PostgreSQL 服务都可以使用。如果 Vercel 上没有设置 `DATABASE_URL`，应用会回退到临时 SQLite 演示数据库。

## 主要 API

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

## CSV 导入

初始化数据库后，可以导入更多 CSV 数据：

```bash
python scripts/import_figures.py data/figures.csv
python scripts/import_prices.py data/price_records.csv
python scripts/import_collection.py data/collection.csv
```

MVP 阶段使用手动整理的 CSV 数据，避免依赖不稳定的外部网站结构或高频爬虫。

## 后续优化

- 图片上传
- 价格提醒
- 发售日提醒
- 用户登录
- 使用 React 重构前端
- Docker 化
- 低频官方商品数据导入
