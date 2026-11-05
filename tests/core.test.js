// Run with: node --test tests/core.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { execFileSync } = require("node:child_process");
const core = require("../core.js");

const ROOT = path.join(__dirname, "..");
function loadData() {
  const ctx = { window: {} };
  vm.runInNewContext(fs.readFileSync(path.join(ROOT, "foods.js"), "utf8"), ctx);
  vm.runInNewContext(fs.readFileSync(path.join(ROOT, "restaurants.js"), "utf8"), ctx);
  return { foods: ctx.window.BOLUS_FOODS, chains: ctx.window.BOLUS_CHAINS };
}
// The same lookups the app builds from the data.
function index(data) {
  const byId = {}, byName = {};
  const add = (f) => { byId[f.id] = f; byName[f.name] = f.name in byName ? null : f; };
  data.foods.curated.forEach((f) => add({ id: core.curatedId(f[0], f[5]), name: f[0], per100: f[2], unit: f[3] }));
  data.chains.forEach((c) => c.items.forEach((it) => add({ id: core.chainId(c.chain, it[1]), name: c.chain + " · " + it[1], perServing: it[2] })));
  return { byId, byName };
}

test("carbs per 100 g and per serving", () => {
  assert.equal(core.carbsFor({ per100: 42.1 }, 72), 42.1 * 72 / 100);
  assert.equal(core.carbsFor({ perServing: 60, per100: 60 }, 2), 120);
});

test("amount warnings", () => {
  const bread = { per100: 42.1, unit: "g" };
  const pizza = { perServing: 80, per100: 80, unit: "serving" };
  assert.equal(core.checkAmount(bread, 72, 30), "");
  assert.match(core.checkAmount(bread, 1500, 631), /more than a usual portion/);
  assert.match(core.checkAmount(pizza, 250, 20000), /servings, not grams/);
  assert.equal(core.checkAmount(pizza, 1, 80), "");
  assert.match(core.checkAmount(pizza, 2, 160), /160 g of carbs/);
  assert.equal(core.checkCarbs(60), "");
  assert.match(core.checkCarbs(500), /500 g/);
});

test("stale meals", () => {
  const now = Date.parse("2026-11-05T12:00:00Z");
  assert.equal(core.isStale([], null, now), false);
  assert.equal(core.isStale([{}], null, now), true, "a meal with no start time is treated as stale");
  assert.equal(core.isStale([{}], -1, now), true, "an old saved meal is treated as stale");
  assert.equal(core.isStale([{}], now - 60 * 60 * 1000, now), false);
  assert.equal(core.isStale([{}], now - 7 * 60 * 60 * 1000, now), true);
});

test("every food and restaurant item has a unique ID", () => {
  const data = loadData();
  const ids = new Set();
  const all = data.foods.curated.map((f) => core.curatedId(f[0], f[5]))
    .concat(data.chains.flatMap((c) => c.items.map((it) => core.chainId(c.chain, it[1]))));
  all.forEach((id) => { assert.ok(!ids.has(id), "repeated ID " + id); ids.add(id); });
  const cofid = data.foods.curated.filter((f) => f[5]).map((f) => "f" + f[5]);
  assert.equal(new Set(cofid).size, cofid.length);
});

test("IDs do not depend on list order", () => {
  const data = loadData();
  const c = data.chains[0], it = c.items[5];
  const before = core.chainId(c.chain, it[1]);
  c.items.reverse();
  assert.equal(core.chainId(c.chain, c.items[c.items.length - 6][1]), before);
  assert.equal(core.curatedId("White bread", "11-980"), "f11-980");
  assert.equal(core.curatedId("Glucose tablet", ""), "k-glucose-tablet");
});

test("JavaScript and Python make the same IDs", () => {
  const names = ["Caffè Nero", "Frankie & Benny's", "hot honey fried chicken, yuzu", "  Ä spaced  name  "];
  const py = execFileSync("python3", ["-c",
    "import sys, json; sys.path.insert(0, 'tools'); import datacheck; print(json.dumps([datacheck.slug(n) for n in json.loads(sys.argv[1])]))",
    JSON.stringify(names)], { cwd: ROOT, encoding: "utf8" });
  assert.deepEqual(JSON.parse(py), names.map(core.slug));
});

test("old saved items move to stable IDs by name, never by position", () => {
  const data = loadData();
  const { byId, byName } = index(data);
  const chain = data.chains[0];
  const items = [
    { foodId: "b0", name: "White bread", amount: 72, unit: "g", carbs: 30 },
    { foodId: "b2", name: "Seeded or granary bread", amount: 44, unit: "g", carbs: 19, label: "1 slice" },
    { foodId: "r0-3", name: chain.chain + " · " + chain.items[3][1], amount: 1, unit: "serving", carbs: chain.items[3][2] },
    { foodId: "b1", name: "Bagel, plain", amount: 85, unit: "g", carbs: 45 },
    { foodId: null, name: "Label value", amount: null, carbs: 12 },
    { foodId: "cabc123", name: "My wrap", amount: 62, unit: "g", carbs: 30 }
  ];
  const unlinked = core.migrateItems(items, byId, byName);
  assert.equal(items[0].foodId, "f11-980");
  assert.equal(items[1].foodId, null, "a renamed food is unlinked, not guessed");
  assert.equal(items[1].carbs, 19, "an unlinked item keeps its carbs");
  assert.equal(items[2].foodId, core.chainId(chain.chain, chain.items[3][1]));
  assert.equal(items[3].foodId, "f11-970", "b1 was Wholemeal bread by position, but the item is a bagel");
  assert.equal(items[4].foodId, null);
  assert.equal(items[5].foodId, "cabc123", "the user's own foods are left alone");
  assert.equal(unlinked, 1);
});

test("an item never resolves to a food with a different name", () => {
  const byId = { f1: { id: "f1", name: "Bagel" } };
  assert.equal(core.resolve({ foodId: "f1", name: "Burger bun" }, byId, {}), null);
  assert.equal(core.resolve({ foodId: "f1", name: "Bagel" }, byId, {}).id, "f1");
});

test("favourites are recalculated and changes reported", () => {
  const byId = { f1: { id: "f1", name: "Parsnips, roasted", per100: 26.6, unit: "g" } };
  const items = [
    { foodId: "f1", name: "Parsnips, roasted", amount: 80, carbs: 10.4 },
    { foodId: null, name: "Label value", amount: null, carbs: 20 }
  ];
  const changed = core.refreshItems(items, byId, {});
  assert.equal(changed.length, 1);
  assert.equal(items[0].carbs, 26.6 * 80 / 100);
  assert.equal(items[1].carbs, 20);
  assert.equal(core.refreshItems(items, byId, {}).length, 0);
});
