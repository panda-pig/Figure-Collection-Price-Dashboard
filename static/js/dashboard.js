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
    [t("metric.totalFigures"), data.total_figures, t("metric.totalFiguresNote"), "#285a7f"],
    [t("metric.owned"), data.owned_count, t("metric.ownedNote"), "#297c63"],
    [t("metric.wishlist"), data.wishlist_count, t("metric.wishlistNote", { amount: yen(data.wishlist_budget) }), "#d85b7f"],
    [t("metric.reserved"), data.reserved_count, t("metric.reservedNote", { amount: yen(data.reserved_budget) }), "#b78a2e"],
    [t("metric.purchaseTotal"), yen(data.total_purchase_amount), t("metric.purchaseTotalNote"), "#111820"],
    [t("metric.monthlyRelease"), data.monthly_release_count, t("metric.monthlyReleaseNote"), "#285a7f"],
    [t("metric.limited"), data.limited_count, t("metric.limitedNote"), "#7f2d38"],
    [t("metric.tracked"), data.default_trend_figure?.name || "-", t("metric.trackedNote"), "#297c63"],
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
  document.querySelector("#nextReleaseLabel").textContent = next
    ? t("dashboard.nextReleaseValue", { month: next.month, count: next.count })
    : t("dashboard.noData");
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
  const translatedRows = rows.map((row) => ({
    ...row,
    translatedName: nameKey === "status" ? statusLabel(row[nameKey]) : row[nameKey],
  }));
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
        data: translatedRows.map((row) => ({ name: row.translatedName, value: row[valueKey] })),
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
  document.querySelector("#trendSubtitle").textContent = rows[0]?.name || t("chart.priceTrendDesc");
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
