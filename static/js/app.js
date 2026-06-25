const yenFormatter = new Intl.NumberFormat("ja-JP", {
  style: "currency",
  currency: "JPY",
  maximumFractionDigits: 0,
});

function yen(value) {
  return yenFormatter.format(Number(value || 0));
}

function text(value, fallback = "-") {
  return value === null || value === undefined || value === "" ? fallback : value;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

function setOptions(select, values, placeholder = "All") {
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
    option.textContent = value.name ?? value;
    select.appendChild(option);
  });
}

function toast(message) {
  const el = document.querySelector("#toast");
  if (!el) return;
  el.textContent = message;
  el.classList.add("visible");
  window.clearTimeout(window.__toastTimer);
  window.__toastTimer = window.setTimeout(() => el.classList.remove("visible"), 2200);
}

function badge(label, variant = "") {
  return `<span class="badge ${variant}">${label}</span>`;
}

function bindResize(charts) {
  window.addEventListener("resize", () => {
    charts.forEach((chart) => chart && chart.resize());
  });
}
