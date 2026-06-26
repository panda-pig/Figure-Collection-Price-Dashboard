document.addEventListener("DOMContentLoaded", async () => {
  try {
    const figureId = window.FIGURE_ID;
    const [figure, collectionRows, priceRows] = await Promise.all([
      api(`/api/figures/${figureId}`),
      api(`/api/collection?figure_id=${figureId}`),
      api(`/api/prices/${figureId}`),
    ]);
    renderFigureDetail(figure, collectionRows[0], priceRows);
  } catch (error) {
    toast(error.message);
  }
});

function renderFigureDetail(figure, collection, prices) {
  document.querySelector("#detailTitle").textContent = figure.name;
  document.querySelector("#detailSubtitle").textContent = `${figure.brand} / ${figure.series_title}`;
  document.querySelector("#figureFacts").innerHTML = factsHtml([
    [t("common.brand"), figure.brand],
    [t("common.series"), figure.series_title],
    [t("table.manufacturer"), figure.manufacturer],
    [t("table.release"), figure.release_date],
    [t("common.price"), yen(figure.official_price)],
    [t("table.attributes"), `${figure.is_articulated ? t("status.articulated") : t("status.fixed")} / ${figure.is_limited ? t("status.limited") : t("status.regular")}`],
    [t("common.status"), statusLabel(figure.status)],
  ]);
  document.querySelector("#collectionFacts").innerHTML = collection
    ? factsHtml([
        [t("common.status"), statusLabel(collection.ownership_status)],
        [t("table.purchasePrice"), collection.purchase_price ? yen(collection.purchase_price) : "-"],
        [t("table.purchaseShop"), text(collection.purchase_shop)],
        [t("table.purchaseDate"), text(collection.purchase_date)],
        [t("collection.displayLocation"), text(collection.display_location)],
        [t("table.opened"), collection.is_opened ? t("common.yes") : t("common.no")],
        [t("table.memo"), text(collection.memo)],
      ])
    : `<div class="empty-state">${t("detail.noCollection")}</div>`;
  renderDetailPrices(prices);
  renderDetailTrend(prices);
}

function factsHtml(rows) {
  return rows
    .map(
      ([label, value]) => `
      <div>
        <dt>${label}</dt>
        <dd>${text(value)}</dd>
      </div>
    `,
    )
    .join("");
}

function renderDetailPrices(rows) {
  const movements = priceMovements(rows);
  document.querySelector("#detailPriceCount").textContent = t("common.records", { count: rows.length });
  const sorted = [...rows].sort((a, b) => b.checked_date.localeCompare(a.checked_date) || b.id - a.id);
  const tbody = document.querySelector("#detailPricesTable");
  if (!sorted.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${t("prices.empty")}</td></tr>`;
    return;
  }
  tbody.innerHTML = sorted
    .map((row) => {
      const movement = movements[row.id];
      return `
        <tr>
          <td>${row.shop_name}</td>
          <td>${yen(row.price)}</td>
          <td>${movementBadge(movement)}</td>
          <td>${badge(conditionLabel(row.condition), row.condition === "used" ? "gold" : "green")}</td>
          <td>${text(row.stock_status)}</td>
          <td>${row.checked_date}</td>
        </tr>
      `;
    })
    .join("");
}

function renderDetailTrend(rows) {
  const chart = echarts.init(document.getElementById("detailTrendChart"));
  const shops = [...new Set(rows.map((row) => row.shop_name))];
  const dates = [...new Set(rows.map((row) => row.checked_date))].sort();
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
  window.addEventListener("resize", () => chart.resize());
}
