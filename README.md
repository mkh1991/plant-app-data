# 🌿 Plant Tracker

A lightweight offline-first PWA for tracking plant watering schedules and care. No accounts, no backend, no dependencies — just a single HTML file.

**Live:** https://mkh1991.github.io/plant-app-data/

## Features

- **Watering dashboard** — cards sorted by urgency (overdue → due soon → on track), with a progress bar and summary strip
- **Plant ID from photo** — point your camera at a plant and identify it via [PlantNet](https://my.plantnet.org/) (free, 500 IDs/day); auto-fills care data when the species is in the local database
- **337-plant database** — browse and filter by pet safety, care level, and placement; one-tap to pre-fill the add form
- **Offline support** — full service worker cache; works without a connection (plant ID requires internet)
- **Dark mode** — follows system preference
- **PWA installable** — add to home screen on iOS/Android

## Plant ID setup

The photo identification feature uses the [PlantNet API](https://my.plantnet.org/):

1. Sign up for a free account at [my.plantnet.org](https://my.plantnet.org/)
2. Copy your API key
3. In the app, go to **+ Add** → tap the ⚙ gear icon → paste your key

The key is stored in your browser's `localStorage` and never leaves your device.

## Stack

Single `index.html` — vanilla JS, CSS custom properties, no build step. Data persisted in `localStorage`. Service worker for offline caching.

## Deployment

The `gh-pages` branch is the live site. To deploy after changes to `main`:

```bash
git checkout gh-pages
git checkout main -- index.html
git commit -m "Deploy: <description>"
git push origin gh-pages
git checkout main
```
