# BolusBuddy

BolusBuddy is a carb-counting app for people with Type 1 diabetes. Pick foods from a catalogue, choose a portion or enter a weight, and it adds up the total carbohydrate for the meal. You can then use that total with your own insulin-to-carb ratio.

BolusBuddy counts carbohydrate only. It does not work out insulin doses.

## What it does

- A catalogue of about 100 common UK foods, with carbs per 100 g (or 100 ml) and typical portions.
- Search and food groups, plus portion presets with a quantity stepper, or a weight you enter yourself.
- A running meal total in grams, shown as 10 g carb portions (CP) or 15 g exchanges if you prefer.
- Your own foods, added from a packet label and saved on your phone.
- Quick entry of a carb figure from a label or menu.
- Works offline and can be added to the home screen.

The figures are typical values and are approximate. Brands and recipes vary, so the packet label is always the better source.

## Running it

It is a single static web app with no build step: `index.html`, `manifest.webmanifest`, `sw.js` and the icons.

- **On your computer:** run `python3 -m http.server` in this folder and open http://localhost:8000.
- **On your phone:** host the folder on any static host (GitHub Pages works), open the address in Safari or Chrome, and choose *Add to Home Screen*.

Meals and custom foods are stored in the browser on that device only.

## Food data

The catalogue is the `FOODS` list near the top of the script in `index.html`. Each entry is `[name, group, carbs per 100, unit, [[portion name, weight], ...]]`.
