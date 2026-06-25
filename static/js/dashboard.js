const dashboardCharts = [];

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const [dashboard, figures] = await Promise.all([api("/api/dashboard"), api("/api/figures")]);
    renderMetrics(dashboard);
    renderDashboardCharts(dashboard);
    setupTrendSelect(figures, dashboard.default_trend_figure);
    bindResize(dashboardCharts);
  } catch (error) {
    toast(error.message);
  }
});

function renderMetrics(data) {
  const metrics = [
    ["商品总数", data.total_figures, "商品主表记录", "#285a7f"],
    ["已收藏", data.owned_count, "ownership_status = 所持", "#297c63"],
    ["想买数量", data.wishlist_count, `预算 ${yen(data.wishlist_budget)}`, "#d85b7f"],
    ["预约中", data.reserved_count, `预约预算 ${yen(data.reserved_budget)}`, "#b78a2e"],
    ["收藏总金额", yen(data.total_purchase_amount), "已拥有购买价合计", "#111820"],
    ["本月发售", data.monthly_release_count, "release_date 为当前月份", "#285a7f"],
    ["限定商品", data.limited_count, "is_limited = 1", "#7f2d38"],
    ["价格记录商品", data.default_trend_figure?.name || "-", "可查看价格趋势", "#297c63"],
  ];
  document.querySelector("#metricGrid").innerHTML = metrics
    .map(
      ([label, value, note, accent]) => `
        <article class="metric-card" style="--accent:${accent}">
          <span>${label}</span>
          <strong>${value}</strong>
          <small>${note}</small>
        </article>
      `,
    )
    .join("");

  const next = data.monthly_releases?.[0];
  document.querySelector("#nextReleaseLabel").textContent = next ? `${next.month} / ${next.count} items` : "No data";
}

function renderDashboardCharts(data) {
  pieChart("brandChart", data.brand_distribution, "brand", "count");
  pieChart("ownershipChart", data.ownership_distribution, "status", "count");
  barChart("releaseChart", data.monthly_releases, "month", "count", "#285a7f");
  barChart("priceBucketChart", data.price_buckets, "bucket", "count", "#d85b7f");
  barChart("purchaseChart", data.purchase_by_brand, "brand", "amount", "#297c63", yen);
}

function pieChart(id, rows, nameKey, valueKey) {
  const chart = echarts.init(document.getElementById(id));
  dashboardCharts.push(chart);
  chart.setOption({
    color: ["#285a7f", "#d85b7f", "#b78a2e", "#297c63", "#111820", "#8c97a6"],
    tooltip: { trigger: "item" },
    legend: { bottom: 0, type: "scroll" },
    series: [
      {
        type: "pie",
        radius: ["42%", "70%"],
        center: ["50%", "44%"],
        label: { formatter: "{b}\n{c}" },
        data: rows.map((row) => ({ name: row[nameKey], value: row[valueKey] })),
      },
    ],
  });
}

function barChart(id, rows, labelKey, valueKey, color, formatter = (value) => value) {
  const chart = echarts.init(document.getElementById(id));
  dashboardCharts.push(chart);
  chart.setOption({
    color: [color],
    grid: { left: 48, right: 20, top: 26, bottom: 56 },
    tooltip: {
      trigger: "axis",
      valueFormatter: formatter,
    },
    xAxis: {
      type: "category",
      data: rows.map((row) => row[labelKey]),
      axisLabel: { interval: 0, rotate: rows.length > 5 ? 24 : 0 },
    },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: rows.map((row) => row[valueKey]), barMaxWidth: 38 }],
  });
}

function setupTrendSelect(figures, defaultFigure) {
  const select = document.querySelector("#trendFigureSelect");
  setOptions(
    select,
    figures.map((figure) => ({ id: figure.id, name: figure.name })),
    null,
  );
  if (defaultFigure) select.value = defaultFigure.id;
  select.addEventListener("change", () => renderTrend(select.value));
  renderTrend(select.value);
}

async function renderTrend(figureId) {
  if (!figureId) return;
  const rows = await api(`/api/prices/${figureId}`);
  const chartEl = document.getElementById("trendChart");
  let chart = echarts.getInstanceByDom(chartEl);
  if (!chart) {
    chart = echarts.init(chartEl);
    dashboardCharts.push(chart);
  }
  const shops = [...new Set(rows.map((row) => row.shop_name))];
  const dates = [...new Set(rows.map((row) => row.checked_date))].sort();
  document.querySelector("#trendSubtitle").textContent = rows[0]?.name || "価格履歴";
  chart.setOption({
    color: ["#285a7f", "#d85b7f", "#b78a2e", "#297c63", "#111820"],
    tooltip: { trigger: "axis", valueFormatter: yen },
    legend: { top: 0, type: "scroll" },
    grid: { left: 64, right: 24, top: 46, bottom: 42 },
    xAxis: { type: "category", data: dates },
    yAxis: { type: "value", axisLabel: { formatter: (value) => `${Math.round(value / 1000)}k` } },
    series: shops.map((shop) => ({
      name: shop,
      type: "line",
      smooth: true,
      symbolSize: 8,
      data: dates.map((date) => rows.find((row) => row.shop_name === shop && row.checked_date === date)?.price ?? null),
    })),
  });
}
