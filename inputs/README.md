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
- **Download**: https://sites.fas.harvard.edu/~chgis/
- **License**: Academic use
- **Contents**: Prefecture-level (rank 3) polygon shapefiles for Chinese historical
  administrative divisions (3,830 records). Available in WGS84 and Xian80 projections,
  GBK and UTF-8 encodings.
- **WHEP assessment**: Too granular for polity-level use. Contains subnational admin
  divisions within China, not sovereign state outer boundaries. China entries already
  covered by CShapes 2.0 + CShapes-Europe. Not currently used by any R script.
