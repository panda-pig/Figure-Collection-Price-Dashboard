import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(new URL("../static/js/app.js", import.meta.url), "utf8");

async function frontend(fetch = async () => ({ ok: true, json: async () => ({}) })) {
  const context = vm.createContext({
    Intl,
    AbortController,
    URLSearchParams,
    fetch,
    localStorage: { getItem: () => null },
    document: {
      body: { classList: { toggle() {} } },
      documentElement: { dataset: {} },
      querySelectorAll: () => [],
      querySelector: () => null,
      addEventListener() {},
    },
  });
  vm.runInContext(source, context);
  await vm.runInContext("I18N_READY", context);
  return context;
}

test("trend uses the newest same-day observation regardless of response order", async () => {
  const context = await frontend();
  const rows = [
    { id: 1, shop_name: "a", checked_date: "2026-01-01", price: 100 },
    { id: 3, shop_name: "a", checked_date: "2026-01-01", price: 80 },
    { id: 2, shop_name: "b", checked_date: "2026-01-02", price: 200 },
  ];
  for (const input of [rows, [...rows].reverse()]) {
    context.rows = input;
    const result = vm.runInContext("trendOption(rows)", context);
    const data = Object.fromEntries(result.series.map((series) => [series.name, Array.from(series.data)]));
    assert.deepEqual(data, { a: [80, null], b: [null, 200] });
    assert.deepEqual(Array.from(result.xAxis.data), ["2026-01-01", "2026-01-02"]);
  }
});

test("a newer filter request cancels the old one and only renders the latest results", async () => {
  const pending = new Map();
  const context = await frontend((path, options) => {
    if (!path.startsWith("/api/")) return { ok: true, json: async () => ({}) };
    return new Promise((resolve) => pending.set(path, { resolve, signal: options.signal }));
  });
  context.rendered = [];
  vm.runInContext("const load = createLatestLoader()", context);
  const first = vm.runInContext('load("/api/figures?brand=old", (data) => rendered.push(data.brand))', context);
  const second = vm.runInContext('load("/api/figures?brand=new", (data) => rendered.push(data.brand))', context);
  assert.equal(pending.get("/api/figures?brand=old").signal.aborted, true);
  pending.get("/api/figures?brand=new").resolve({ ok: true, json: async () => ({ brand: "new" }) });
  await second;
  pending.get("/api/figures?brand=old").resolve({ ok: true, json: async () => ({ brand: "old" }) });
  await first;
  assert.deepEqual(context.rendered, ["new"]);
});

test("only a current request failure is reported", async () => {
  const failures = [];
  const context = await frontend((path) => {
    if (!path.startsWith("/api/")) return { ok: true, json: async () => ({}) };
    return new Promise((_, reject) => failures.push(reject));
  });
  context.messages = [];
  vm.runInContext("toast = (message) => messages.push(message); const load = createLatestLoader()", context);
  const first = vm.runInContext('load("/api/prices/1", () => {})', context);
  const second = vm.runInContext('load("/api/prices/2", () => {})', context);
  failures[0](new Error("cancelled"));
  failures[1](new Error("offline"));
  await first;
  await second;
  assert.deepEqual(context.messages, ["offline"]);
});

test("collection fields track write access changes", async () => {
  const context = await frontend();
  const field = { disabled: false };
  context.document.querySelectorAll = () => [field];
  vm.runInContext("renderAuthState()", context);
  assert.equal(field.disabled, true);
  vm.runInContext("apiConfig.writes_open = true; renderAuthState()", context);
  assert.equal(field.disabled, false);
  vm.runInContext("apiConfig.writes_open = false; renderAuthState()", context);
  assert.equal(field.disabled, true);
});

test("price date defaults to the local calendar date, not UTC", async () => {
  const context = await frontend();
  const input = {};
  context.document.querySelector = () => input;
  context.localDate = {
    getFullYear: () => 2026,
    getMonth: () => 0,
    getDate: () => 1,
    toISOString: () => "2025-12-31T16:00:00.000Z",
  };
  const prices = readFileSync(new URL("../static/js/prices.js", import.meta.url), "utf8");
  vm.runInContext(prices, context);
  vm.runInContext("resetCheckedDate(localDate)", context);
  assert.equal(input.value, "2026-01-01");
});

test("trend preserves zero prices and supports empty history", async () => {
  const context = await frontend();
  assert.equal(vm.runInContext("trendOption([]).series.length", context), 0);
  context.rows = [{ id: 1, shop_name: "a", checked_date: "2026-01-01", price: 0 }];
  assert.equal(vm.runInContext("trendOption(rows).series[0].data[0]", context), 0);
});

test("write controls stay locked before config loads and when config fails", async () => {
  const context = await frontend(async (path) => {
    if (path === "/api/config") throw new Error("offline");
    return { ok: true, json: async () => ({}) };
  });
  assert.equal(vm.runInContext("canWrite()", context), false);
  await vm.runInContext("loadApiConfig()", context);
  assert.equal(vm.runInContext("canWrite()", context), false);
});

test("local write controls unlock when the server allows writes", async () => {
  const context = await frontend(async () => ({
    ok: true,
    json: async () => ({ writes_open: true, auth_required: false }),
  }));
  await vm.runInContext("loadApiConfig()", context);
  assert.equal(vm.runInContext("canWrite()", context), true);
});

test("collection dialog restores saved fields, including zero price and opened state", async () => {
  const context = await frontend();
  const elements = [
    { name: "purchase_price", type: "number", value: "" },
    { name: "memo", type: "text", value: "" },
    { name: "is_opened", type: "checkbox", checked: false },
    { name: "ownership_status", type: "select-one", value: "" },
  ];
  const nodes = {
    "#collectionDialog": { showModal() { this.open = true; } },
    "#collectionForm": { elements, reset() {} },
    "#collectionFigureId": {},
    "#collectionFigureName": {},
    "#collectionStatus": elements[3],
  };
  context.document.querySelector = (selector) => nodes[selector];
  context.saved = { purchase_price: 0, memo: "keep", is_opened: 1, ownership_status: "所持" };
  vm.runInContext("api = async () => ({ items: [saved] })", context);
  const figures = readFileSync(new URL("../static/js/figures.js", import.meta.url), "utf8");
  vm.runInContext(figures, context);
  await vm.runInContext('openCollectionDialog({ id: 1, name: "Test", brand: "Brand" })', context);
  assert.equal(elements[0].value, 0);
  assert.equal(elements[1].value, "keep");
  assert.equal(elements[2].checked, true);
  assert.equal(elements[3].value, "所持");
  assert.equal(nodes["#collectionDialog"].open, true);
});
