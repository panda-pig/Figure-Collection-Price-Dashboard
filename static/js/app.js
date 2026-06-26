const yenFormatter = new Intl.NumberFormat("ja-JP", {
  style: "currency",
  currency: "JPY",
  maximumFractionDigits: 0,
});

const SUPPORTED_LANGS = ["zh", "ja", "en"];
const DEFAULT_LANG = "zh";

const I18N = {
  zh: {
    "brand.subtitle": "收藏与价格",
    "language.label": "语言",
    "nav.dashboard": "仪表盘",
    "nav.figures": "商品",
    "nav.collection": "收藏",
    "nav.prices": "价格",
    "common.all": "全部",
    "common.loading": "加载中",
    "common.reset": "重置",
    "common.cancel": "取消",
    "common.close": "关闭",
    "common.yes": "是",
    "common.no": "否",
    "common.confirmDelete": "确定要删除这条记录吗？",
    "common.search": "搜索",
    "common.brand": "品牌",
    "common.series": "作品",
    "common.price": "价格",
    "common.limited": "限定",
    "common.status": "状态",
    "common.items": "{count} 件商品",
    "common.records": "{count} 条记录",
    "dashboard.eyebrow": "模型/手办商品比较",
    "dashboard.title": "收藏仪表盘",
    "dashboard.nextRelease": "下一批发售窗口",
    "dashboard.noData": "暂无数据",
    "dashboard.nextReleaseValue": "{month} / {count} 件",
    "metric.totalFigures": "商品总数",
    "metric.totalFiguresNote": "商品主表记录",
    "metric.owned": "已收藏",
    "metric.ownedNote": "收藏状态 = 已拥有",
    "metric.wishlist": "想买数量",
    "metric.wishlistNote": "预算 {amount}",
    "metric.reserved": "预约中",
    "metric.reservedNote": "预约预算 {amount}",
    "metric.purchaseTotal": "收藏总金额",
    "metric.purchaseTotalNote": "已拥有购买价合计",
    "metric.monthlyRelease": "本月发售",
    "metric.monthlyReleaseNote": "发售日在当前月份",
    "metric.limited": "限定商品",
    "metric.limitedNote": "限定标记 = 是",
    "metric.tracked": "价格记录商品",
    "metric.trackedNote": "可查看价格趋势",
    "chart.brandDistribution": "品牌分布",
    "chart.brandDistributionDesc": "商品主表整体品牌占比",
    "chart.ownership": "收藏状态",
    "chart.ownershipDesc": "个人收藏状态分布",
    "chart.releaseCalendar": "发售日历",
    "chart.releaseCalendarDesc": "按发售月份统计",
    "chart.priceBands": "价格区间",
    "chart.priceBandsDesc": "官方价格区间",
    "chart.ownedAmount": "已拥有金额",
    "chart.ownedAmountDesc": "已拥有商品按品牌金额",
    "chart.priceTrend": "价格趋势",
    "chart.priceTrendDesc": "价格记录较多的商品",
    "figures.eyebrow": "商品主表",
    "figures.title": "商品",
    "figures.searchPlaceholder": "商品名 / 作品 / 品牌",
    "figures.priceUnder5000": "5000 日元以下",
    "figures.priceUnder10000": "10000 日元以下",
    "figures.priceOver10000": "10000 日元以上",
    "figures.releaseMonth": "发售月份",
    "figures.articulation": "可动性",
    "figures.productList": "商品列表",
    "figures.empty": "没有找到符合条件的商品",
    "figures.addCollection": "加入收藏",
    "figures.detail": "详情",
    "figures.saved": "已加入收藏：想买",
    "figures.memoAdded": "已加入想买清单",
    "collection.eyebrow": "收藏状态管理",
    "collection.title": "收藏",
    "collection.addToCollection": "加入收藏",
    "collection.saveCollection": "保存收藏",
    "collection.displayLocation": "展示位置",
    "collection.displayLocationPlaceholder": "展示柜 A / 书架 B",
    "collection.records": "收藏记录",
    "collection.empty": "暂无收藏记录",
    "collection.saved": "收藏记录已更新",
    "collection.deleted": "收藏记录已删除",
    "detail.eyebrow": "商品详情",
    "detail.backToList": "返回列表",
    "detail.productInfo": "商品信息",
    "detail.collectionInfo": "收藏信息",
    "detail.collectionInfoDesc": "当前收藏记录",
    "detail.priceTrendDesc": "该商品的价格历史",
    "detail.noCollection": "还没有收藏记录",
    "prices.eyebrow": "价格历史",
    "prices.title": "价格",
    "prices.addRecord": "新增价格记录",
    "prices.addRecordDesc": "不同平台、日期、状态都可以独立记录",
    "prices.shop": "店铺",
    "prices.shopPlaceholder": "amiami / 骏河屋 / Mercari",
    "prices.condition": "新品/中古",
    "prices.stock": "库存",
    "prices.stockPlaceholder": "预约中 / 有库存",
    "prices.date": "日期",
    "prices.savePrice": "保存价格",
    "prices.records": "价格记录",
    "prices.change": "涨跌",
    "prices.up": "上涨 {amount}",
    "prices.down": "下降 {amount}",
    "prices.flat": "持平",
    "prices.noPrevious": "首次记录",
    "prices.empty": "暂无价格记录",
    "prices.saved": "价格记录已保存",
    "prices.deleted": "价格记录已删除",
    "table.figureName": "商品名",
    "table.figure": "商品",
    "table.manufacturer": "厂商",
    "table.release": "发售",
    "table.attributes": "属性",
    "table.actions": "操作",
    "table.purchasePrice": "购买价格",
    "table.purchaseShop": "购买平台",
    "table.purchaseDate": "购买日期",
    "table.opened": "开封",
    "table.memo": "备注",
    "button.save": "保存",
    "button.delete": "删除",
    "aria.figureFilters": "商品筛选",
    "aria.collectionFilters": "收藏筛选",
    "aria.chooseTrendFigure": "选择价格趋势商品",
    "aria.filterPriceFigure": "按商品筛选价格记录",
    "status.articulated": "可动",
    "status.fixed": "固定",
    "status.limited": "限定",
    "status.regular": "一般",
    "status.wishlist": "想买",
    "status.reserved": "已预约",
    "status.owned": "已拥有",
    "status.sold": "已卖出",
    "status.skipped": "放弃购买",
    "status.tooExpensive": "太贵",
    "status.preorder": "预约中",
    "status.planned": "预计发售",
    "status.released": "已发售",
    "condition.new": "新品",
    "condition.used": "中古",
  },
  ja: {
    "brand.subtitle": "コレクション・価格管理",
    "language.label": "言語",
    "nav.dashboard": "ダッシュボード",
    "nav.figures": "商品",
    "nav.collection": "コレクション",
    "nav.prices": "価格",
    "common.all": "すべて",
    "common.loading": "読み込み中",
    "common.reset": "リセット",
    "common.cancel": "キャンセル",
    "common.close": "閉じる",
    "common.yes": "はい",
    "common.no": "いいえ",
    "common.confirmDelete": "この記録を削除しますか？",
    "common.search": "検索",
    "common.brand": "ブランド",
    "common.series": "作品",
    "common.price": "価格",
    "common.limited": "限定",
    "common.status": "状態",
    "common.items": "{count}件の商品",
    "common.records": "{count}件の記録",
    "dashboard.eyebrow": "フィギュア商品比較",
    "dashboard.title": "コレクションダッシュボード",
    "dashboard.nextRelease": "次の発売月",
    "dashboard.noData": "データなし",
    "dashboard.nextReleaseValue": "{month} / {count}件",
    "metric.totalFigures": "商品総数",
    "metric.totalFiguresNote": "商品マスターの件数",
    "metric.owned": "所持数",
    "metric.ownedNote": "所有状況 = 所持",
    "metric.wishlist": "欲しい数",
    "metric.wishlistNote": "予算 {amount}",
    "metric.reserved": "予約済み",
    "metric.reservedNote": "予約予算 {amount}",
    "metric.purchaseTotal": "購入総額",
    "metric.purchaseTotalNote": "所持商品の購入価格合計",
    "metric.monthlyRelease": "今月発売",
    "metric.monthlyReleaseNote": "発売日が今月の商品",
    "metric.limited": "限定商品",
    "metric.limitedNote": "限定フラグ = あり",
    "metric.tracked": "価格履歴商品",
    "metric.trackedNote": "価格推移を表示可能",
    "chart.brandDistribution": "ブランド分布",
    "chart.brandDistributionDesc": "商品マスター全体のブランド比率",
    "chart.ownership": "所有状況",
    "chart.ownershipDesc": "コレクション状態の分布",
    "chart.releaseCalendar": "発売カレンダー",
    "chart.releaseCalendarDesc": "発売月ごとの商品数",
    "chart.priceBands": "価格帯",
    "chart.priceBandsDesc": "公式価格の価格帯",
    "chart.ownedAmount": "所持金額",
    "chart.ownedAmountDesc": "ブランド別の購入金額",
    "chart.priceTrend": "価格推移",
    "chart.priceTrendDesc": "価格履歴が多い商品",
    "figures.eyebrow": "商品マスター",
    "figures.title": "商品",
    "figures.searchPlaceholder": "商品名 / 作品 / ブランド",
    "figures.priceUnder5000": "5000円以下",
    "figures.priceUnder10000": "10000円以下",
    "figures.priceOver10000": "10000円以上",
    "figures.releaseMonth": "発売月",
    "figures.articulation": "可動",
    "figures.productList": "商品一覧",
    "figures.empty": "条件に一致する商品がありません",
    "figures.addCollection": "コレクション追加",
    "figures.detail": "詳細",
    "figures.saved": "コレクションに追加しました：欲しい",
    "figures.memoAdded": "欲しいリストに追加",
    "collection.eyebrow": "所有状況管理",
    "collection.title": "コレクション",
    "collection.addToCollection": "コレクション追加",
    "collection.saveCollection": "保存する",
    "collection.displayLocation": "展示場所",
    "collection.displayLocationPlaceholder": "ガラスケース A / 本棚 B",
    "collection.records": "コレクション記録",
    "collection.empty": "コレクション記録がありません",
    "collection.saved": "コレクション記録を更新しました",
    "collection.deleted": "コレクション記録を削除しました",
    "detail.eyebrow": "商品詳細",
    "detail.backToList": "一覧へ戻る",
    "detail.productInfo": "商品情報",
    "detail.collectionInfo": "コレクション情報",
    "detail.collectionInfoDesc": "現在の所有記録",
    "detail.priceTrendDesc": "この商品の価格履歴",
    "detail.noCollection": "コレクション記録がありません",
    "prices.eyebrow": "価格履歴",
    "prices.title": "価格",
    "prices.addRecord": "価格記録を追加",
    "prices.addRecordDesc": "店舗・日付・状態ごとに価格を記録できます",
    "prices.shop": "店舗",
    "prices.shopPlaceholder": "あみあみ / 駿河屋 / メルカリ",
    "prices.condition": "新品/中古",
    "prices.stock": "在庫",
    "prices.stockPlaceholder": "予約中 / 在庫あり",
    "prices.date": "日付",
    "prices.savePrice": "価格を保存",
    "prices.records": "価格記録",
    "prices.change": "変動",
    "prices.up": "{amount} 上昇",
    "prices.down": "{amount} 下落",
    "prices.flat": "変化なし",
    "prices.noPrevious": "初回記録",
    "prices.empty": "価格記録がありません",
    "prices.saved": "価格記録を保存しました",
    "prices.deleted": "価格記録を削除しました",
    "table.figureName": "商品名",
    "table.figure": "商品",
    "table.manufacturer": "メーカー",
    "table.release": "発売",
    "table.attributes": "属性",
    "table.actions": "操作",
    "table.purchasePrice": "購入価格",
    "table.purchaseShop": "購入店舗",
    "table.purchaseDate": "購入日",
    "table.opened": "開封",
    "table.memo": "メモ",
    "button.save": "保存",
    "button.delete": "削除",
    "aria.figureFilters": "商品フィルター",
    "aria.collectionFilters": "コレクションフィルター",
    "aria.chooseTrendFigure": "価格推移の商品を選択",
    "aria.filterPriceFigure": "商品で価格記録を絞り込む",
    "status.articulated": "可動",
    "status.fixed": "固定",
    "status.limited": "限定",
    "status.regular": "一般",
    "status.wishlist": "欲しい",
    "status.reserved": "予約済み",
    "status.owned": "所持",
    "status.sold": "売却済み",
    "status.skipped": "見送り",
    "status.tooExpensive": "高すぎる",
    "status.preorder": "予約中",
    "status.planned": "発売予定",
    "status.released": "発売済み",
    "condition.new": "新品",
    "condition.used": "中古",
  },
  en: {
    "brand.subtitle": "Collection & Price",
    "language.label": "Language",
    "nav.dashboard": "Dashboard",
    "nav.figures": "Figures",
    "nav.collection": "Collection",
    "nav.prices": "Prices",
    "common.all": "All",
    "common.loading": "Loading",
    "common.reset": "Reset",
    "common.cancel": "Cancel",
    "common.close": "Close",
    "common.yes": "Yes",
    "common.no": "No",
    "common.confirmDelete": "Delete this record?",
    "common.search": "Search",
    "common.brand": "Brand",
    "common.series": "Series",
    "common.price": "Price",
    "common.limited": "Limited",
    "common.status": "Status",
    "common.items": "{count} items",
    "common.records": "{count} records",
    "dashboard.eyebrow": "Figure product comparison",
    "dashboard.title": "Collection Dashboard",
    "dashboard.nextRelease": "Next release window",
    "dashboard.noData": "No data",
    "dashboard.nextReleaseValue": "{month} / {count} items",
    "metric.totalFigures": "Total figures",
    "metric.totalFiguresNote": "Product master records",
    "metric.owned": "Owned",
    "metric.ownedNote": "Ownership status = owned",
    "metric.wishlist": "Wishlist",
    "metric.wishlistNote": "Budget {amount}",
    "metric.reserved": "Reserved",
    "metric.reservedNote": "Reserved budget {amount}",
    "metric.purchaseTotal": "Collection amount",
    "metric.purchaseTotalNote": "Owned purchase price total",
    "metric.monthlyRelease": "This month",
    "metric.monthlyReleaseNote": "Release date in current month",
    "metric.limited": "Limited items",
    "metric.limitedNote": "Limited flag = yes",
    "metric.tracked": "Tracked figure",
    "metric.trackedNote": "Price trend available",
    "chart.brandDistribution": "Brand Distribution",
    "chart.brandDistributionDesc": "Brand mix across product master",
    "chart.ownership": "Ownership",
    "chart.ownershipDesc": "Collection status distribution",
    "chart.releaseCalendar": "Release Calendar",
    "chart.releaseCalendarDesc": "Items by release month",
    "chart.priceBands": "Price Bands",
    "chart.priceBandsDesc": "Official price bands",
    "chart.ownedAmount": "Owned Amount",
    "chart.ownedAmountDesc": "Purchase amount by brand",
    "chart.priceTrend": "Price Trend",
    "chart.priceTrendDesc": "Figure with rich price records",
    "figures.eyebrow": "Product master",
    "figures.title": "Figures",
    "figures.searchPlaceholder": "Name / series / brand",
    "figures.priceUnder5000": "Under ¥5,000",
    "figures.priceUnder10000": "Under ¥10,000",
    "figures.priceOver10000": "¥10,000 and up",
    "figures.releaseMonth": "Release month",
    "figures.articulation": "Articulation",
    "figures.productList": "Product List",
    "figures.empty": "No figures found",
    "figures.addCollection": "Add",
    "figures.detail": "Details",
    "figures.saved": "Added to collection: wishlist",
    "figures.memoAdded": "Added to wishlist",
    "collection.eyebrow": "Ownership management",
    "collection.title": "Collection",
    "collection.addToCollection": "Add to Collection",
    "collection.saveCollection": "Save Collection",
    "collection.displayLocation": "Display location",
    "collection.displayLocationPlaceholder": "Display case A / Shelf B",
    "collection.records": "Collection Records",
    "collection.empty": "No collection records",
    "collection.saved": "Collection record updated",
    "collection.deleted": "Collection record deleted",
    "detail.eyebrow": "Figure detail",
    "detail.backToList": "Back to list",
    "detail.productInfo": "Product Info",
    "detail.collectionInfo": "Collection Info",
    "detail.collectionInfoDesc": "Current ownership record",
    "detail.priceTrendDesc": "Price history for this figure",
    "detail.noCollection": "No collection record yet",
    "prices.eyebrow": "Price history",
    "prices.title": "Prices",
    "prices.addRecord": "Add Price Record",
    "prices.addRecordDesc": "Record prices by shop, date, and condition",
    "prices.shop": "Shop",
    "prices.shopPlaceholder": "AmiAmi / Surugaya / Mercari",
    "prices.condition": "Condition",
    "prices.stock": "Stock",
    "prices.stockPlaceholder": "Preorder / In stock",
    "prices.date": "Date",
    "prices.savePrice": "Save Price",
    "prices.records": "Price Records",
    "prices.change": "Change",
    "prices.up": "Up {amount}",
    "prices.down": "Down {amount}",
    "prices.flat": "No change",
    "prices.noPrevious": "First record",
    "prices.empty": "No price records",
    "prices.saved": "Price record saved",
    "prices.deleted": "Price record deleted",
    "table.figureName": "Figure name",
    "table.figure": "Figure",
    "table.manufacturer": "Manufacturer",
    "table.release": "Release",
    "table.attributes": "Attributes",
    "table.actions": "Actions",
    "table.purchasePrice": "Purchase price",
    "table.purchaseShop": "Purchase shop",
    "table.purchaseDate": "Purchase date",
    "table.opened": "Opened",
    "table.memo": "Memo",
    "button.save": "Save",
    "button.delete": "Delete",
    "aria.figureFilters": "Figure filters",
    "aria.collectionFilters": "Collection filters",
    "aria.chooseTrendFigure": "Choose figure for trend",
    "aria.filterPriceFigure": "Filter price records by figure",
    "status.articulated": "Articulated",
    "status.fixed": "Fixed",
    "status.limited": "Limited",
    "status.regular": "Regular",
    "status.wishlist": "Wishlist",
    "status.reserved": "Reserved",
    "status.owned": "Owned",
    "status.sold": "Sold",
    "status.skipped": "Skipped",
    "status.tooExpensive": "Too expensive",
    "status.preorder": "Preorder",
    "status.planned": "Planned",
    "status.released": "Released",
    "condition.new": "New",
    "condition.used": "Used",
  },
};

const STATUS_TRANSLATION_KEYS = {
  欲しい: "status.wishlist",
  予約済み: "status.reserved",
  所持: "status.owned",
  売却済み: "status.sold",
  見送り: "status.skipped",
  高すぎる: "status.tooExpensive",
  予約中: "status.preorder",
  発売予定: "status.planned",
  発売済み: "status.released",
};

const CONDITION_TRANSLATION_KEYS = {
  new: "condition.new",
  used: "condition.used",
};

function currentLang() {
  const stored = localStorage.getItem("figureDashboardLang");
  return SUPPORTED_LANGS.includes(stored) ? stored : DEFAULT_LANG;
}

function t(key, params = {}) {
  const lang = currentLang();
  const template = I18N[lang]?.[key] || I18N[DEFAULT_LANG][key] || key;
  return Object.entries(params).reduce((value, [name, replacement]) => {
    return value.replaceAll(`{${name}}`, replacement);
  }, template);
}

function statusLabel(value) {
  return t(STATUS_TRANSLATION_KEYS[value] || value);
}

function conditionLabel(value) {
  return t(CONDITION_TRANSLATION_KEYS[value] || value || "-");
}

function applyI18n(root = document) {
  const lang = currentLang();
  document.documentElement.lang = lang === "zh" ? "zh-CN" : lang;
  root.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.setAttribute("placeholder", t(el.dataset.i18nPlaceholder));
  });
  root.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
    el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel));
  });
  root.querySelectorAll(".language-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === lang);
    button.setAttribute("aria-pressed", String(button.dataset.lang === lang));
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".language-button").forEach((button) => {
    button.addEventListener("click", () => {
      localStorage.setItem("figureDashboardLang", button.dataset.lang);
      window.location.reload();
    });
  });
  applyI18n();
});

function yen(value) {
  return yenFormatter.format(Number(value || 0));
}

function text(value, fallback = "-") {
  return value === null || value === undefined || value === "" ? fallback : value;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

function setOptions(select, values, placeholder = t("common.all")) {
  select.innerHTML = "";
  if (placeholder !== null) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.appendChild(option);
  }
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value.id ?? value;
    option.textContent = value.label ?? value.name ?? value;
    select.appendChild(option);
  });
}

function toast(message) {
  const el = document.querySelector("#toast");
  if (!el) return;
  el.textContent = message;
  el.classList.add("visible");
  window.clearTimeout(window.__toastTimer);
  window.__toastTimer = window.setTimeout(() => el.classList.remove("visible"), 2200);
}

function badge(label, variant = "") {
  return `<span class="badge ${variant}">${label}</span>`;
}

function priceMovements(rows) {
  const movements = {};
  const previousByShop = {};
  [...rows]
    .sort((a, b) => {
      const groupA = `${a.figure_id}-${a.shop_name}`;
      const groupB = `${b.figure_id}-${b.shop_name}`;
      return groupA.localeCompare(groupB) || a.checked_date.localeCompare(b.checked_date) || a.id - b.id;
    })
    .forEach((row) => {
      const key = `${row.figure_id}-${row.shop_name}`;
      const previous = previousByShop[key];
      previousByShop[key] = row;
      if (!previous) {
        movements[row.id] = { type: "none", diff: 0 };
        return;
      }
      const diff = Number(row.price) - Number(previous.price);
      movements[row.id] = {
        type: diff > 0 ? "up" : diff < 0 ? "down" : "flat",
        diff,
      };
    });
  return movements;
}

function movementBadge(movement) {
  if (!movement || movement.type === "none") return badge(t("prices.noPrevious"));
  if (movement.type === "flat") return badge(t("prices.flat"));
  if (movement.type === "up") return badge(t("prices.up", { amount: yen(Math.abs(movement.diff)) }), "rose");
  return badge(t("prices.down", { amount: yen(Math.abs(movement.diff)) }), "green");
}

function bindResize(charts) {
  window.addEventListener("resize", () => {
    charts.forEach((chart) => chart && chart.resize());
  });
}
