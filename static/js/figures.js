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
  document.querySelector("#resultCount").textContent = `${rows.length} items`;
  const tbody = document.querySelector("#figuresTable");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty-state">No figures found</td></tr>`;
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
            ${row.is_articulated ? badge("可動", "green") : badge("固定")}
            ${row.is_limited ? badge("限定", "rose") : badge("一般")}
            ${row.height_mm ? badge(`${row.height_mm}mm`, "gold") : ""}
          </span>
        </td>
        <td>${badge(row.status || "-", row.status === "予約中" ? "rose" : "")}</td>
        <td>
          <div class="row-actions">
            <button class="button small primary" data-action="collect" data-id="${row.id}" type="button">加入收藏</button>
            <a class="button small secondary" href="${row.product_url || "#"}" target="_blank" rel="noreferrer">详情</a>
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
      memo: `${figure?.name || "Figure"} を欲しいリストに追加`,
    }),
  });
  toast("收藏已保存：欲しい");
}
