let pricesPager;
let currentPage = 1;
const loadLatestPrices = createLatestLoader();

function resetCheckedDate(date = new Date()) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  document.querySelector("input[name='checked_date']").value = `${date.getFullYear()}-${month}-${day}`;
}

document.addEventListener("DOMContentLoaded", async () => {
  await I18N_READY;
  try {
    await loadApiConfig();
    // /api/options carries id+name pairs, so the dropdowns no longer pull the
    // entire figures table.
    const options = await api("/api/options");
    setOptions(document.querySelector("#figureSelect"), options.figures, null);
    setOptions(document.querySelector("#priceFigureFilter"), options.figures);
    resetCheckedDate();

    pricesPager = createPager("pricesPager", (page) => loadPrices(page));

    document.querySelector("#priceForm").addEventListener("submit", savePrice);
    document.querySelector("#priceFigureFilter").addEventListener("change", () => loadPrices(1));
    document.querySelector("#pricesTable").addEventListener("click", onPriceAction);
    await loadPrices(1);
  } catch (error) {
    toast(error.message);
  }
});

async function savePrice(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  payload.figure_id = Number(payload.figure_id);
  payload.price = Number(payload.price);
  try {
    await api("/api/prices", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    resetCheckedDate();
    toast(t("prices.saved"));
    await loadPrices(1);
  } catch (error) {
    toast(error.message);
  }
}

async function loadPrices(page = currentPage) {
  const params = new URLSearchParams();
  const figureId = document.querySelector("#priceFigureFilter").value;
  if (figureId) params.set("figure_id", figureId);
  params.set("page", page);

  await loadLatestPrices(`/api/prices?${params.toString()}`, (result) => {
    currentPage = result.page;
    renderPrices(result);
    pricesPager.update(result);
  });
}

function renderPrices(result) {
  document.querySelector("#priceCount").textContent = t("common.records", { count: result.total });
  const tbody = document.querySelector("#pricesTable");
  if (!result.items.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">${esc(t("prices.empty"))}</td></tr>`;
    return;
  }
  tbody.innerHTML = result.items
    .map(
      (row) => `
      <tr>
        <td>
          <span class="item-title">
            <strong>${esc(row.name)}</strong>
            <small>${esc([row.brand, row.series_title].filter(Boolean).join(" / "))}</small>
          </span>
        </td>
        <td>${esc(row.shop_name)}</td>
        <td>${esc(yen(row.price))}</td>
        <td>${movementBadge(row)}</td>
        <td>${badge(conditionLabel(row.condition), row.condition === "used" ? "gold" : "green")}</td>
        <td>${cell(row.stock_status)}</td>
        <td>${cell(row.checked_date)}</td>
        <td>
          <button class="button small danger write-only" data-action="delete" data-id="${esc(row.id)}" type="button">${esc(t("button.delete"))}</button>
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
  try {
    await api(`/api/prices/${button.dataset.id}`, { method: "DELETE" });
    toast(t("prices.deleted"));
    await loadPrices();
  } catch (error) {
    toast(error.message);
  }
}
