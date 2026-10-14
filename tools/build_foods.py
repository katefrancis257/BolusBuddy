"""Build foods.js from the CoFID 2021 spreadsheets.

Usage: python3 tools/build_foods.py CoFID_2021.xlsx CoFID_oldFoods.xlsx

CoFID gives carbohydrate as monosaccharide equivalents. UK packet labels give
carbohydrate by weight, so each figure is converted to the label basis:
starch and oligosaccharides / 1.10, disaccharides / 1.05, monosaccharides as is.
The ratio from each food's own breakdown is applied to its published total.
"""
import csv
import json
import sys

import openpyxl

STARCH, OLIGO, SUGARS, GLU, GAL, FRU, SUC, MAL, LAC = 14, 15, 16, 17, 18, 19, 20, 21, 22
DEFAULT_RATIO = 1 / 1.07  # used only when a food has no starch and sugar breakdown

# Curated foods: name, group, CoFID code (None if not in CoFID), fallback carbs per 100, unit, portions
CURATED = [
    ["White bread", "Bread", "11-980", None, "g", [["1 medium slice", 36], ["1 thick slice", 44]]],
    ["Wholemeal bread", "Bread", "11-981", None, "g", [["1 medium slice", 36], ["1 thick slice", 44]]],
    ["Seeded bread", "Bread", "11-947", None, "g", [["1 slice", 44]]],
    ["White bread roll, soft", "Bread", "11-1006", None, "g", [["1 roll", 60]]],
    ["Burger bun", "Bread", "11-481", None, "g", [["1 bun", 60]]],
    ["Bagel, plain", "Bread", "11-970", None, "g", [["1 bagel", 85]]],
    ["Pitta bread, white", "Bread", "11-974", None, "g", [["1 pitta", 60], ["1 mini pitta", 30]]],
    ["Tortilla wrap, plain", "Bread", "11-925", None, "g", [["1 wrap", 62], ["1 mini wrap", 35]]],
    ["Naan bread, plain", "Bread", "11-973", None, "g", [["1 large naan", 160], ["1 mini naan", 65]]],
    ["Crumpet, toasted", "Bread", "11-989", None, "g", [["1 crumpet", 55]]],
    ["English muffin", "Bread", "11-541", None, "g", [["1 muffin", 65]]],
    ["Croissant", "Bread", "11-988", None, "g", [["1 croissant", 60]]],
    ["Crispbread (rye)", "Bread", "11-822", None, "g", [["1 crispbread", 10]]],
    ["Rice cake", "Bread", "17-633", None, "g", [["1 rice cake", 8]]],

    ["Porridge oats (dry)", "Cereal", "11-788", None, "g", [["1 sachet or small bowl", 40], ["1 tablespoon", 10]]],
    ["Wheat biscuits (e.g. Weetabix)", "Cereal", "11-773", None, "g", [["1 biscuit", 19]]],
    ["Shredded wheat", "Cereal", "11-775", None, "g", [["1 biscuit", 22]]],
    ["Cornflakes", "Cereal", "11-742", None, "g", [["1 bowl", 30]]],
    ["Crisped rice cereal", "Cereal", "11-750", None, "g", [["1 bowl", 30]]],
    ["Bran flakes", "Cereal", "11-763", None, "g", [["1 bowl", 30]]],
    ["Muesli", "Cereal", "11-780", None, "g", [["1 bowl", 45]]],
    ["Granola (with nuts)", "Cereal", "11-939", None, "g", [["1 bowl", 45]]],

    ["White rice, boiled", "Rice & pasta", "11-862", None, "g", [["1 portion", 180], ["1 tablespoon", 25]]],
    ["Brown rice, boiled", "Rice & pasta", "11-869", None, "g", [["1 portion", 180], ["1 tablespoon", 25]]],
    ["Rice, uncooked", "Rice & pasta", "11-861", None, "g", [["1 portion", 75]]],
    ["Pasta, boiled", "Rice & pasta", "11-722", None, "g", [["1 portion", 230], ["1 small portion", 150]]],
    ["Wholewheat pasta, boiled", "Rice & pasta", "11-723", None, "g", [["1 portion", 230]]],
    ["Pasta, uncooked", "Rice & pasta", "11-716", None, "g", [["1 portion", 75]]],
    ["Egg noodles, boiled", "Rice & pasta", "11-724", None, "g", [["1 portion", 200]]],
    ["Rice noodles, boiled", "Rice & pasta", "11-725", None, "g", [["1 portion", 200]]],
    ["Couscous, cooked", "Rice & pasta", "11-902", None, "g", [["1 portion", 150]]],
    ["Quinoa, cooked", "Rice & pasta", None, 19, "g", [["1 portion", 150]]],

    ["Potatoes, boiled", "Potatoes", "13-490", None, "g", [["1 portion", 175], ["1 egg-sized potato", 50]]],
    ["Mashed potato", "Potatoes", "13-553", None, "g", [["1 portion", 180], ["1 scoop", 60]]],
    ["Jacket potato, with skin", "Potatoes", "13-491", None, "g", [["1 medium", 180], ["1 large", 250]]],
    ["Roast potatoes", "Potatoes", "13-534", None, "g", [["1 roast potato", 60]]],
    ["Oven chips", "Potatoes", "13-487", None, "g", [["1 portion", 165]]],
    ["Chip shop chips", "Potatoes", "13-485", None, "g", [["1 portion", 200]]],
    ["Sweet potato, baked", "Potatoes", "13-672", None, "g", [["1 medium", 130]]],

    ["Apple", "Fruit", "14-319", None, "g", [["1 medium", 150]]],
    ["Banana, peeled", "Fruit", "14-318", None, "g", [["1 medium", 100], ["1 large", 130]]],
    ["Orange, peeled", "Fruit", "14-327", None, "g", [["1 medium", 160]]],
    ["Satsuma or clementine, peeled", "Fruit", "14-326", None, "g", [["1 fruit", 70]]],
    ["Pear", "Fruit", "14-321", None, "g", [["1 medium", 160]]],
    ["Grapes", "Fruit", "14-350", None, "g", [["1 handful", 80]]],
    ["Strawberries", "Fruit", "14-324", None, "g", [["1 handful", 80]]],
    ["Blueberries", "Fruit", "14-325", None, "g", [["1 handful", 80]]],
    ["Kiwi fruit", "Fruit", "14-371", None, "g", [["1 fruit", 75]]],
    ["Mango", "Fruit", "14-378", None, "g", [["1 portion", 80]]],
    ["Pineapple", "Fruit", "14-376", None, "g", [["1 portion", 80]]],
    ["Melon", "Fruit", "14-354", None, "g", [["1 slice", 150]]],
    ["Watermelon", "Fruit", "14-296", None, "g", [["1 slice", 200]]],
    ["Raisins", "Fruit", "14-393", None, "g", [["1 mini box", 14], ["1 tablespoon", 25]]],
    ["Dates, dried", "Fruit", "14-394", None, "g", [["1 date", 8]]],

    ["Peas", "Veg & beans", "13-536", None, "g", [["1 portion", 80]]],
    ["Sweetcorn, canned", "Veg & beans", "13-529", None, "g", [["1 portion", 80]]],
    ["Carrots, boiled", "Veg & beans", "13-497", None, "g", [["1 portion", 80]]],
    ["Parsnips, roasted", "Veg & beans", "13-632", None, "g", [["1 portion", 80]]],
    ["Butternut squash, baked", "Veg & beans", "13-644", None, "g", [["1 portion", 80]]],
    ["Broccoli, boiled", "Veg & beans", "13-503", None, "g", [["1 portion", 80]]],
    ["Tomato", "Veg & beans", "13-517", None, "g", [["1 medium", 85]]],
    ["Lettuce", "Veg & beans", "13-520", None, "g", [["1 bowl", 50]]],
    ["Baked beans", "Veg & beans", "13-532", None, "g", [["Half a can", 207], ["1 small can", 150]]],
    ["Chickpeas, canned", "Veg & beans", "13-670", None, "g", [["1 portion", 80]]],
    ["Kidney beans, canned", "Veg & beans", "13-660", None, "g", [["1 portion", 80]]],
    ["Lentils, red, boiled", "Veg & beans", "13-658", None, "g", [["1 portion", 80]]],

    ["Semi-skimmed milk", "Dairy", "12-313", None, "ml", [["1 glass", 200], ["In tea or coffee", 30]]],
    ["Whole milk", "Dairy", "12-596", None, "ml", [["1 glass", 200]]],
    ["Oat drink", "Drinks", None, 6.5, "ml", [["1 glass", 200]]],
    ["Natural yoghurt", "Dairy", "12-184", None, "g", [["1 pot", 125]]],
    ["Greek-style yoghurt", "Dairy", "12-555", None, "g", [["1 pot", 125]]],
    ["Fruit yoghurt, low fat", "Dairy", "12-380", None, "g", [["1 pot", 125]]],
    ["Cheddar cheese", "Dairy", "12-346", None, "g", [["1 matchbox piece", 30]]],
    ["Vanilla ice cream", "Dairy", "12-508", None, "g", [["1 scoop", 60]]],
    ["Custard, ready made", "Dairy", "12-543", None, "g", [["1 portion", 120]]],
    ["Orange juice", "Drinks", "14-329", None, "ml", [["1 small glass", 150]]],
    ["Apple juice", "Drinks", "14-331", None, "ml", [["1 small glass", 150]]],
    ["Cola, full sugar", "Drinks", "17-175", None, "ml", [["1 can", 330]]],
    ["Lager", "Drinks", "17-749", None, "ml", [["1 pint", 568]]],

    ["Chicken nuggets (coated chicken)", "Meals", "18-503", None, "g", [["1 nugget", 18]]],
    ["Fish fingers", "Meals", "16-405", None, "g", [["1 fish finger", 28]]],
    ["Battered fish, takeaway", "Meals", "16-368", None, "g", [["1 fillet", 180]]],
    ["Pork sausage, grilled", "Meals", "19-509", None, "g", [["1 sausage", 40]]],
    ["Sausage roll", "Meals", "19-643", None, "g", [["1 sausage roll", 100]]],
    ["Pizza, cheese and tomato", "Meals", "11-936", None, "g", [["1 slice (1/8 of 12 inch)", 70], ["Whole 10 inch pizza", 330]]],
    ["Beef lasagne", "Meals", "19-523", None, "g", [["1 portion", 400]]],
    ["Tomato soup", "Meals", "17-280", None, "g", [["1 bowl", 300]]],
    ["Chicken, eggs, meat or fish (plain)", "Meals", None, 0, "g", [["1 portion", 120]]],

    ["Ready salted crisps", "Snacks & sweets", "17-671", None, "g", [["1 bag", 25]]],
    ["Popcorn, salted", "Snacks & sweets", "17-692", None, "g", [["1 bag", 30]]],
    ["Digestive biscuit", "Snacks & sweets", "11-799", None, "g", [["1 biscuit", 15]]],
    ["Chocolate digestive", "Snacks & sweets", "11-807", None, "g", [["1 biscuit", 17]]],
    ["Rich tea biscuit", "Snacks & sweets", "11-797", None, "g", [["1 biscuit", 8]]],
    ["Jaffa cake", "Snacks & sweets", "11-739", None, "g", [["1 cake", 12]]],
    ["Cereal bar", "Snacks & sweets", "11-819", None, "g", [["1 bar", 25]]],
    ["Milk chocolate", "Snacks & sweets", "17-648", None, "g", [["1 bar", 45], ["1 square", 6]]],
    ["Victoria sponge cake", "Snacks & sweets", "11-831", None, "g", [["1 slice", 60]]],
    ["Scone, plain", "Snacks & sweets", "11-827", None, "g", [["1 scone", 70]]],
    ["Jam doughnut", "Snacks & sweets", "11-849", None, "g", [["1 doughnut", 75]]],
    ["Blueberry muffin", "Snacks & sweets", "11-738", None, "g", [["1 muffin", 110]]],
    ["Sugar", "Snacks & sweets", "17-063", None, "g", [["1 teaspoon", 4]]],
    ["Honey", "Snacks & sweets", "17-050", None, "g", [["1 teaspoon", 7]]],
    ["Jam", "Snacks & sweets", "17-073", None, "g", [["1 teaspoon", 7], ["1 tablespoon", 15]]],
    ["Jelly babies (fruit gums)", "Snacks & sweets", "17-107", None, "g", [["1 sweet", 6]]],
    ["Glucose tablet", "Snacks & sweets", None, 93, "g", [["1 tablet", 3]]],
]

GROUPS = ["Bread", "Cereal", "Rice & pasta", "Potatoes", "Fruit", "Veg & beans", "Dairy", "Drinks", "Meals",
          "Meat & fish", "Eggs", "Cakes & biscuits", "Snacks & sweets", "Nuts & seeds", "Soups & sauces",
          "Fats & oils", "Herbs & spices", "Other"]


def group_for(code, name):
    n = name.lower()
    if n.startswith("pizza") or code in ("AB", "AE"):
        return "Meals"
    if code == "A":
        return "Cereal"
    for prefixes, g in [
        (("AF", "AG", "AP"), "Bread"),
        (("AI", "AK"), "Cereal"),
        (("AA", "AC", "AD", "AT"), "Rice & pasta"),
        (("AM", "AN", "AO", "AS"), "Cakes & biscuits"),
        (("BTM",), "Fats & oils"),
        (("BV",), "Meals"),
        (("B",), "Dairy"),
        (("C",), "Eggs"),
        (("DA",), "Potatoes"),
        (("DR",), "Meals"),
        (("D",), "Veg & beans"),
        (("FC",), "Drinks"),
        (("F",), "Fruit"),
        (("G",), "Nuts & seeds"),
        (("H",), "Herbs & spices"),
        (("JR", "MR", "MIG"), "Meals"),
        (("J", "M"), "Meat & fish"),
        (("O",), "Fats & oils"),
        (("P", "Q"), "Drinks"),
        (("S",), "Snacks & sweets"),
        (("W",), "Soups & sauces"),
    ]:
        if code.startswith(prefixes):
            return g
    return "Other"


def num(v):
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "N"):
        return None
    if s == "Tr":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return None


def to_label(r):
    """Return (label carbs per 100 g, method) or (None, reason)."""
    cho = num(r[11])
    if cho is None:
        return None, "no carbohydrate figure"
    if cho == 0:
        return 0.0, "exact"
    starch, oligo = num(r[STARCH]), num(r[OLIGO]) or 0.0
    mono = [num(r[i]) for i in (GLU, GAL, FRU)]
    di = [num(r[i]) for i in (SUC, MAL, LAC)]
    sugars = num(r[SUGARS])
    if starch is not None and None not in mono and None not in di:
        as_mono = starch + oligo + sum(mono) + sum(di)
        as_weight = (starch + oligo) / 1.10 + sum(mono) + sum(di) / 1.05
        method = "exact"
    elif starch is not None and sugars is not None:
        as_mono = starch + oligo + sugars
        as_weight = (starch + oligo) / 1.10 + sugars / 1.025
        method = "approx"
    else:
        return round(cho * DEFAULT_RATIO, 1), "estimated"
    if as_mono <= 0:
        return round(cho * DEFAULT_RATIO, 1), "estimated"
    return round(cho * as_weight / as_mono, 1), method


def main(new_path, old_path, out_js, out_csv):
    foods = {}
    for src, path in (("2021", new_path), ("old", old_path)):
        ws = openpyxl.load_workbook(path, read_only=True)["1.3 Proximates"]
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i < 3 or not r[0]:
                continue
            code = str(r[0]).strip()
            if code in foods:
                continue  # keep the 2021 entry when a code appears in both files
            label, method = to_label(r)
            foods[code] = {"code": code, "name": " ".join(str(r[1]).split()), "group": str(r[3] or "").strip(),
                           "src": src, "cho": num(r[11]), "label": label, "method": method}

    curated, used = [], set()
    check = []
    for name, group, code, fallback, unit, portions in CURATED:
        f = foods.get(code) if code else None
        per100 = f["label"] if f else fallback
        curated.append([name, group, per100, unit, portions, code or ""])
        if code:
            used.add(code)
        check.append({"food": name, "cofid_code": code or "", "cofid_name": f["name"] if f else "Not in CoFID",
                      "cofid_published": f["cho"] if f else "", "label_basis": per100,
                      "method": f["method"] if f else "kept previous value"})

    cofid = []
    for f in sorted(foods.values(), key=lambda x: x["name"].lower()):
        if f["label"] is None:
            continue
        flags = (1 if f["src"] == "old" else 0) | (2 if f["method"] == "estimated" else 0)
        cofid.append([f["code"], f["name"], GROUPS.index(group_for(f["group"], f["name"])), f["label"], flags])

    data = {"groups": GROUPS, "curated": curated, "cofid": cofid}
    with open(out_js, "w") as fh:
        fh.write("// Generated by tools/build_foods.py from McCance and Widdowson's CoFID 2021. Do not edit by hand.\n")
        fh.write("window.BOLUS_FOODS = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n")
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(check[0].keys()))
        w.writeheader()
        w.writerows(check)
    skipped = sum(1 for f in foods.values() if f["label"] is None)
    print(f"{len(foods)} CoFID foods read, {len(cofid)} written, {skipped} skipped without a carb figure")
    print("methods:", {m: sum(1 for f in foods.values() if f['method'] == m) for m in ("exact", "approx", "estimated")})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "foods.js",
         sys.argv[4] if len(sys.argv) > 4 else "cofid-check.csv")
