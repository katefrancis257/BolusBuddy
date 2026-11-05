// Carb maths and saved-data rules shared by the app and the tests. No DOM access here.
(function (root) {
  "use strict";

  // Amounts above these ask the user to confirm before they reach the meal total.
  var LIMITS = { amount: 1000, servings: 10, carbs: 150 };
  // A meal started longer ago than this is offered for clearing when the app opens.
  var STALE_MS = 6 * 60 * 60 * 1000;
  // Favourite items whose figure moved by at least this much are flagged as updated.
  var CHANGE_G = 0.5;

  function fold(s) { return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); }
  function slug(s) { return fold(s).replace(/&/g, " and ").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, ""); }

  // Stable IDs: built from what a food is, never from its position in a list.
  function curatedId(name, code) { return code ? "f" + code : "k-" + slug(name); }
  function chainId(chain, item) { return "r-" + slug(chain) + "--" + slug(item); }

  function carbsFor(food, amount) { return food.perServing != null ? food.perServing * amount : food.per100 * amount / 100; }

  // Returns a warning when an amount or its carbs is out of the usual range, or "" when it looks normal.
  function checkAmount(food, amount, carbs) {
    if (food && food.perServing != null) {
      if (amount > LIMITS.servings) return "That is " + amount + " servings. This box counts servings, not grams.";
    } else if (amount > LIMITS.amount) {
      return "That is " + amount + " " + ((food && food.unit) || "g") + ", which is more than a usual portion. Check the weight.";
    }
    if (carbs > LIMITS.carbs) return "That is " + Math.round(carbs) + " g of carbs for one item. Check the amount.";
    return "";
  }
  function checkCarbs(carbs) {
    return carbs > LIMITS.carbs ? "That is " + Math.round(carbs) + " g of carbs for one item. Check the figure." : "";
  }

  // A meal is stale when it has items and was started too long ago, or its start time is unknown
  // (missing, or -1 for a meal saved before start times were kept).
  function isStale(meal, startedAt, now) {
    if (!meal || !meal.length) return false;
    if (!(startedAt > 0)) return true;
    return now - startedAt > STALE_MS;
  }

  // Finds the food a saved item came from. The name must match too, so an item never
  // re-links to a different food after the data changes.
  function resolve(item, byId, byName) {
    if (!item || !item.foodId) return null;
    var f = byId[item.foodId];
    if (f && f.name === item.name) return f;
    f = byName[item.name];
    return f || null;
  }

  // Moves saved meal and favourite items onto stable IDs. Items that cannot be matched by
  // name keep their carbs but are unlinked, so they show as label entries.
  function migrateItems(items, byId, byName) {
    var unlinked = 0;
    (items || []).forEach(function (i) {
      if (!i.foodId || i.foodId.charAt(0) === "c") return; // label entries and the user's own foods
      var f = resolve(i, byId, byName);
      if (f) { i.foodId = f.id; return; }
      i.foodId = null; i.amount = null; i.unit = "g"; i.label = ""; unlinked++;
    });
    return unlinked;
  }

  // Recalculates a favourite's items from current data. Returns the items that changed.
  function refreshItems(items, byId, byName) {
    var changed = [];
    (items || []).forEach(function (i) {
      if (i.amount == null) return;
      var f = resolve(i, byId, byName);
      if (!f) return;
      var now = carbsFor(f, i.amount);
      if (Math.abs(now - i.carbs) >= CHANGE_G) changed.push({ name: i.name, was: i.carbs, now: now });
      i.carbs = now;
    });
    return changed;
  }

  var api = { LIMITS: LIMITS, STALE_MS: STALE_MS, fold: fold, slug: slug, curatedId: curatedId, chainId: chainId,
    carbsFor: carbsFor, checkAmount: checkAmount, checkCarbs: checkCarbs, isStale: isStale, resolve: resolve,
    migrateItems: migrateItems, refreshItems: refreshItems };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BolusCore = api;
})(this);
