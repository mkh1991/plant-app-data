#!/usr/bin/env python3
"""Add toxicity and care_level to every entry in plants_db.json."""
import json, re

# ── Toxicity: "safe" | "toxic-pets" | "toxic-all"
# toxic-pets = toxic to cats/dogs but generally safe for humans
# toxic-all  = toxic to pets AND can harm humans (irritant/poisonous)
TOXICITY_BY_GENUS = {
    # Aroids (calcium oxalate crystals — toxic-all: oral irritant to everyone)
    "epipremnum": "toxic-pets",
    "scindapsus": "toxic-pets",
    "philodendron": "toxic-pets",
    "thaumatophyllum": "toxic-pets",
    "monstera": "toxic-pets",
    "rhaphidophora": "toxic-pets",
    "spathiphyllum": "toxic-pets",
    "aglaonema": "toxic-pets",
    "dieffenbachia": "toxic-all",   # causes severe mouth numbness
    "caladium": "toxic-all",
    "colocasia": "toxic-all",
    "alocasia": "toxic-all",
    "syngonium": "toxic-pets",
    "zantedeschia": "toxic-all",    # calla lily
    "anthurium": "toxic-pets",
    # Dracaena / Asparagus family
    "dracaena": "toxic-pets",
    "cordyline": "toxic-pets",
    "asparagus": "toxic-pets",
    # Ficus
    "ficus": "toxic-pets",
    # Succulents
    "crassula": "toxic-pets",       # jade plant
    "kalanchoe": "toxic-pets",
    "euphorbia": "toxic-all",       # milky sap is caustic
    "adenium": "toxic-all",         # desert rose: cardiac glycosides
    # Aloe
    "aloe": "toxic-pets",           # safe topically for humans, toxic if ingested by pets
    # Ivy & climbers
    "hedera": "toxic-pets",
    "senecio": "toxic-all",         # string of pearls / groundsel family
    "curio": "toxic-all",
    # Palms
    "cycas": "toxic-all",           # sago palm: highly toxic, can be fatal
    # Other common toxics
    "zamioculcas": "toxic-pets",    # ZZ plant
    "schefflera": "toxic-pets",
    "lantana": "toxic-all",
    "tulipa": "toxic-pets",
    "narcissus": "toxic-pets",
    "hyacinthus": "toxic-pets",
    "nerium": "toxic-all",          # oleander: extremely toxic
    "taxus": "toxic-all",           # yew
    "solanum": "toxic-all",         # tomato (leaves), nightshade
    "lycium": "toxic-all",
    "brugmansia": "toxic-all",
    "datura": "toxic-all",
    "cestrum": "toxic-all",         # night jasmine
    "clerodendrum": "toxic-pets",
    "ipomoea": "toxic-pets",
    "convallaria": "toxic-all",     # lily of the valley
    "lilium": "toxic-pets",         # true lilies (very toxic to cats)
    "hemerocallis": "toxic-pets",   # daylily (toxic to cats)
    "hippeastrum": "toxic-pets",    # amaryllis
    "cyclamen": "toxic-pets",
    "rhododendron": "toxic-all",    # azalea
    "pieris": "toxic-all",
    "kalmia": "toxic-all",
    "taxodium": "toxic-pets",
    "juniperus": "toxic-pets",
    "podocarpus": "toxic-pets",
    "nandina": "toxic-all",
    "wisteria": "toxic-all",
    "robinia": "toxic-all",
    "laburnum": "toxic-all",
    "digitalis": "toxic-all",       # foxglove
    "colchicum": "toxic-all",
    "veratrum": "toxic-all",
    "aconitum": "toxic-all",
    "delphinium": "toxic-all",
    "helleborus": "toxic-all",
    "ranunculus": "toxic-pets",
    "clematis": "toxic-pets",
    "ligustrum": "toxic-all",       # privet
    "buxus": "toxic-all",           # boxwood
    "rhamnus": "toxic-all",
    "sambucus": "toxic-all",        # elderberry (raw)
    "pyracantha": "toxic-pets",
    "cotoneaster": "toxic-pets",
    "prunus": "toxic-pets",         # cherry/plum pits
    "malus": "toxic-pets",          # apple seeds (small amount)
}

TOXICITY_OVERRIDES = {
    # Common name exact overrides
    "lucky bamboo": "toxic-pets",   # dracaena sanderiana
    "sago palm": "toxic-all",
    "peace lily": "toxic-pets",
    "snake plant": "toxic-pets",
    "ZZ plant": "toxic-pets",
    "pothos": "toxic-pets",
    "english ivy": "toxic-pets",
    "string of pearls": "toxic-all",
    "string of dolphins": "toxic-all",
    "string of bananas": "toxic-all",
    "tomato": "toxic-all",
    "night jasmine": "toxic-all",
    "pencil cactus": "toxic-all",
    "crown of thorns": "toxic-all",
    "desert rose": "toxic-all",
    "oleander": "toxic-all",
    "azalea": "toxic-all",
    "wisteria": "toxic-all",
}

# ── Care level: "easy" | "moderate" | "difficult"
CARE_BY_GENUS = {
    # Very easy / hard to kill
    "zamioculcas": "easy",
    "dracaena": "easy",
    "epipremnum": "easy",
    "scindapsus": "easy",
    "aspidistra": "easy",
    "sansevieria": "easy",
    "aloe": "easy",
    "haworthia": "easy",
    "haworthiopsis": "easy",
    "gasteria": "easy",
    "crassula": "easy",
    "sedum": "easy",
    "sempervivum": "easy",
    "echeveria": "easy",
    "kalanchoe": "easy",
    "agave": "easy",
    "portulacaria": "easy",
    "beaucarnea": "easy",
    "yucca": "easy",
    "chlorophytum": "easy",
    "spathiphyllum": "easy",
    "chamaedorea": "easy",
    "rhapis": "easy",
    "peperomia": "easy",
    "tradescantia": "easy",
    "pilea": "easy",
    "hoya": "easy",
    "oxalis": "easy",
    "dypsis": "easy",
    # Moderate
    "monstera": "moderate",
    "philodendron": "moderate",
    "thaumatophyllum": "moderate",
    "ficus": "moderate",
    "aglaonema": "moderate",
    "anthurium": "moderate",
    "alocasia": "moderate",
    "colocasia": "moderate",
    "begonia": "moderate",
    "orchid": "moderate",
    "phalaenopsis": "moderate",
    "dendrobium": "moderate",
    "syngonium": "moderate",
    "rhaphidophora": "moderate",
    "calathea": "moderate",
    "goeppertia": "moderate",
    "maranta": "moderate",
    "ctenanthe": "moderate",
    "stromanthe": "moderate",
    "dieffenbachia": "moderate",
    "caladium": "moderate",
    "schefflera": "moderate",
    "cordyline": "moderate",
    "bromeliaceae": "moderate",
    "guzmania": "moderate",
    "vriesea": "moderate",
    "neoregelia": "moderate",
    "tillandsia": "moderate",
    "howea": "moderate",
    "ravenea": "moderate",
    "phoenix": "moderate",
    "strelitzia": "moderate",
    "pachira": "moderate",
    "nephrolepis": "moderate",
    "platycerium": "moderate",
    "asplenium": "moderate",
    "pellaea": "moderate",
    "dryopteris": "moderate",
    "hedera": "moderate",
    "fatsia": "moderate",
    "gardenia": "moderate",
    "cyclamen": "moderate",
    "hippeastrum": "moderate",
    "hibiscus": "moderate",
    "jasmine": "moderate",
    "jasminum": "moderate",
    "bougainvillea": "moderate",
    "plumeria": "moderate",
    "lavandula": "moderate",
    "salvia": "moderate",
    "ocimum": "moderate",
    "mentha": "moderate",
    "thymus": "moderate",
    "solanum": "moderate",
    "capsicum": "moderate",
    "fragaria": "moderate",
    "citrus": "moderate",
    "punica": "moderate",
    "olea": "moderate",
    "nepenthes": "moderate",
    "sinningia": "moderate",
    # Difficult
    "adiantum": "difficult",
    "selaginella": "difficult",
    "fittonia": "difficult",
    "streptocarpus": "moderate",    # african violet actually moderate
    "saintpaulia": "moderate",
    "dionaea": "difficult",
    "sarracenia": "difficult",
    "drosera": "difficult",
    "pinguicula": "moderate",
    "musa": "moderate",
    "ravenala": "moderate",
    "lepanthes": "difficult",
    "bonsai": "difficult",
    "acer": "difficult",
}

CARE_OVERRIDES = {
    "maidenhair fern": "difficult",
    "fiddle leaf fig": "difficult",
    "calathea white fusion": "difficult",
    "nerve plant": "difficult",
    "bonsai juniper": "difficult",
    "bonsai maple": "difficult",
    "bonsai ficus": "difficult",
    "venus flytrap": "difficult",
    "pitcher plant": "difficult",
    "tropical pitcher": "difficult",
    "ZZ plant": "easy",
    "snake plant": "easy",
    "pothos": "easy",
    "spider plant": "easy",
    "cast iron plant": "easy",
    "lucky bamboo": "easy",
    "chinese evergreen": "easy",
    "peace lily": "easy",
    "aloe vera": "easy",
    "jade plant": "easy",
    "boston fern": "moderate",
    "orchid phalaenopsis": "moderate",
    "phalaenopsis orchid": "moderate",
    "african violet": "moderate",
    "gardenia": "difficult",
    "string of pearls": "moderate",
    "string of hearts": "easy",
}


# ── Placement: "indoor" | "outdoor" | "both"
# Base rule: low/medium → indoor, medium-high → both, high → outdoor
# Genus/name overrides handle exceptions (e.g. aloe is "high" but lives indoors)
PLACEMENT_BY_GENUS = {
    # Indoor tropical foliage
    "epipremnum": "indoor", "scindapsus": "indoor", "philodendron": "indoor",
    "thaumatophyllum": "indoor", "monstera": "indoor", "rhaphidophora": "indoor",
    "spathiphyllum": "indoor", "aglaonema": "indoor", "dieffenbachia": "indoor",
    "caladium": "indoor", "syngonium": "indoor", "anthurium": "indoor",
    "dracaena": "indoor", "cordyline": "indoor", "zamioculcas": "indoor",
    "aspidistra": "indoor", "sansevieria": "indoor",
    # Indoor succulents & cacti (high-light but window-sill plants)
    "aloe": "indoor", "haworthia": "indoor", "haworthiopsis": "indoor",
    "gasteria": "indoor", "crassula": "indoor", "echeveria": "indoor",
    "kalanchoe": "indoor", "portulacaria": "indoor", "beaucarnea": "indoor",
    # Indoor palms & ferns
    "chamaedorea": "indoor", "rhapis": "indoor", "howea": "indoor",
    "nephrolepis": "indoor", "asplenium": "indoor", "platycerium": "indoor",
    # Indoor other
    "peperomia": "indoor", "pilea": "indoor", "hoya": "indoor",
    "chlorophytum": "indoor", "tradescantia": "indoor", "oxalis": "indoor",
    "pachira": "indoor", "schefflera": "indoor",
    "ficus": "indoor",          # fiddle leaf fig, rubber plant — kept indoors
    # Outdoor (vegetables, fruit, true outdoor ornamentals)
    "solanum": "outdoor", "capsicum": "outdoor", "fragaria": "outdoor",
    "citrus": "outdoor", "punica": "outdoor", "olea": "outdoor",
    "helianthus": "outdoor", "tagetes": "outdoor",
    "tulipa": "outdoor", "narcissus": "outdoor", "hyacinthus": "outdoor",
    "rosa": "outdoor", "bougainvillea": "outdoor",
    "lavandula": "outdoor",
    "cycas": "outdoor",
    # Both (herbs, plants happy indoors or outdoors)
    "ocimum": "both", "mentha": "both", "thymus": "both", "salvia": "both",
    "hibiscus": "both", "jasminum": "both", "begonia": "both",
    "strelitzia": "both", "plumeria": "both",
    "sedum": "both", "sempervivum": "both", "agave": "both", "yucca": "both",
}

PLACEMENT_OVERRIDES = {
    "aloe vera": "indoor", "jade plant": "indoor", "snake plant": "indoor",
    "pothos": "indoor", "zz plant": "indoor", "peace lily": "indoor",
    "spider plant": "indoor", "lucky bamboo": "indoor",
    "chinese evergreen": "indoor", "boston fern": "indoor",
    "fiddle leaf fig": "indoor", "rubber plant": "indoor",
    "money tree": "indoor", "bird of paradise": "both",
    "string of pearls": "indoor", "string of hearts": "indoor",
    "string of dolphins": "indoor", "string of bananas": "indoor",
    "tomato": "outdoor", "sunflower": "outdoor", "marigold": "outdoor",
    "tulip": "outdoor", "daffodil": "outdoor", "hyacinth": "outdoor",
    "lavender": "outdoor", "rosemary": "both", "basil": "both",
    "mint": "both", "thyme": "both",
}

PLACEMENT_BY_SUNLIGHT = {
    "low": "indoor",
    "medium": "indoor",
    "medium-high": "both",
    "high": "outdoor",
}


def get_genus(scientific_name):
    if not scientific_name:
        return ""
    return scientific_name.split()[0].lower()


def get_toxicity(plant):
    cn = plant.get("common_name", "").lower()
    sci = plant.get("scientific_name", "")
    genus = get_genus(sci)

    for key, val in TOXICITY_OVERRIDES.items():
        if key.lower() in cn:
            return val

    if genus in TOXICITY_BY_GENUS:
        return TOXICITY_BY_GENUS[genus]

    # Default: safe (most herbs, flowers, safe succulents)
    return "safe"


def get_care(plant):
    cn = plant.get("common_name", "").lower()
    sci = plant.get("scientific_name", "")
    genus = get_genus(sci)

    for key, val in CARE_OVERRIDES.items():
        if key.lower() in cn:
            return val

    if genus in CARE_BY_GENUS:
        return CARE_BY_GENUS[genus]

    return "moderate"


def get_placement(plant):
    cn = plant.get("common_name", "").lower()
    sci = plant.get("scientific_name", "")
    genus = get_genus(sci)

    for key, val in PLACEMENT_OVERRIDES.items():
        if key.lower() in cn:
            return val

    if genus in PLACEMENT_BY_GENUS:
        return PLACEMENT_BY_GENUS[genus]

    sunlight = plant.get("sunlight", "medium")
    return PLACEMENT_BY_SUNLIGHT.get(sunlight, "both")


db = json.load(open("plants_db.json"))
for p in db:
    p["toxicity"] = get_toxicity(p)
    p["care_level"] = get_care(p)
    p["placement"] = get_placement(p)

with open("plants_db.json", "w") as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

by_tox = {}
by_care = {}
by_place = {}
for p in db:
    by_tox[p["toxicity"]] = by_tox.get(p["toxicity"], 0) + 1
    by_care[p["care_level"]] = by_care.get(p["care_level"], 0) + 1
    by_place[p["placement"]] = by_place.get(p["placement"], 0) + 1

print(f"Updated {len(db)} plants")
print("Toxicity breakdown:", by_tox)
print("Care level breakdown:", by_care)
print("Placement breakdown:", by_place)
print("\nSample:")
for p in db[:5]:
    print(f"  {p['common_name']}: {p['toxicity']}, {p['care_level']}, {p['placement']}")
