# 模型/手办商品比较与收藏价格管理系统

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md)

一个使用 Flask + SQLite/PostgreSQL 构建的 Web 应用，用于管理模型/手办商品信息、收藏状态、购买计划和价格记录。

线上演示：https://figure-dashboard-deploy.vercel.app

## 项目概述

Figure Collection & Price Dashboard 将模型/手办收藏场景做成一个小型数据管理与可视化系统。它支持商品搜索、收藏流程管理、价格历史记录，以及品牌分布、发售月份、价格区间、收藏金额和价格涨跌等仪表盘图表。

## 功能

- 仪表盘指标卡片与 ECharts 可视化
- 商品列表支持关键字、品牌、作品、厂商、发售月份、商品状态、价格、限定、可动筛选
- 商品增删改查，含新增/编辑弹窗表单
- 收藏弹窗表单，支持状态、购买价格、购买平台、购买日期、展示位置、开封状态和备注
- 商品详情页，展示商品信息、收藏信息、价格趋势和价格记录
- 价格记录支持涨跌标签：首次记录、上涨、下降、持平（涨跌由 SQL 窗口函数计算，分页和筛选后依然正确）
- 列表接口全部分页，避免一次性返回全表
- 支持从 CSV 导入商品、价格记录和收藏记录
- 本地使用 SQLite，生产环境可通过 `DATABASE_URL` 使用 PostgreSQL
- 前端支持中文、日文、英文切换（按需只加载当前语言词典）

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

### 数据库命令

| 命令 | 行为 |
|---|---|
| `flask --app app init-db` | 创建缺失的表，空库时导入示例数据。**不会删除已有数据**，可以重复执行。 |
| `flask --app app reset-db` | 删除所有表后重建并重新导入示例数据。**会清空全部数据。** |

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

在 Vercel 中，可以在 Project Settings → Environment Variables 添加 `DATABASE_URL`。Neon、Supabase、Render Postgres 或标准 PostgreSQL 服务都可以使用。

> **注意：** 如果 Vercel 上没有设置 `DATABASE_URL`，应用会回退到 `/tmp` 下的临时 SQLite 演示数据库。该数据库在每次冷启动时都会重置，写入的数据不会保留。要真正持久化，必须配置 `DATABASE_URL`。

## 写入权限

读接口始终公开。写接口（POST / PUT / DELETE）按以下规则控制：

| 环境 | `FIGURE_DASHBOARD_TOKEN` | 写入行为 |
|---|---|---|
| 本地开发 | 未设置 | 直接放行，零配置 |
| 部署环境（`VERCEL=1`） | 未设置 | 只读，写接口返回 403 |
| 任意环境 | 已设置 | 需要 `X-Auth-Token` 请求头，否则返回 401 |

设置方式：

```bash
export FIGURE_DASHBOARD_TOKEN="your-long-random-token"
```

在浏览器中，侧边栏底部会出现「写入权限」面板，点击「解锁」输入令牌即可，令牌保存在 `localStorage`。未解锁时新增/编辑/删除按钮会隐藏。

## 主要 API

```txt
GET    /api/config
GET    /api/dashboard
GET    /api/options
GET    /api/figures              # 分页
GET    /api/figures/<id>
POST   /api/figures
PUT    /api/figures/<id>
DELETE /api/figures/<id>
GET    /api/collection           # 分页
POST   /api/collection
PUT    /api/collection/<id>      # 部分更新，未传字段保持不变
DELETE /api/collection/<id>
GET    /api/prices               # 分页
GET    /api/prices/<figure_id>
POST   /api/prices
DELETE /api/prices/<id>
```

列表接口接受 `page` 与 `per_page`（默认 50，最大 200），返回结构为：

```json
{ "items": [], "total": 0, "page": 1, "per_page": 50, "pages": 1 }
```

`PUT /api/collection/<id>` 和 `PUT /api/figures/<id>` 只更新请求体中出现的字段，未出现的字段保持原值。

## 开发

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
```

CI 会在 SQLite 和真实 PostgreSQL 上分别跑同一套测试，避免只在某一种数据库上能跑的 SQL 混进主干。

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
- 多用户登录
- 使用 React 重构前端
- Docker 化
- 低频官方商品数据导入
