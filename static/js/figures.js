let figuresState = [];

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const options = await api("/api/options");
    setOptions(document.querySelector("#brand"), options.brands);
    setOptions(document.querySelector("#series_title"), options.series);
    document.querySelectorAll(".filters input, .filters select").forEach((el) => {
      el.addEventListener("input", loadFigures);
      el.addEventListener("change", loadFigures);
    });
    document.querySelector("#clearFilters").addEventListener("click", () => {
      document.querySelectorAll(".filters input, .filters select").forEach((el) => {
        el.value = "";
      });
      loadFigures();
    });
    document.querySelector("#figuresTable").addEventListener("click", onFigureAction);
    await loadFigures();
  } catch (error) {
    toast(error.message);
  }
});

async function loadFigures() {
  const params = new URLSearchParams();
  ["keyword", "brand", "series_title", "is_limited", "is_articulated"].forEach((id) => {
    const value = document.querySelector(`#${id}`).value;
    if (value) params.set(id, value);
  });
  const priceRange = document.querySelector("#priceRange").value;
  if (priceRange) {
    const [min, max] = priceRange.split("-");
    if (min) params.set("min_price", min);
    if (max) params.set("max_price", max);
  }
  figuresState = await api(`/api/figures?${params.toString()}`);
  renderFigures(figuresState);
}

function renderFigures(rows) {
  document.querySelector("#resultCount").textContent = t("common.items", { count: rows.length });
  const tbody = document.querySelector("#figuresTable");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty-state">${t("figures.empty")}</td></tr>`;
    return;
  }
  tbody.innerHTML = rows
    .map(
      (row) => `
      <tr>
        <td>
          <span class="item-title">
            <strong>${row.name}</strong>
            <small>${text(row.product_url)}</small>
          </span>
        </td>
        <td>${row.brand}</td>
        <td>${row.series_title}</td>
        <td>${row.manufacturer}</td>
        <td>${row.release_date}</td>
        <td>${yen(row.official_price)}</td>
        <td>
          <span class="badge-row">
            ${row.is_articulated ? badge(t("status.articulated"), "green") : badge(t("status.fixed"))}
            ${row.is_limited ? badge(t("status.limited"), "rose") : badge(t("status.regular"))}
            ${row.height_mm ? badge(`${row.height_mm}mm`, "gold") : ""}
          </span>
        </td>
        <td>${badge(row.status ? statusLabel(row.status) : "-", row.status === "予約中" ? "rose" : "")}</td>
        <td>
          <div class="row-actions">
            <button class="button small primary" data-action="collect" data-id="${row.id}" type="button">${t("figures.addCollection")}</button>
            <a class="button small secondary" href="${row.product_url || "#"}" target="_blank" rel="noreferrer">${t("figures.detail")}</a>
          </div>
        </td>
      </tr>
    `,
    )
    .join("");
}

async function onFigureAction(event) {
  const button = event.target.closest("button[data-action='collect']");
  if (!button) return;
  const figure = figuresState.find((item) => String(item.id) === button.dataset.id);
  await api("/api/collection", {
    method: "POST",
    body: JSON.stringify({
      figure_id: Number(button.dataset.id),
      ownership_status: "欲しい",
      memo: `${figure?.name || "Figure"} ${t("figures.memoAdded")}`,
    }),
  });
  toast(t("figures.saved"));
}
