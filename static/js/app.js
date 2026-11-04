const yenFormatter = new Intl.NumberFormat("ja-JP", {
  style: "currency",
  currency: "JPY",
  maximumFractionDigits: 0,
});

const SUPPORTED_LANGS = ["zh", "ja", "en"];
const DEFAULT_LANG = "zh";
const LANG_STORAGE_KEY = "figureDashboardLang";
const TOKEN_STORAGE_KEY = "figureDashboardToken";

const STATUS_TRANSLATION_KEYS = {
  欲しい: "status.wishlist",
  予約済み: "status.reserved",
  所持: "status.owned",
  売却済み: "status.sold",
  見送り: "status.skipped",
  高すぎる: "status.tooExpensive",
  予約中: "status.preorder",
  発売予定: "status.planned",
  発売済み: "status.released",
};

const CONDITION_TRANSLATION_KEYS = {
  new: "condition.new",
  used: "condition.used",
};

function currentLang() {
  const stored = localStorage.getItem(LANG_STORAGE_KEY);
  return SUPPORTED_LANGS.includes(stored) ? stored : DEFAULT_LANG;
}

let translations = {};

// Only the active language is fetched. The three dictionaries are kept in
// lockstep by tests/test_i18n.py, so no runtime fallback file is needed.
async function loadTranslations() {
  const lang = currentLang();
  const version = document.documentElement.dataset.assetVersion || "";
  const suffix = version ? `?v=${encodeURIComponent(version)}` : "";
  const response = await fetch(`/static/i18n/${lang}.json${suffix}`);
  translations = await response.json();
}

// Page scripts await this before their first render so `t()` is never called
// against an empty dictionary.
const I18N_READY = loadTranslations()
  .then(() => {
    applyI18n();
  })
  .catch(() => {
    /* Rendering still works: t() falls back to returning the key itself. */
  });

function t(key, params = {}) {
  const template = translations[key] ?? key;
  return Object.entries(params).reduce(
    (value, [name, replacement]) => value.replaceAll(`{${name}}`, replacement),
    template,
  );
}

function statusLabel(value) {
  if (value === null || value === undefined || value === "") return "-";
  return t(STATUS_TRANSLATION_KEYS[value] || value);
}

function conditionLabel(value) {
  if (!value) return "-";
  return t(CONDITION_TRANSLATION_KEYS[value] || value);
}

function applyI18n(root = document) {
  const lang = currentLang();
  document.documentElement.lang = lang === "zh" ? "zh-CN" : lang;
  root.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.setAttribute("placeholder", t(el.dataset.i18nPlaceholder));
  });
  root.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
    el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel));
  });
  root.querySelectorAll(".language-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === lang);
    button.setAttribute("aria-pressed", String(button.dataset.lang === lang));
  });
}

/**
 * Escapes text before it goes into an innerHTML template. Every value that
 * originates from the database must pass through here.
 */
function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function yen(value) {
  if (value === null || value === undefined || value === "") return "-";
  const numeric = Number(value);
  return Number.isFinite(numeric) ? yenFormatter.format(numeric) : "-";
}

function text(value, fallback = "-") {
  return value === null || value === undefined || value === "" ? fallback : value;
}

/** Escaped counterpart of `text()`, for use inside innerHTML templates. */
function cell(value, fallback = "-") {
  return esc(text(value, fallback));
}

/* ---------------------------------------------------------------- auth --- */

let apiConfig = { writes_open: false, auth_required: false };

function storedToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY) || "";
}

function setStoredToken(value) {
  if (value) localStorage.setItem(TOKEN_STORAGE_KEY, value);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
  renderAuthState();
}

function canWrite() {
  return apiConfig.writes_open || (apiConfig.auth_required && Boolean(storedToken()));
}

function renderAuthState() {
  const panel = document.querySelector("#authPanel");
  if (!panel) return;
  // The lock only matters when the server actually enforces it.
  panel.hidden = apiConfig.writes_open;
  const unlocked = canWrite();
  const button = panel.querySelector("#authToggle");
  const state = panel.querySelector("#authState");
  if (state) state.textContent = unlocked ? t("auth.unlocked") : t("auth.locked");
  if (button) button.textContent = unlocked ? t("auth.lock") : t("auth.unlock");
  panel.classList.toggle("unlocked", unlocked);
  document.body.classList.toggle("read-only", !unlocked);
}

function promptForToken(message = t("auth.tokenPrompt")) {
  if (!apiConfig.auth_required) {
    toast(t("auth.readOnly"));
    return false;
  }
  const value = window.prompt(message, storedToken());
  if (value === null) return false;
  setStoredToken(value.trim());
  return Boolean(value.trim());
}

/* ----------------------------------------------------------------- api --- */

const WRITE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

async function api(path, options = {}, { retryOnAuth = true } = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (WRITE_METHODS.has(method)) {
    const token = storedToken();
    if (token) headers["X-Auth-Token"] = token;
  }

  const response = await fetch(path, { ...options, headers });
  const payload = await response.json().catch(() => ({}));

  if (response.status === 401 && retryOnAuth && WRITE_METHODS.has(method)) {
    if (promptForToken(t("auth.failed"))) {
      return api(path, options, { retryOnAuth: false });
    }
  }
  if (!response.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

async function loadApiConfig() {
  try {
    apiConfig = await api("/api/config");
  } catch {
    apiConfig = { writes_open: false, auth_required: false };
  }
  renderAuthState();
  return apiConfig;
}

/* ------------------------------------------------------------- helpers --- */

function setOptions(select, values, placeholder = t("common.all")) {
  const previous = select.value;
  select.innerHTML = "";
  if (placeholder !== null) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.appendChild(option);
  }
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value.id ?? value;
    option.textContent = value.label ?? value.name ?? value;
    select.appendChild(option);
  });
  if (previous) select.value = previous;
}

function toast(message) {
  const el = document.querySelector("#toast");
  if (!el) return;
  el.textContent = message;
  el.classList.add("visible");
  window.clearTimeout(window.__toastTimer);
  window.__toastTimer = window.setTimeout(() => el.classList.remove("visible"), 2600);
}

function badge(label, variant = "") {
  return `<span class="badge ${esc(variant)}">${esc(label)}</span>`;
}

/**
 * Builds the up/down badge from the `prev_price` the API resolves in SQL, so
 * the result stays correct regardless of filtering or pagination.
 */
function movementBadge(row) {
  if (row.prev_price === null || row.prev_price === undefined) return badge(t("prices.noPrevious"));
  const diff = Number(row.price) - Number(row.prev_price);
  if (diff === 0) return badge(t("prices.flat"));
  if (diff > 0) return badge(t("prices.up", { amount: yen(Math.abs(diff)) }), "rose");
  return badge(t("prices.down", { amount: yen(Math.abs(diff)) }), "green");
}

function bindResize(charts) {
  window.addEventListener("resize", () => {
    charts.forEach((chart) => chart && chart.resize());
  });
}

const TREND_PALETTE = ["#285a7f", "#d85b7f", "#b78a2e", "#297c63", "#111820"];

/** Multi-shop price line chart, shared by the dashboard and the detail page. */
function trendOption(rows) {
  const shops = [...new Set(rows.map((row) => row.shop_name))];
  const dates = [...new Set(rows.map((row) => row.checked_date))].sort();
  const latestByShop = new Map();
  rows.forEach((row) => {
    if (!latestByShop.has(row.shop_name)) latestByShop.set(row.shop_name, new Map());
    const byDate = latestByShop.get(row.shop_name);
    const previous = byDate.get(row.checked_date);
    if (!previous || Number(row.id) > Number(previous.id)) byDate.set(row.checked_date, row);
  });
  return {
    color: TREND_PALETTE,
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
      connectNulls: true,
      data: dates.map((date) => latestByShop.get(shop).get(date)?.price ?? null),
    })),
  };
}

/**
 * Wires a prev/next pager. `onChange` receives the requested page number.
 */
function createPager(containerId, onChange) {
  const container = document.querySelector(`#${containerId}`);
  if (!container) return { update() {}, page: 1 };
  const state = { page: 1, pages: 1 };

  container.innerHTML = `
    <button class="button small secondary" data-page-action="prev" type="button"></button>
    <span class="pager-info"></span>
    <button class="button small secondary" data-page-action="next" type="button"></button>
  `;
  const prev = container.querySelector("[data-page-action='prev']");
  const next = container.querySelector("[data-page-action='next']");
  const info = container.querySelector(".pager-info");

  prev.addEventListener("click", () => {
    if (state.page > 1) onChange(state.page - 1);
  });
  next.addEventListener("click", () => {
    if (state.page < state.pages) onChange(state.page + 1);
  });

  function update(meta) {
    state.page = meta.page;
    state.pages = meta.pages;
    prev.textContent = t("pagination.prev");
    next.textContent = t("pagination.next");
    info.textContent = t("pagination.info", { page: meta.page, pages: meta.pages });
    prev.disabled = meta.page <= 1;
    next.disabled = meta.page >= meta.pages;
    container.hidden = meta.pages <= 1;
  }

  return { update, state };
}

/* ------------------------------------------------------------ bootstrap --- */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".language-button").forEach((button) => {
    button.addEventListener("click", () => {
      localStorage.setItem(LANG_STORAGE_KEY, button.dataset.lang);
      window.location.reload();
    });
  });

  const authToggle = document.querySelector("#authToggle");
  if (authToggle) {
    authToggle.addEventListener("click", () => {
      if (canWrite() && apiConfig.auth_required) {
        setStoredToken("");
        toast(t("auth.locked"));
        return;
      }
      if (promptForToken()) toast(t("auth.unlocked"));
    });
  }
});
