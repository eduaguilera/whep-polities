---
source_slug: juan-subnational
title: "WHEP harmonized subnational production compilation"
author: WHEP project (in-house compilation; per-country upstreams cited below)
publisher: Unpublished project dataset, in preparation
year: 2026
license: Project-internal. NOT redistributable and NOT committed to this repository.
access_date: 2026-09-01
type: dataset
coverage: 26 countries, 444 admin units (431 excluding national placeholders), 1860-2026; area, production and yield
---

# WHEP harmonized subnational production compilation

## What it is

The project's in-house harmonized compilation of subnational agricultural statistics:
**8,929,673 valued rows**, 26 countries, 444 admin-unit identifiers, 1860–2026, carrying
`area`, `production` and `yield`. Described in
[whep#1000](https://github.com/eduaguilera/whep/issues/1000) as the candidate constraint layer for
subnational spatialization, where it is recorded as *in preparation*.

Each row carries a stable `admin_unit_id` (e.g. `JPN-AICHI`, `USA-CALIFORNIA`), an `admin_level`,
and the cleaned country and unit names. That identifier is what this repository's polity vocabulary
is keyed to.

## NOT IN THIS REPOSITORY, BY DECISION

The panel is **never committed here**, in whole or in part. Tools read it from the path in
`WHEP_SUBNATIONAL`, defaulting to its location outside the repository, exactly as the layer-B tools
read `WHEP_LAYER_B`. What this repository stores is **vocabulary** — polity rows, containment edges,
counts and provenance — never a data row.

## Composition, by upstream

`source` values observed in the panel, with the units they cover:

| upstream | countries | units |
|---|---|---|
| Mediterranean Subnational | France, Spain, Italy, Portugal | NUTS-3 (FR, ES) and NUTS-2 (IT, PT) |
| LatAm Subnational (Infante-Amate, Urrego-Mesa et al.) | 12 Latin American countries | admin-1 |
| USDA NASS Subnational | United States | states |
| Japan Prefectural Subnational | Japan | prefectures |
| ABS Historical Agricultural Commodities | Australia | states |

## What this repository does NOT create from it

Two classes are deliberately excluded, because a polity code is an identity and not an aggregation
bucket:

- **Residual buckets.** `USA-RESID` ("Other States") is the residual of a state-level breakdown, not
  a territory.
- **National figures wearing a subnational label.** Thirteen countries in the panel have exactly one
  admin unit, each identified `<ISO>-NATIONAL` — Costa Rica, Cuba, the Dominican Republic, Ecuador,
  El Salvador, Guatemala, Honduras, Nicaragua, Panama, Paraguay, Peru, Uruguay and Venezuela. Those
  are national totals in a subnational table; creating polities for them would manufacture thirteen
  provinces that never existed.

Excluding both takes 444 identifiers to **431** creatable units.

## Known upstream defects found while matching

- **GADM 4.1 misspells Nagasaki as `Naoasaki`** in `gadm41_adm1.gpkg` (`JPN.27_1`). Recorded because
  any name-based match against that layer will silently miss the prefecture.
- The panel spells two prefectures with variant romanisations against GADM: `Gumma` for `Gunma`, and
  `Hyogo` without the macron in GADM's `Hyōgo`. Both are the same unit.
- **Okinawa is absent** from the panel's 46 Japanese prefectures, against GADM's 47. The 46 created
  prefectures sum to 370,135 km2 against Japan's ~377,975, which is consistent with Okinawa and minor
  islands being the remainder.
