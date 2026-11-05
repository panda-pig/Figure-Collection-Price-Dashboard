let figuresState = [];
let figureOptions = {};
let figuresPager;
let currentPage = 1;
const loadLatestFigures = createLatestLoader();

const FILTER_IDS = [
  "keyword",
  "brand",
  "series_title",
  "manufacturer",
  "release_month",
  "status",
  "is_limited",
  "is_articulated",
];

document.addEventListener("DOMContentLoaded", async () => {
  await I18N_READY;
  try {
    await loadApiConfig();
    figureOptions = await api("/api/options");
    setOptions(document.querySelector("#brand"), figureOptions.brands);
    setOptions(document.querySelector("#series_title"), figureOptions.series);
    setOptions(document.querySelector("#manufacturer"), figureOptions.manufacturers);
    setOptions(document.querySelector("#release_month"), figureOptions.release_months);
    setOptions(
      document.querySelector("#status"),
      figureOptions.statuses.map((status) => ({ id: status, label: statusLabel(status) })),
    );
    setOptions(
      document.querySelector("#collectionStatus"),
      figureOptions.ownership_statuses.map((status) => ({ id: status, label: statusLabel(status) })),
      null,
    );

    figuresPager = createPager("figuresPager", (page) => loadFigures(page));

    let debounce;
    document.querySelectorAll(".filters input, .filters select").forEach((el) => {
      const handler = () => {
        window.clearTimeout(debounce);
        debounce = window.setTimeout(() => loadFigures(1), 200);
      };
      el.addEventListener("input", handler);
      el.addEventListener("change", handler);
    });
    document.querySelector("#clearFilters").addEventListener("click", () => {
      window.clearTimeout(debounce);
      document.querySelectorAll(".filters input, .filters select").forEach((el) => {
        el.value = "";
      });
      loadFigures(1);
    });

    document.querySelector("#figuresTable").addEventListener("click", onFigureAction);
    document.querySelector("#collectionForm").addEventListener("submit", saveCollectionFromDialog);
    document.querySelector("#closeCollectionDialog").addEventListener("click", closeCollectionDialog);
    document.querySelector("#collectionForm [data-action='cancel']").addEventListener("click", closeCollectionDialog);

    document.querySelector("#addFigure").addEventListener("click", () => openFigureDialog(null));
    document.querySelector("#figureForm").addEventListener("submit", saveFigure);
    document.querySelector("#closeFigureDialog").addEventListener("click", closeFigureDialog);
    document.querySelector("#figureForm [data-action='cancel']").addEventListener("click", closeFigureDialog);

    await loadFigures(1);
  } catch (error) {
    toast(error.message);
  }
});

async function loadFigures(page = currentPage) {
  const params = new URLSearchParams();
  FILTER_IDS.forEach((id) => {
    const value = document.querySelector(`#${id}`).value;
    if (value) params.set(id, value);
  });
  const priceRange = document.querySelector("#priceRange").value;
  if (priceRange) {
    const [min, max] = priceRange.split("-");
    if (min) params.set("min_price", min);
    if (max) params.set("max_price", max);
  }
  params.set("page", page);

  await loadLatestFigures(`/api/figures?${params.toString()}`, (result) => {
    currentPage = result.page;
    figuresState = result.items;
    renderFigures(result);
    figuresPager.update(result);
  });
}

function renderFigures(result) {
  document.querySelector("#resultCount").textContent = t("common.items", { count: result.total });
  const tbody = document.querySelector("#figuresTable");
  if (!result.items.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty-state">${esc(t("figures.empty"))}</td></tr>`;
    return;
  }
  tbody.innerHTML = result.items
    .map(
      (row) => `
      <tr>
        <td>
          <span class="item-title">
            <strong>${esc(row.name)}</strong>
            <small>${cell(row.product_url, "")}</small>
          </span>
        </td>
        <td>${cell(row.brand)}</td>
        <td>${cell(row.series_title)}</td>
        <td>${cell(row.manufacturer)}</td>
        <td>${cell(row.release_date)}</td>
        <td>${esc(yen(row.official_price))}</td>
        <td>
          <span class="badge-row">
            ${row.is_articulated ? badge(t("status.articulated"), "green") : badge(t("status.fixed"))}
            ${row.is_limited ? badge(t("status.limited"), "rose") : badge(t("status.regular"))}
            ${row.height_mm ? badge(`${row.height_mm}mm`, "gold") : ""}
          </span>
        </td>
        <td>${badge(statusLabel(row.status), row.status === "予約中" ? "rose" : "")}</td>
        <td>
          <div class="row-actions">
            <button class="button small primary write-only" data-action="collect" data-id="${esc(row.id)}" type="button">${esc(t("figures.addCollection"))}</button>
            <a class="button small secondary" href="/figures/${encodeURIComponent(row.id)}">${esc(t("figures.detail"))}</a>
            <button class="button small secondary write-only" data-action="edit" data-id="${esc(row.id)}" type="button">${esc(t("button.edit"))}</button>
            <button class="button small danger write-only" data-action="delete" data-id="${esc(row.id)}" type="button">${esc(t("button.delete"))}</button>
          </div>
        </td>
      </tr>
    `,
    )
    .join("");
}

function findFigure(id) {
  return figuresState.find((item) => String(item.id) === String(id));
}

async function onFigureAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const figure = findFigure(button.dataset.id);

  try {
    if (button.dataset.action === "collect") {
      await openCollectionDialog(figure);
    } else if (button.dataset.action === "edit") {
      openFigureDialog(figure);
    } else if (button.dataset.action === "delete") {
      if (!window.confirm(t("figures.confirmDeleteFigure"))) return;
      await api(`/api/figures/${button.dataset.id}`, { method: "DELETE" });
      toast(t("figures.deleted"));
      await loadFigures();
    }
  } catch (error) {
    toast(error.message);
  }
}

/* ------------------------------------------------------- figure dialog --- */

const FIGURE_FORM_FIELDS = [
  "name",
  "brand",
  "series_title",
  "manufacturer",
  "release_date",
  "official_price",
  "height_mm",
  "scale",
  "status",
  "product_url",
  "image_url",
];

function openFigureDialog(figure) {
  const dialog = document.querySelector("#figureDialog");
  const form = document.querySelector("#figureForm");
  form.reset();
  form.dataset.figureId = figure ? figure.id : "";
  document.querySelector("#figureDialogTitle").textContent = figure
    ? t("figures.editFigure")
    : t("figures.newFigure");

  if (figure) {
    FIGURE_FORM_FIELDS.forEach((field) => {
      const input = form.elements[field];
      if (input) input.value = figure[field] ?? "";
    });
    form.elements.is_articulated.checked = Boolean(figure.is_articulated);
    form.elements.is_limited.checked = Boolean(figure.is_limited);
  }
  dialog.showModal();
}

function closeFigureDialog() {
  document.querySelector("#figureDialog").close();
}

async function saveFigure(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const figureId = form.dataset.figureId;

  const payload = {};
  FIGURE_FORM_FIELDS.forEach((field) => {
    const input = form.elements[field];
    if (!input) return;
    const value = input.value.trim();
    payload[field] = value === "" ? null : value;
  });
  payload.is_articulated = form.elements.is_articulated.checked;
  payload.is_limited = form.elements.is_limited.checked;

  if (!payload.name) {
    toast(t("figures.namePlaceholder"));
    return;
  }

  try {
    if (figureId) {
      await api(`/api/figures/${figureId}`, { method: "PUT", body: JSON.stringify(payload) });
      toast(t("figures.updated"));
    } else {
      await api("/api/figures", { method: "POST", body: JSON.stringify(payload) });
      toast(t("figures.created"));
    }
    closeFigureDialog();
    figureOptions = await api("/api/options");
    await loadFigures();
  } catch (error) {
    toast(error.message);
  }
}

/* --------------------------------------------------- collection dialog --- */

async function openCollectionDialog(figure) {
  if (!figure) return;
  const result = await api(`/api/collection?figure_id=${encodeURIComponent(figure.id)}`);
  const existing = result.items[0];
  const dialog = document.querySelector("#collectionDialog");
  const form = document.querySelector("#collectionForm");
  form.reset();
  document.querySelector("#collectionFigureId").value = figure.id;
  document.querySelector("#collectionFigureName").textContent = [figure.name, figure.brand]
    .filter(Boolean)
    .join(" / ");
  document.querySelector("#collectionStatus").value = "欲しい";
  if (existing) {
    Array.from(form.elements).forEach((input) => {
      if (!input.name || !(input.name in existing)) return;
      if (input.type === "checkbox") input.checked = Boolean(existing[input.name]);
      else input.value = existing[input.name] ?? "";
    });
  }
  dialog.showModal();
}

function closeCollectionDialog() {
  document.querySelector("#collectionDialog").close();
}

async function saveCollectionFromDialog(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());
  payload.figure_id = Number(payload.figure_id);
  payload.purchase_price = payload.purchase_price ? Number(payload.purchase_price) : null;
  payload.is_opened = formData.has("is_opened");
  if (!payload.memo) {
    const figure = findFigure(payload.figure_id);
    payload.memo = `${figure?.name || "Figure"} ${t("figures.memoAdded")}`;
  }
  try {
    await api("/api/collection", { method: "POST", body: JSON.stringify(payload) });
    closeCollectionDialog();
    toast(t("figures.saved"));
  } catch (error) {
    toast(error.message);
  }
}
