# External Input Data

This folder contains externally-sourced datasets that are **not redistributable**
and therefore excluded from version control via `.gitignore`.

Users must download these files themselves from the original sources.

## Required Files

### paine_et_al.zip

- **Paper**: Paine, J., Qiu, Y., & Ricart-Huguet, J. (2024). "Endogenous Colonial
  Borders: Precolonial States and Geography in the Partition of Africa."
  *American Political Science Review*, 119(1), 1-20.
- **Download**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/9QJVJ1
- **License**: Free download from Harvard Dataverse. Terms: "This dataset not to be
  distributed/posted outside of the Harvard Dataverse."
- **Contents used**: `Shapefiles/Precolonial states/PCS.shp` (46 pre-colonial
  African state polygons, 929 KB)
- **Used by**: `R/11_integrate_precolonial_polygons.R`

### cliopatria.geojson.zip

- **Source**: Seshat Global History Databank / Cliopatria
- **Download**: https://github.com/Seshat-Global-History-Databank/seshat_browser
  (GeoJSON export from the `geojson/` directory)
- **License**: CC BY 4.0
- **Contents used**: `cliopatria_polities_only.geojson` (15,690 features, 1,618
  polities spanning 3400 BCE to 2024 CE)
- **Used by**: `R/12_integrate_cliopatria_polygons.R`
- **WHEP usage**: 4 polygons extracted for polities with no other polygon source:
  IRN-1800-1828 (Qajar Dynasty), AUH-1800-1867 (Austrian Empire),
  SWE-1800-1809 (Swedish Empire incl. Finland), SWE-1809-1814 (Sweden post-Finland)

### chgis.zip

- **Source**: China Historical GIS (CHGIS) v6, Harvard & Fudan University
- **Paper**: "CHGIS, Version: 6. (c) Fairbank Center for Chinese Studies, Harvard
  University and Center for Historical Geographical Studies, Fudan University, 2016."
- **Download**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/ST5KKM
  (Dataset: "1820 Layers UTF8 Encoding" in CHGIS v6 Dataverse)
- **License**: Free for academic use, no commercial use or redistribution.
- **Contents**: 1820 Qing Dynasty spatial layers (UTF-8 encoding):
  - `v6_1820_prov_pgn_utf.zip` — **Province polygons** (32 records, 26 used)
  - `v6_1820_pref_pgn_utf.zip` — Prefecture polygons (not used)
  - `v6_1820_cnty_pts_utf.zip` — County points (not used)
  - Plus rivers, lakes, towns, and points layers
- **Used by**: `R/13_integrate_chgis_provinces.R`
- **WHEP usage**: 26 Qing province polygons added as subnational entries (1820-1912).
  Excluded 5 South China Sea island claims and 1 treaty-disputed area (Nibuchu).
