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
