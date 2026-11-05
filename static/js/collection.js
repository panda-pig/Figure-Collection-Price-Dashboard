let collectionOptions = {};
let collectionPager;
let currentPage = 1;
const loadLatestCollection = createLatestLoader();

document.addEventListener("DOMContentLoaded", async () => {
  await I18N_READY;
  try {
    await loadApiConfig();
    collectionOptions = await api("/api/options");
    setOptions(
      document.querySelector("#ownershipFilter"),
      collectionOptions.ownership_statuses.map((status) => ({ id: status, label: statusLabel(status) })),
    );
    setOptions(document.querySelector("#brandFilter"), collectionOptions.brands);

    collectionPager = createPager("collectionPager", (page) => loadCollection(page));

    document.querySelector("#ownershipFilter").addEventListener("change", () => loadCollection(1));
    document.querySelector("#brandFilter").addEventListener("change", () => loadCollection(1));
    document.querySelector("#clearCollectionFilters").addEventListener("click", () => {
      document.querySelector("#ownershipFilter").value = "";
      document.querySelector("#brandFilter").value = "";
      loadCollection(1);
    });
    document.querySelector("#collectionTable").addEventListener("click", onCollectionAction);
    await loadCollection(1);
  } catch (error) {
    toast(error.message);
  }
});

async function loadCollection(page = currentPage) {
  const params = new URLSearchParams();
  const status = document.querySelector("#ownershipFilter").value;
  const brand = document.querySelector("#brandFilter").value;
  if (status) params.set("ownership_status", status);
  if (brand) params.set("brand", brand);
  params.set("page", page);

  await loadLatestCollection(`/api/collection?${params.toString()}`, (result) => {
    currentPage = result.page;
    renderCollection(result);
    collectionPager.update(result);
  });
}

function renderCollection(result) {
  document.querySelector("#collectionCount").textContent = t("common.records", { count: result.total });
  const tbody = document.querySelector("#collectionTable");
  if (!result.items.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty-state">${esc(t("collection.empty"))}</td></tr>`;
    return;
  }
  tbody.innerHTML = result.items
    .map(
      (row) => `
      <tr data-id="${esc(row.id)}">
        <td>
          <span class="item-title">
            <strong>${esc(row.name)}</strong>
            <small>${esc([row.brand, row.series_title].filter(Boolean).join(" / "))}</small>
          </span>
        </td>
        <td>
          <select class="inline-input" data-field="ownership_status">
            ${collectionOptions.ownership_statuses
              .map(
                (status) =>
                  `<option value="${esc(status)}" ${row.ownership_status === status ? "selected" : ""}>${esc(statusLabel(status))}</option>`,
              )
              .join("")}
          </select>
        </td>
        <td><input class="inline-input" data-field="purchase_price" type="number" min="0" value="${cell(row.purchase_price, "")}"></td>
        <td><input class="inline-input" data-field="purchase_shop" value="${cell(row.purchase_shop, "")}"></td>
        <td><input class="inline-input" data-field="purchase_date" type="date" value="${cell(row.purchase_date, "")}"></td>
        <td><input data-field="is_opened" type="checkbox" ${row.is_opened ? "checked" : ""}></td>
        <td><input class="inline-input" data-field="display_location" value="${cell(row.display_location, "")}"></td>
        <td><input class="inline-input memo-input" data-field="memo" value="${cell(row.memo, "")}"></td>
        <td>
          <div class="row-actions">
            <button class="button small primary write-only" data-action="save" type="button">${esc(t("button.save"))}</button>
            <button class="button small danger write-only" data-action="delete" type="button">${esc(t("button.delete"))}</button>
          </div>
        </td>
      </tr>
    `,
    )
    .join("");
  syncWriteFields();
}

async function onCollectionAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const tr = button.closest("tr");
  const id = tr.dataset.id;

  try {
    if (button.dataset.action === "delete") {
      if (!window.confirm(t("common.confirmDelete"))) return;
      await api(`/api/collection/${id}`, { method: "DELETE" });
      toast(t("collection.deleted"));
      await loadCollection();
      return;
    }
    const payload = {};
    tr.querySelectorAll("[data-field]").forEach((input) => {
      payload[input.dataset.field] = input.type === "checkbox" ? input.checked : input.value;
    });
    await api(`/api/collection/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    toast(t("collection.saved"));
    await loadCollection();
  } catch (error) {
    toast(error.message);
  }
}
