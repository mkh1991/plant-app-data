#!/usr/bin/env python3
"""Fetch plant care data from Perenual API v2."""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

API_KEY = os.environ.get("PERENUAL_API_KEY")
if not API_KEY:
    print("ERROR: PERENUAL_API_KEY environment variable is not set.")
    print("Set it with: export PERENUAL_API_KEY=your_key_here")
    sys.exit(1)

BASE_URL = "https://perenual.com/api/v2"
DELAY = 0.5
MAX_CALLS = 94  # stay under 95

PLANTS = [
    "Radermachera",
    "Hibiscus",
    "Mimosa pudica",
    "Alocasia Frydek",
    "Jasminum sambac",
    "Jasminum grandiflorum",
    "Croton",
    "Philodendron Birkin",
    "ZZ Plant",
    "Rosemary",
    "Apple dwarf",
    "Monstera deliciosa",
    "Pothos",
    "Snake Plant",
    "Peace Lily",
    "Spider Plant",
    "Fiddle Leaf Fig",
    "Rubber Plant",
    "Boston Fern",
    "English Ivy",
    "Aloe Vera",
    "Jade Plant",
    "String of Pearls",
    "Calathea",
    "Philodendron Heartleaf",
    "Money Tree",
    "Bird of Paradise",
    "Peperomia",
    "Dracaena",
    "Chinese Evergreen",
    "Areca Palm",
    "Parlor Palm",
    "Anthurium",
    "Begonia",
    "African Violet",
    "Orchid Phalaenopsis",
    "Succulent Echeveria",
    "Cactus Barrel",
    "Lavender",
    "Mint",
    "Basil",
    "Thyme",
    "Tomato",
    "Marigold",
    "Sunflower",
    "Tulip",
    "Bamboo Lucky",
]

call_count = 0


def api_get(path, params=None):
    global call_count
    if call_count >= MAX_CALLS:
        raise RuntimeError(f"API call limit ({MAX_CALLS}) reached")
    url = f"{BASE_URL}/{path}?key={API_KEY}"
    if params:
        url += "&" + urllib.parse.urlencode(params)
    call_count += 1
    req = urllib.request.Request(url, headers={"User-Agent": "PlantTracker/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def parse_watering_days(watering_str, benchmark):
    """Convert Perenual watering info to integer days."""
    if benchmark:
        value = benchmark.get("value") or benchmark.get("unit")
        if value and isinstance(value, str) and "-" in value:
            parts = value.split("-")
            try:
                return round(sum(float(p) for p in parts) / len(parts))
            except ValueError:
                pass
        elif value:
            try:
                return round(float(str(value)))
            except ValueError:
                pass

    mapping = {
        "frequent": 3,
        "average": 7,
        "minimum": 14,
        "none": 30,
    }
    if watering_str:
        return mapping.get(watering_str.lower(), 7)
    return 7


def parse_sunlight(sunlight_list):
    """Convert Perenual sunlight array to low/medium/medium-high/high."""
    if not sunlight_list:
        return "medium"
    combined = " ".join(str(s).lower() for s in sunlight_list)
    if "full_sun" in combined or "full sun" in combined:
        if "part" in combined or "shade" in combined:
            return "medium-high"
        return "high"
    if "sun-part_shade" in combined or "sun_part_shade" in combined:
        return "medium-high"
    if "part_shade" in combined or "part shade" in combined:
        return "medium"
    if "full_shade" in combined or "full shade" in combined:
        return "low"
    return "medium"


results = []
matched = 0
failed = []

print(f"Fetching {len(PLANTS)} plants from Perenual API...")

for i, plant_name in enumerate(PLANTS):
    remaining = MAX_CALLS - call_count
    # Each plant needs 2 calls (search + details)
    if remaining < 2:
        print(f"\nAPI limit approaching — stopping after {i} plants ({matched} matched).")
        break

    print(f"[{i+1}/{len(PLANTS)}] Searching: {plant_name}", end="", flush=True)

    try:
        time.sleep(DELAY)
        search_data = api_get("species-list", {"q": plant_name, "page": 1})
        plant_list = search_data.get("data", [])

        if not plant_list:
            print(" — NO MATCH")
            failed.append(plant_name)
            continue

        best = plant_list[0]
        plant_id = best.get("id")

        time.sleep(DELAY)
        details = api_get(f"species/details/{plant_id}")

        watering = details.get("watering", "")
        benchmark = details.get("watering_general_benchmark", {})
        sunlight_raw = details.get("sunlight", [])
        if isinstance(sunlight_raw, str):
            sunlight_raw = [sunlight_raw]

        entry = {
            "common_name": details.get("common_name") or best.get("common_name") or plant_name,
            "scientific_name": (details.get("scientific_name") or [""])[0]
            if isinstance(details.get("scientific_name"), list)
            else details.get("scientific_name", ""),
            "sunlight": parse_sunlight(sunlight_raw),
            "watering_days": parse_watering_days(watering, benchmark),
            "source": "perenual",
            "_query": plant_name,
            "_watering_raw": watering,
            "_sunlight_raw": sunlight_raw,
            "care_level": details.get("care_level", ""),
            "cycle": details.get("cycle", ""),
            "indoor": details.get("indoor", None),
        }
        results.append(entry)
        matched += 1
        print(f" — matched: {entry['common_name']} ({entry['scientific_name']})")

    except RuntimeError as e:
        print(f"\n{e}")
        break
    except Exception as e:
        print(f" — ERROR: {e}")
        failed.append(plant_name)

output_path = "perenual_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n=== Summary ===")
print(f"Total API calls made: {call_count}")
print(f"Plants matched:       {matched}/{len(PLANTS)}")
print(f"Failed/skipped:       {len(failed)}")
if failed:
    print(f"  Failed: {', '.join(failed)}")
print(f"Saved to: {output_path}")
