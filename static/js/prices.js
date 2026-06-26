let priceFigures = [];

document.addEventListener("DOMContentLoaded", async () => {
  try {
    priceFigures = await api("/api/figures");
    const figureOptions = priceFigures.map((figure) => ({ id: figure.id, name: figure.name }));
    setOptions(document.querySelector("#figureSelect"), figureOptions, null);
    setOptions(document.querySelector("#priceFigureFilter"), figureOptions);
    document.querySelector("input[name='checked_date']").valueAsDate = new Date();
    document.querySelector("#priceForm").addEventListener("submit", savePrice);
    document.querySelector("#priceFigureFilter").addEventListener("change", loadPrices);
    document.querySelector("#pricesTable").addEventListener("click", onPriceAction);
    await loadPrices();
  } catch (error) {
    toast(error.message);
  }
});

async function savePrice(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());
  payload.figure_id = Number(payload.figure_id);
  payload.price = Number(payload.price);
  await api("/api/prices", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  event.currentTarget.reset();
  document.querySelector("input[name='checked_date']").valueAsDate = new Date();
  toast(t("prices.saved"));
  await loadPrices();
}

async function loadPrices() {
  const figureId = document.querySelector("#priceFigureFilter").value;
  const params = figureId ? `?figure_id=${figureId}` : "";
  const rows = await api(`/api/prices${params}`);
  renderPrices(rows);
}

function renderPrices(rows) {
  document.querySelector("#priceCount").textContent = t("common.records", { count: rows.length });
  const tbody = document.querySelector("#pricesTable");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">${t("prices.empty")}</td></tr>`;
    return;
  }
  const movements = priceMovements(rows);
  tbody.innerHTML = rows
    .map(
      (row) => `
      <tr>
        <td>
          <span class="item-title">
            <strong>${row.name}</strong>
            <small>${row.brand} / ${row.series_title}</small>
          </span>
        </td>
        <td>${row.shop_name}</td>
        <td>${yen(row.price)}</td>
        <td>${movementBadge(movements[row.id])}</td>
        <td>${badge(conditionLabel(row.condition), row.condition === "used" ? "gold" : "green")}</td>
        <td>${text(row.stock_status)}</td>
        <td>${row.checked_date}</td>
        <td>
          <button class="button small danger" data-action="delete" data-id="${row.id}" type="button">${t("button.delete")}</button>
        </td>
      </tr>
    `,
    )
    .join("");
}

async function onPriceAction(event) {
  const button = event.target.closest("button[data-action='delete']");
  if (!button) return;
  if (!window.confirm(t("common.confirmDelete"))) return;
  await api(`/api/prices/${button.dataset.id}`, { method: "DELETE" });
  toast(t("prices.deleted"));
  await loadPrices();
}
