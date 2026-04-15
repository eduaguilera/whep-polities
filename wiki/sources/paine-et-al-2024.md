---
source_slug: paine-et-al-2024
title: "Endogenous Colonial Borders: Precolonial States and Geography in the Partition of Africa"
author: Jack Paine, Xiaoyan Qiu, Joan Ricart-Huguet
year: 2024
url: https://www.cambridge.org/core/journals/american-political-science-review/article/endogenous-colonial-borders-precolonial-states-and-geography-in-the-partition-of-africa/132D6CBDE92946D14CCC64E59A94D3D2
access_date: 2026-04-15
type: dataset
coverage: sub-Saharan African precolonial polities, 18th–late-19th century (replication data in APSR Dataverse)
---

# Endogenous Colonial Borders: Precolonial States and Geography in the Partition of Africa

## Why it was ingested

To provide polygon boundaries and polity existence dates for sub-Saharan African precolonial states that predate CShapes 2.0 (temporal coverage from 1886) and are absent from COW. The paper assembles an original spatial dataset of precolonial polities used to analyse the relationship between precolonial statehood and the position of modern African colonial borders. Cited in the WHEP CSV `polygon_source` column as "Paine et al. (2024)" for dozens of African polity rows covering the 1800-to-conquest window (e.g., Sokoto Caliphate, Bornu Empire, Ibadan, Luba, Lunda, Zulu, Swazi, Kingdom of Benin, Ijebu, Nupe, Igala, Egba, Kingdom of Rwanda, Bundu, etc.).

## What it adds

- Boundary polygons for precolonial African states that have no CShapes coverage (before 1886) and no COW-code entry.
- A consistent spatial frame for the full list of WHEP "pre-colonial African kingdom" rows, which otherwise would have no polygon provenance.
- Endpoint dates anchored to events of colonial conquest or incorporation (British Ijebu Expedition 1892, Punitive Expedition to Benin 1897, Sokoto/Bornu conquests 1903, Swazi Convention 1894, etc.) — used by WHEP to set `end_year` on the precolonial row and `start_year` on the subsequent colonial row.

## Known limitations

- Paper's primary concern is *whether* a precolonial state existed and *where*, not precise border lines or sub-decadal dating. Polygons are approximate and drawn from a synthesis of historical atlases and secondary literature.
- Exact start dates: the WHEP 1800 floor on many rows is a *database truncation*, not a claim that the polity started in 1800; most are older (Kingdom of Benin c.1180, Luba c.1585, Lunda c.1665, Bornu founded c.1380 as Kanem-Bornu, etc.). The Paine dataset documents existence as of the paper's ~1880 snapshot but does not give authoritative founding years.
- Territorial control in precolonial African states was often tributary/ceremonial at the periphery rather than Westphalian. Polygon edges should be read as "area of recognised political authority" not "controlled territory with a surveyed border". Flag as `oq-paine-polygon-provenance` on individual pages where the boundary is load-bearing.
- The paper is a political-science work, not a historical atlas; polities may be aggregated (e.g., Sokoto Caliphate as one unit rather than its constituent emirates) in ways that differ from conventional historiography.
