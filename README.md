# BolusBuddy

BolusBuddy is a carb-counting app for people with Type 1 diabetes. Pick foods from a catalogue, choose a portion or enter a weight, and it adds up the total carbohydrate for the meal. You can then use that total with your own insulin-to-carb ratio.

BolusBuddy counts carbohydrate only. It does not work out insulin doses.

## What it does

- About 100 common UK foods with typical portions, plus every food in McCance and Widdowson's CoFID 2021 that has a carb figure (over 3,200 foods in all).
- Search and food groups, plus portion presets with a quantity stepper, or a weight you enter yourself.
- A running meal total in grams, shown as 10 g carb portions (CP) or 15 g exchanges if you prefer.
- Your own foods, added from a packet label and saved on your phone.
- Quick entry of a carb figure from a label or menu.
- Favourite meals: save a meal with its total carbs and add it back in one tap.
- Barcode scanner: live camera scanning (or a photo of the barcode) looks the product up on Open Food Facts and fills in its carbs for you to check and save. Saved products are found instantly next time.
- Label reading: inside Claude, a photo of a nutrition panel can be read by Claude to fill in the carbs.
- Works offline and can be added to the home screen.

Carb figures come from CoFID 2021 and are converted to match UK packet labels. CoFID states carbohydrate as monosaccharide equivalents, so starch is divided by 1.10 and disaccharides by 1.05. Brands and recipes vary, so the packet label is always the better source. See [docs/cofid-check.md](docs/cofid-check.md) for how each common food compares.

## Running it

It is a static web app: `index.html`, `foods.js`, `manifest.webmanifest`, `sw.js` and the icons.

- **On your computer:** run `python3 -m http.server` in this folder and open http://localhost:8000.
- **On your phone:** host the folder on any static host (GitHub Pages works), open the address in Safari or Chrome, and choose *Add to Home Screen*.

Meals, favourites and custom foods are stored in the browser on that device only.

The live camera needs the app served over HTTPS from its own address (for example GitHub Pages). Inside a Claude artifact the camera and the Open Food Facts lookup are blocked, so there the scanner reads barcodes from photos and reads nutrition labels with Claude instead.

## Food data

`foods.js` is generated from the CoFID spreadsheets, which are published by the UK government at https://www.gov.uk/government/publications/composition-of-foods-integrated-dataset-cofid. Download both files, then run:

```
python3 -m pip install openpyxl
python3 tools/build_foods.py CoFID_2021.xlsx CoFID_oldFoods.xlsx foods.js cofid-check.csv
```

The common foods, their portions and their CoFID codes are the `CURATED` list in `tools/build_foods.py`.

## Licence and attribution

The food data is derived from McCance and Widdowson's Composition of Foods Integrated Dataset (CoFID) 2021, published by Public Health England. Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Scanned product data comes from [Open Food Facts](https://world.openfoodfacts.org), available under the Open Database Licence.
