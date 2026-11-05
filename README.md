# BolusBuddy

BolusBuddy is a carb-counting app for people with Type 1 diabetes. Pick foods from a catalogue, choose a portion or enter a weight, and it adds up the total carbohydrate for the meal. You can then use that total with your own insulin-to-carb ratio.

BolusBuddy counts carbohydrate only. It does not work out insulin doses.

## What it does

- About 100 common UK foods with typical portions, plus every food in McCance and Widdowson's CoFID 2021 that has a carb figure (over 3,200 foods in all).
- Search and food groups, plus portion presets with a quantity stepper, or a weight you enter yourself.
- A running meal total in grams, shown as 10 g carb portions (CP) or 15 g exchanges if you prefer.
- Your own foods, added from a packet label and saved on your phone.
- Restaurant and café menus with per-serving carbs copied from each chain's own nutrition guide (see `tools/restaurants/sources.json`). Pick a chain in the group chips, or search, for example "wagamama katsu".
- Quick entry of a carb figure from a label or menu, with UK restaurant and café chains suggested. Items can be remembered under Eating out and added again in one tap.
- Favourite meals: save a meal with its total carbs and add it back in one tap.
- Barcode scanner: live camera scanning (or a photo of the barcode) looks the product up on Open Food Facts and fills in its carbs for you to check and save. Saved products are found instantly next time.
- Branded and supermarket own-brand products: search Open Food Facts by name (for example "Hovis wholemeal"), optionally narrowed to a shop such as Tesco or Aldi, and save the product you pick to My foods.
- Label reading: inside Claude, a photo of a nutrition panel can be read by Claude to fill in the carbs.
- Works offline and can be added to the home screen.

Carb figures come from CoFID 2021 and are converted to match UK packet labels. CoFID states carbohydrate as monosaccharide equivalents, so starch is divided by 1.10 and disaccharides by 1.05. Brands and recipes vary, so the packet label is always the better source. See [docs/cofid-check.md](docs/cofid-check.md) for how each common food compares.

## Running it

It is a static web app: `index.html`, `core.js`, `foods.js`, `restaurants.js`, `manifest.webmanifest`, `sw.js` and the icons. `core.js` holds the carb maths and the rules for saved data, so the tests can check them.

- **On your computer:** run `python3 -m http.server` in this folder and open http://localhost:8000.
- **On your phone:** host the folder on any static host (GitHub Pages works), open the address in Safari or Chrome, and choose *Add to Home Screen*.

Meals, favourites and custom foods are stored in the browser on that device only.

The live camera needs the app served over HTTPS from its own address (for example GitHub Pages). Inside a Claude artifact the camera and the Open Food Facts lookup are blocked, so there the scanner reads barcodes from photos and reads nutrition labels with Claude instead.

## Safety checks

BolusBuddy guards against the mistakes most likely to put a wrong figure into a meal total:

- **Unusual amounts:** more than 1,000 g or ml, more than 10 servings, or more than 150 g of carbs in one item asks you to confirm before it is added.
- **Old meals:** the meal records when it was started. A meal started more than six hours ago is offered for clearing when the app opens, so old items don't join today's total.
- **Stable food IDs:** each food is identified by its CoFID code, its name, or its chain and item name, never by its place in a list. A saved item only reopens a food with the same name. Items saved before this change are moved across by name, and any that can't be matched keep their carbs but can no longer be edited.
- **Favourites:** these are recalculated from the current food figures, and any item whose figure has changed is listed when you open the favourite.
- **Trace values:** foods where CoFID records only a trace of carbohydrate show 0 g and are marked "trace only, check the label".

## Checks and tests

```
python3 tools/datacheck.py               # food data ranges, repeated names or IDs, starchy foods at 0 g
python3 -m unittest discover -s tests    # data check rules
node --test tests/core.test.js           # carb maths, warnings, IDs and saved-data migration
```

GitHub Actions runs all three on every push. The build scripts run the same data checks and refuse to write a file that fails them.

After changing any app file or rebuilding the food data, run `python3 tools/stamp_sw.py`. It stamps `sw.js` with a new cache name so phones fetch the new copy. The data check fails while the stamp is out of date.

## Food data

`foods.js` is generated from the CoFID spreadsheets, which are published by the UK government at https://www.gov.uk/government/publications/composition-of-foods-integrated-dataset-cofid. Download both files, then run:

```
python3 -m pip install openpyxl
python3 tools/build_foods.py CoFID_2021.xlsx CoFID_oldFoods.xlsx foods.js cofid-check.csv
```

The common foods, their portions and their CoFID codes are the `CURATED` list in `tools/build_foods.py`.

## Licence and attribution

The food data is derived from McCance and Widdowson's Composition of Foods Integrated Dataset (CoFID) 2021, published by Public Health England. Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Scanned product data comes from [Open Food Facts](https://world.openfoodfacts.org), available under the Open Database Licence.

Restaurant menus are built with:

```
python3 tools/build_restaurants.py
```

Each chain is one TSV in `tools/restaurants/` with its source and date in `sources.json`. Every figure was read at least twice from the chain's own guide and kept only when the reads agreed.
