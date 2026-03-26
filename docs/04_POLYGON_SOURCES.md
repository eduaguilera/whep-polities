# Polygon Sources Documentation

This document describes where the geographic boundary (polygon) for each polity comes
from, how the sources are integrated, and what coverage gaps remain.

---

## 1. Source Datasets for Polygons

### 1.1 CShapes 2.0 (Primary Source)

- **Provider**: ETH Zurich (Schvitz et al. 2022)
- **Coverage**: 1886-2019
- **CRS**: WGS84 (EPSG:4326)
- **Geometry type**: MULTIPOLYGON
- **Resolution**: ~1:1,000,000
- **Access**: R package `cshapes`, function `cshp()`
- **License**: Creative Commons Attribution 4.0

**Key technical detail**: CShapes has TWO modes:
- `cshp(dependencies = FALSE)` (default): Returns only independent states (~315 entries)
- `cshp(dependencies = TRUE)`: Returns all entities including colonies, protectorates,
  mandates, and occupied territories (~930 entries)

**The WHEP pipeline must use `dependencies = TRUE`** to get colonial territory polygons.

**CShapes status field values**:
| Status code | Meaning | Example |
|-------------|---------|---------|
| 1 | Gleditsch-Ward independent state | France, Japan |
| 2 | COW-only state | Not in G-W list but in COW |
| 3 | Dependency/colony | British India, Belgian Congo |
| 4 | Protectorate | Bechuanaland, Swaziland |
| 5 | Occupied territory | Southern Sakhalin (Japan) |

**CShapes columns**: `gwcode`, `cowcode`, `country_name`, `start`, `end`, `status`,
`owner` (GW code of colonial power), `capname`, `caplong`, `caplat`, `b_def`, `fid`,
`geometry`.

### 1.2 CShapes-Europe Extension (Pre-1886 Europe)

- **Coverage**: 1806-2023 (extends earlier than CShapes 2.0)
- **CRS**: WGS84 (EPSG:4326)
- **Stored as**: GeoPackage (`cshapes_europe_geometries.gpkg`, 274 KB)

Provides boundaries for pre-unification European states not covered by main CShapes:
- Italian pre-unification: Sardinia/Piedmont, Two Sicilies, Papal States, Tuscany,
  Duchy of Modena, Duchy of Parma, Lucca, Massa, Kingdom of Naples
- German pre-unification: Most of the ~30 German states
- Danish pre-1864: Denmark before Schleswig-Holstein loss
- Ottoman European territories

### 1.3 GADM 4.1 (Modern Boundaries)

- **Provider**: University of California, Davis
- **Coverage**: Current snapshot (no historical data)
- **CRS**: WGS84 (EPSG:4326)
- **Geometry type**: MULTIPOLYGON
- **Resolution**: ~1:100,000 (more detailed than CShapes)
- **Access**: https://gadm.org/ or R package `geodata::gadm()`
- **License**: Free for academic use
- **Stored as**: GeoPackage (`gadm_geometries.gpkg`, 22.3 MB) + 166 cached GeoJSON files

GADM is used for:
- Modern territories without CShapes coverage (Andorra, Liechtenstein, microstates)
- Sub-national boundaries (German Lander, Australian states, UAE emirates)
- Approximating colonial territories via modern country borders (uti possidetis principle)

**Administrative levels**:
| Level | Description | Example |
|-------|------------|---------|
| L0 | Country boundary | France |
| L1 | First admin subdivision | Ile-de-France, Bavaria, Texas |
| L2 | Second subdivision | Paris, Munich |
| L3-L5 | Further subdivisions | Increasingly detailed |

### 1.4 Natural Earth (Fallback)

- **Provider**: Natural Earth (community project)
- **Coverage**: Current snapshot
- **CRS**: WGS84 (EPSG:4326)
- **Resolution**: 1:10,000,000 (most detailed scale)
- **License**: Public domain
- **Access**: R package `rnaturalearth`

Used for:
- Disputed territories (Western Sahara, Kosovo, etc.)
- Small island territories that GADM may miss
- Validation/cross-referencing

**Key layers**:
| Layer | N features | Description |
|-------|-----------|-------------|
| Admin 0 Countries | 258 | Standard country boundaries |
| Admin 0 Map Units | 298 | Includes overseas departments separately |
| Admin 0 Map Subunits | 360 | More granular subdivisions |
| Admin 0 Sovereignty | 209 | Sovereignty-based grouping |
| Breakaway/Disputed | ~100 | Disputed territories |

### 1.5 Additional Historical Sources

| Source | Coverage | Format | Access | Use case |
|--------|----------|--------|--------|----------|
| Aourednik | 800 BCE-2010 CE | GeoJSON | Free | Pre-1886 global snapshots |
| MPIDR Census Mosaic | Europe 1860-2003 | Shapefiles | Free (registration) | Pre-1886 European boundaries |
| Geo-Larhra (CNRS/Lyon) | Italy 1815-1866 | Shapefiles | Free | Italian pre-unification states |
| Thenmap API | 1945-present | GeoJSON | Free API | Post-WWII boundaries |

**Important limitation of Aourednik/Cliopatria**: These sources show empires as single
monolithic polygons (e.g., "British Empire" as one polygon, not broken into individual
colonies). WHEP needs separate polygons per colonial territory because each has its
own trade data.

---

## 2. Polygon Assignment Strategy

### Priority order for assigning polygons:

```
1. CShapes 2.0 (dependencies=TRUE)     -- 1886-2019, sovereign + colonial
2. CShapes-Europe extension             -- 1806-2023, European pre-unification
3. GADM 4.1 level 0 (direct match)     -- Modern territories still existing
4. GADM 4.1 level 1+ (subnational)     -- Sub-national entities, emirates
5. GADM combination (colonial proxy)    -- Colonial territories via modern borders
6. Natural Earth                        -- Disputed territories, small islands
7. Manual/None                          -- No polygon available
```

### 2.1 CShapes Coverage (~480 polities)

All sovereign states 1886-2019 plus colonial/dependent territories when loaded with
`dependencies = TRUE`. This is the primary source and covers the largest number of
polities.

**Includes**: All major sovereign states, British colonial territories (India, Malaya,
East Africa, etc.), French colonial territories (Indochina, West Africa, Equatorial
Africa, etc.), Belgian Congo, Dutch East Indies, Portuguese colonies, German colonies,
Italian colonies, Japanese colonial acquisitions, Ottoman dependencies, League of
Nations mandates, UN trust territories.

### 2.2 CShapes-Europe Coverage (~46 polities)

Pre-1886 European entities with dedicated boundaries from the CShapes European extension:
- Pre-unification Italian states
- Pre-unification German states
- Pre-1864 Denmark
- Ottoman European territories
- Various small European states (Cracow, Frankfurt, etc.)

### 2.3 GADM Direct Match (~96 polities)

Modern territories that still exist but are not in CShapes. These use current GADM
level-0 boundaries as the polygon:

| Category | Examples | N |
|----------|---------|---|
| Microstates | Andorra, Liechtenstein, Monaco, San Marino, Vatican | 5 |
| Overseas territories | Bermuda, Cayman Islands, Guam, American Samoa | ~30 |
| Dependencies | Cook Islands, Niue, Tokelau, Pitcairn | ~15 |
| Small island states | Bahrain, Maldives, Seychelles, Tuvalu, Nauru | ~20 |
| Other | Bhutan, Brunei, Eswatini, Western Sahara | ~26 |

### 2.4 GADM Subnational (~36 polities)

Entities that correspond to subnational units in modern countries:

| Entity | GADM source | Level |
|--------|------------|-------|
| Abu Dhabi | ARE L1 "Abu Dhabi" | 1 |
| Ajman | ARE L1 "Ajman" | 1 |
| Fujairah | ARE L1 "Fujairah" | 1 |
| Sharjah | ARE L1 "Sharjah" | 1 |
| Ras al Khaimah | ARE L1 "Ras al Khaimah" | 1 |
| Umm al Qawain | ARE L1 "Umm al Qawain" | 1 |
| Bavaria | DEU L1 "Bayern" | 1 |
| Saxony | DEU L1 "Sachsen" | 1 |
| Hanover | DEU L1 "Niedersachsen" (proxy) | 1 |
| Wurttemberg | DEU L1 "Baden-Wurttemberg" (proxy) | 1 |
| East Berlin | DEU L2 "Berlin" (subset) | 2 |
| West Berlin | DEU L2 "Berlin" (subset) | 2 |
| Queensland | AUS L1 "Queensland" | 1 |
| New South Wales | AUS L1 "New South Wales" | 1 |
| Victoria | AUS L1 "Victoria" | 1 |
| South Australia | AUS L1 "South Australia" | 1 |
| Western Australia | AUS L1 "Western Australia" | 1 |
| Tasmania | AUS L1 "Tasmania" | 1 |
| Ontario | CAN L1 "Ontario" | 1 |
| Quebec | CAN L1 "Quebec" | 1 |
| Nova Scotia | CAN L1 "Nova Scotia" | 1 |
| New Brunswick | CAN L1 "New Brunswick" | 1 |
| Prince Edward Island | CAN L1 "Prince Edward Island" | 1 |
| British Columbia | CAN L1 "British Columbia" | 1 |
| Ryukyu Islands | JPN L1 "Okinawa" | 1 |
| Tibet | CHN L1 "Xizang" | 1 |
| Yunnan | CHN L1 "Yunnan" | 1 |
| Sikkim | IND L1 "Sikkim" | 1 |
| Portuguese India (Goa) | IND L1 "Goa" + L2 Daman/Diu | 1-2 |
| Badakhshan | AFG L1 "Badakhshan" | 1 |

### 2.5 GADM Combination (Colonial Proxy, ~30 polities)

Colonial territories approximated by combining modern country boundaries. This works
because most colonial borders became modern country borders at independence via the
**uti possidetis juris** principle.

| Colonial entity | Modern country approximation | Accuracy |
|----------------|---------------------------|----------|
| Belgian Congo | DRC (COD L0) | ~95% |
| British East Africa | Kenya + Uganda (pre-separation) | ~90% |
| French West Africa | Senegal + Mali + Niger + Guinea + Ivory Coast + Burkina Faso + Benin + Mauritania | ~95% |
| French Equatorial Africa | Chad + CAR + Congo + Gabon | ~95% |
| French Indochina | Vietnam + Laos + Cambodia | ~95% |
| Dutch East Indies | Indonesia (IDN L0) | ~95% |
| Manchukuo | CHN L1 (Heilongjiang + Jilin + Liaoning + Inner Mongolia east) | ~80% |
| British Malaya | MYS L0 (peninsular portion) | ~90% |
| German East Africa | Tanzania + Rwanda + Burundi | ~95% |
| German South West Africa | Namibia (NAM L0) | ~98% |
| Portuguese East Africa | Mozambique (MOZ L0) | ~95% |
| Anglo-Egyptian Sudan | Sudan + South Sudan | ~98% |

### 2.6 Polities Without Polygons (~118 region entries + some historical)

**Regional aggregates (no polygon expected)**: FAOSTAT/M49 aggregate regions like
"Africa", "Eastern Europe", "OECD", "Least Developed Countries" etc. These are
statistical groupings, not geographic entities.

**Historical entities with no available polygon**: Some very small or short-lived
entities (Gambier Island, Palmyra Island, etc.) may lack readily available polygons.

---

## 3. CRS Compatibility

All polygon sources use **WGS84 (EPSG:4326)**. No CRS transformation is needed
when combining polygons from different sources. Polygons from different sources can
be directly combined using `sf::bind_rows()` in R after ensuring:
1. All geometries are cast to MULTIPOLYGON (using `sf::st_cast()`)
2. All geometries are validated (using `sf::st_make_valid()`)

---

## 4. Geometry Processing Pipeline

```
Source polygons (CShapes / GADM / NatEarth / CShapes-Europe)
    |
    v
st_make_valid()          -- Fix any topological errors
    |
    v
st_cast("MULTIPOLYGON")  -- Ensure consistent geometry type
    |
    v
Simplify (if needed)      -- Reduce detail for large GADM polygons
    |
    v
Combine via bind_rows()   -- Merge all sources into single sf tibble
    |
    v
Final validation           -- Check for NULLs, empty geometries, valid types
```

### Simplification

GADM polygons at ~1:100K resolution are significantly more detailed than CShapes at
~1:1M. When combining, GADM polygons may be simplified using `sf::st_simplify()` with
a tolerance of ~1 km to match CShapes resolution and reduce storage size.

---

## 5. Coverage Summary

| Source | N polities covered | Time range | Geometry type |
|--------|-------------------|------------|---------------|
| CShapes 2.0 (deps=TRUE) | ~480 | 1886-2019 | Historical boundaries |
| CShapes-Europe | ~46 | 1806-2023 | Historical European boundaries |
| GADM direct (L0) | ~96 | Current | Modern boundaries (proxy) |
| GADM subnational (L1+) | ~36 | Current | Subnational boundaries (proxy) |
| GADM combination | ~30 | Current | Combined modern (colonial proxy) |
| Natural Earth | ~10 | Current | Disputed/special territories |
| None (regions) | ~118 | N/A | Statistical aggregates |
| None (other) | ~5 | N/A | Too small/obscure |

**Total coverage**: ~700 of ~820 polities have or can have polygon geometry (~85%).
The remaining ~120 are statistical/regional aggregates that don't need polygons.

---

## 6. Known Polygon Issues

1. **GADM as historical proxy**: Using modern boundaries for colonial territories
   is ~90-95% accurate but not exact. Colonial borders sometimes differed slightly
   from modern borders.

2. **German pre-unification states**: Modern German Lander do not map exactly to
   pre-1871 states. Hesse, for example, combines parts of Hesse-Kassel and
   Hesse-Darmstadt. GADM L1 provides the best available approximation.

3. **CShapes 2.0 ends at 2019**: Post-2019 territorial changes (Crimea, South Sudan
   border adjustments) require manual polygon adjustments.

4. **Small island territories**: Some very small territories may only appear in
   Natural Earth at 1:10M scale. The 1:50M and 1:110M scales omit many small islands.

5. **Aourednik/Cliopatria empire polygons**: These sources merge colonial territories
   into single empire polygons, making them unsuitable for WHEP's per-territory approach.
   Must use GADM modern borders as colonial proxies instead.
