let collectionRows = [];
let collectionOptions = {};

document.addEventListener("DOMContentLoaded", async () => {
  try {
    collectionOptions = await api("/api/options");
    setOptions(document.querySelector("#ownershipFilter"), collectionOptions.ownership_statuses);
    setOptions(document.querySelector("#brandFilter"), collectionOptions.brands);
    document.querySelector("#ownershipFilter").addEventListener("change", loadCollection);
    document.querySelector("#brandFilter").addEventListener("change", loadCollection);
    document.querySelector("#clearCollectionFilters").addEventListener("click", () => {
      document.querySelector("#ownershipFilter").value = "";
      document.querySelector("#brandFilter").value = "";
      loadCollection();
    });
    document.querySelector("#collectionTable").addEventListener("click", onCollectionAction);
    await loadCollection();
  } catch (error) {
    toast(error.message);
  }
});

async function loadCollection() {
  const params = new URLSearchParams();
  const status = document.querySelector("#ownershipFilter").value;
  const brand = document.querySelector("#brandFilter").value;
  if (status) params.set("ownership_status", status);
  if (brand) params.set("brand", brand);
  collectionRows = await api(`/api/collection?${params.toString()}`);
  renderCollection(collectionRows);
}

function renderCollection(rows) {
  document.querySelector("#collectionCount").textContent = `${rows.length} records`;
  const tbody = document.querySelector("#collectionTable");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">No collection records</td></tr>`;
    return;
  }
  tbody.innerHTML = rows
    .map(
      (row) => `
      <tr data-id="${row.id}">
        <td>
          <span class="item-title">
            <strong>${row.name}</strong>
            <small>${row.brand} / ${row.series_title}</small>
          </span>
        </td>
        <td>
          <select class="inline-input" data-field="ownership_status">
            ${collectionOptions.ownership_statuses
              .map((status) => `<option value="${status}" ${row.ownership_status === status ? "selected" : ""}>${status}</option>`)
              .join("")}
          </select>
        </td>
        <td><input class="inline-input" data-field="purchase_price" type="number" min="0" value="${text(row.purchase_price, "")}"></td>
        <td><input class="inline-input" data-field="purchase_shop" value="${text(row.purchase_shop, "")}"></td>
        <td><input class="inline-input" data-field="purchase_date" type="date" value="${text(row.purchase_date, "")}"></td>
        <td><input data-field="is_opened" type="checkbox" ${row.is_opened ? "checked" : ""}></td>
        <td><input class="inline-input memo-input" data-field="memo" value="${text(row.memo, "")}"></td>
        <td>
          <div class="row-actions">
            <button class="button small primary" data-action="save" type="button">保存</button>
            <button class="button small danger" data-action="delete" type="button">删除</button>
          </div>
        </td>
      </tr>
    `,
    )
    .join("");
}

async function onCollectionAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const tr = button.closest("tr");
  const id = tr.dataset.id;
  if (button.dataset.action === "delete") {
    await api(`/api/collection/${id}`, { method: "DELETE" });
    toast("收藏记录已删除");
    await loadCollection();
    return;
  }
  const payload = {};
  tr.querySelectorAll("[data-field]").forEach((input) => {
    payload[input.dataset.field] = input.type === "checkbox" ? input.checked : input.value;
  });
  await api(`/api/collection/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  toast("收藏记录已更新");
  await loadCollection();
}
