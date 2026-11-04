document.addEventListener("DOMContentLoaded", async () => {
  await I18N_READY;
  try {
    await loadApiConfig();
    const figureId = window.FIGURE_ID;
    const [figure, collection, priceRows] = await Promise.all([
      api(`/api/figures/${figureId}`),
      api(`/api/collection?figure_id=${figureId}`),
      api(`/api/prices/${figureId}`),
    ]);
    renderFigureDetail(figure, collection.items[0], priceRows);
  } catch (error) {
    toast(error.message);
  }
});

function renderFigureDetail(figure, collection, prices) {
  document.querySelector("#detailTitle").textContent = figure.name;
  document.querySelector("#detailSubtitle").textContent =
    [figure.brand, figure.series_title].filter(Boolean).join(" / ") || "-";

  document.querySelector("#figureFacts").innerHTML = factsHtml([
    [t("common.brand"), figure.brand],
    [t("common.series"), figure.series_title],
    [t("table.manufacturer"), figure.manufacturer],
    [t("table.release"), figure.release_date],
    [t("common.price"), yen(figure.official_price)],
    [t("table.scale"), figure.scale],
    [t("table.height"), figure.height_mm ? `${figure.height_mm}mm` : null],
    [
      t("table.attributes"),
      `${figure.is_articulated ? t("status.articulated") : t("status.fixed")} / ${figure.is_limited ? t("status.limited") : t("status.regular")}`,
    ],
    [t("common.status"), statusLabel(figure.status)],
  ]);

  document.querySelector("#collectionFacts").innerHTML = collection
    ? factsHtml([
        [t("common.status"), statusLabel(collection.ownership_status)],
        [t("table.purchasePrice"), yen(collection.purchase_price)],
        [t("table.purchaseShop"), collection.purchase_shop],
        [t("table.purchaseDate"), collection.purchase_date],
        [t("collection.displayLocation"), collection.display_location],
        [t("table.opened"), collection.is_opened ? t("common.yes") : t("common.no")],
        [t("table.memo"), collection.memo],
      ])
    : `<div class="empty-state">${esc(t("detail.noCollection"))}</div>`;

  renderDetailPrices(prices);
  renderDetailTrend(prices);
}

function factsHtml(rows) {
  return rows
    .map(
      ([label, value]) => `
      <div>
        <dt>${esc(label)}</dt>
        <dd>${cell(value)}</dd>
      </div>
    `,
    )
    .join("");
}

function renderDetailPrices(rows) {
  document.querySelector("#detailPriceCount").textContent = t("common.records", { count: rows.length });
  const sorted = [...rows].sort((a, b) => b.checked_date.localeCompare(a.checked_date) || b.id - a.id);
  const tbody = document.querySelector("#detailPricesTable");
  if (!sorted.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${esc(t("prices.empty"))}</td></tr>`;
    return;
  }
  tbody.innerHTML = sorted
    .map(
      (row) => `
        <tr>
          <td>${esc(row.shop_name)}</td>
          <td>${esc(yen(row.price))}</td>
          <td>${movementBadge(row)}</td>
          <td>${badge(conditionLabel(row.condition), row.condition === "used" ? "gold" : "green")}</td>
          <td>${cell(row.stock_status)}</td>
          <td>${cell(row.checked_date)}</td>
        </tr>
      `,
    )
    .join("");
}

function renderDetailTrend(rows) {
  const chart = echarts.init(document.getElementById("detailTrendChart"));
  chart.setOption(trendOption(rows));
  bindResize([chart]);
}
