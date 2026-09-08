---
polity_code: ARG-NEUQUEN-1884-2025
polity_name: Neuquén (territory/province of Argentina)
start_year: 1884
end_year: 2025
type: subnational
iso3: ARG
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: ARG-1800-1899
    start_year: 1884
    end_year: 1899
    basis: Territorio Nacional del Neuquén, created by Ley 1532 (1884), administered as a national territory of Argentina under the pre-1899 national chain
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: continuation of Territorio Nacional del Neuquén inside Argentina during the short 1899-1902 national-chain segment
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: Territorio Nacional del Neuquén (to 1955) and then Provincia del Neuquén (from Ley 14408, 1955) inside Argentina's 1902-2025 national chain, through to the present
---

# Neuquén (territory/province of Argentina)

## Summary

This page covers Neuquén, an Argentine administrative division in northern Patagonia at the foot of the Andes, from its creation as a Territorio Nacional in 1884 through its 1955 elevation to full provincial status and up to the present. The type is `subnational` because Neuquén has never held sovereignty of its own: it was and remains an internal administrative unit of Argentina, first as a national territory governed by an appointed governor reporting to Buenos Aires, then (from 1955) as a self-governing province with its own constitution, legislature, and elected governor within the Argentine federal system. The entry exists to give a single, continuous polity row to statistics collected at the Neuquén level well before 1955: the routing decision found no existing candidate polity for this unit, and treating the pre-1955 years as unroutable (as earlier verdicts did for sibling former-territorios like Chaco and Formosa) would wrongly assume the Territorio Nacional del Neuquén had no identifiable administration, when in fact it was the same continuously governed territory, merely under a different constitutional status, as the later province. Spanning 1884-2025 in one row, rather than splitting at 1955, avoids leaving 1900-1954 data unrouted and avoids an artificial predecessor/successor break at a status change that altered neither the territory's boundaries nor its identity as a single administered unit. This entry directly follows the precedent set by ARG-CHUBUT-1884-2025, created under the identical reasoning for a sibling former-territorio-nacional.

**Why this entry exists.** This entry captures Argentine national-level statistical series (agricultural/livestock production data per the juan-subnational source, cited in the routing decision as a continuous 1900-2023 run) reported at the Neuquén administrative level from around 1900 through the present. The routing decision found zero existing name candidates and zero boundary matches for Neuquén, so this data was previously unmatched rather than misrouted to a wrong polity — but a naive application of the country convention's default start rule would have fixed the span to 1955 (the provincial-elevation year), which would leave the 1900-1954 portion of the run unroutable, exactly the defect already identified and corrected for the sibling ARG-CHUBUT-1884-2025 entry. What confirms Neuquén was a distinct, continuously identifiable administrative entity across the full 1884-2025 span is its unbroken legal existence: created as Territorio Nacional del Neuquén by Ley 1532 in 1884, and continued without interruption — only a change of constitutional status, not of territory or identity — as Provincia del Neuquén under Ley 14408 in 1955. This is why a single polity row spanning 1884-2025 is the correct match rather than two rows split at the 1955 status change, following the resolution already adopted for Chubut.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is present in the GeoPackage for this unit at any period. The intended source is GADM 4.1's admin-1 layer, which does publish Argentine provincial boundaries globally, but the locally fetched subset of GADM 4.1 adm1 used by this repository is curated to 81 countries and does not currently include Argentina (0 features for ARG). This is recorded as `polygon_source: gadm-4.1-adm1` with `polygon_status: unassigned` (registered_source_unfetched route) rather than `none`, because the source family is registered in sources.yaml and the fix is to fetch Argentina's layer, not to find a different source. No construction from other registered sources is possible in the meantime: cshapes, the other Argentina-relevant registered source, carries only national-level ARG polygons and cannot be subdivided into provinces.

**Territory description:** Neuquén occupies northern Argentine Patagonia, bordered by Chile and the Andes to the west, Mendoza and La Pampa provinces to the north and east, Río Negro province to the south and east (along the Río Neuquén/Limay/Negro system), and the Río Colorado marking part of its northern limit. A reader can locate it as the province immediately north of Río Negro, spanning roughly 36°S to 39°S latitude, containing the cities of Neuquén (provincial capital), Zapala, and San Martín de los Andes, and the volcanic Andean landscape around Lanín and Copahue. The modern province covers approximately 94,078 km2, comparable in size to Portugal. Neuquén's external boundaries derive from the original Ley 1532 partition of Patagonia, adjusted afterward along the Andean frontier as the Argentina-Chile boundary was progressively settled through the early 20th century; whether the exact 1884 limits differ materially from the boundary used at 1955 provincial elevation, or from the present-day province, has not been checked against a primary source here (see open questions) — no measured-from-geometry figure is available since no polygon is yet attached.

## Predecessors and successors

Neuquén has no predecessor entry: it was created directly by Ley 1532 in 1884 as a national territory carved from Patagonian land brought under effective Argentine administration by the 1878-1885 "Conquista del Desierto" campaigns, not by splitting or merging with a previously existing polity in this database. It has no successor entry either, since the entity persists to the present as Provincia del Neuquén, one of Argentina's 23 provinces; end_year 2025 reflects the country convention's open-ended present-day cutoff, not a dissolution or absorption event. The 1955 transition from Territorio Nacional to Provincia under Ley 14408 is treated as an internal status change within this single polity row, not a predecessor/successor boundary — the same treatment applied to ARG-CHUBUT-1884-2025 and consistent with how the exemplar MAN-1950-1955 handles an administrative-tier change without creating a new row.

## Sourced claims

- Ley 1532 (16 October 1884) organized the Patagonian territories recently brought under effective Argentine administration into several Territorios Nacionales, including Neuquén, with its capital eventually fixed at the city of Neuquén.
- Ley 14408 (1955) elevated the Territorio Nacional del Neuquén to full provincial status as the Provincia del Neuquén, giving it its own constitution and elected governor for the first time.
- Argentine national-territory and provincial production series (per the routing decision, a continuous 1900-2023 data run) report Neuquén-level agricultural and livestock figures well before its 1955 provincial elevation, which is the data this polity row is created to capture.

## Decisions

### d-code-follows-iso3-subunit-pattern

**Code follows the ISO3-SUBUNIT-start-end pattern, matching the ARG-CHUBUT precedent**

The dominant pattern across the table (338 of 351 subnational rows, e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) is <ISO3>-<SUBUNIT>-<start>-<end>, and ARG already has this pattern established by ARG-BA, ARG-CAT, ARG-CF, ARG-CHUBUT, ARG-CORDOBA, and ARG-CORRIENTES. Neuquén is an ordinary Argentine administrative division with no separate historical identity outside Argentina's administrative hierarchy — it was carved out of Patagonian land brought under Argentine control by the 1878-1885 desert campaigns, exactly like Chubut, Río Negro, Santa Cruz, Chaco, Formosa, and La Pampa, all created by the same 1884 law. No bespoke code is warranted. The chosen code is ARG-NEUQUEN-1884-2025, following ARG-CHUBUT-1884-2025 exactly.

### d-span-starts-at-1884-not-1955

**Span starts at the 1884 creation of the Territorio Nacional, not at the 1955 provincial elevation**

The routing decision explicitly rejects fixing the start on provincial status (1955, Ley 14408) because doing so would leave the 1900-1954 portion of the data run unrouted — the same defect already corrected for ARG-CHUBUT-1884-2025. Neuquén was one continuously administered unit from Ley 1532 (1884) through Ley 14408 (1955) to the present: the 1955 event changed constitutional status (appointed territorial governor to elected provincial governor with own constitution and legislature) but not the identity or, so far as documented here, the boundaries of the territory. Starting at 1884 lets the full 1900-2025 data run attach to one polity row rather than splitting at a status change that is not a territorial break. This mirrors ARG-CHUBUT's resolution and is a second data point that the ARG-CHACO and ARG-FORMOSA verdicts (flagged as needing the same fix in that page's open questions) should also be revisited.

## Open questions

### oq-ley-1532-creation-date

**Confirm the exact 1884 creation date and original boundaries of Ley 1532 for Neuquén**

Ley 1532 (October 1884) created several Argentine national territories in one act (Chubut, Río Negro, Neuquén, Santa Cruz, Chaco, Formosa, Misiones, La Pampa). Secondary sources consistently cite 1884 for Neuquén's creation, but the exact promulgation date and Neuquén's originally assigned limits (which may differ from the boundary later used at 1955 provincial elevation under Ley 14408, particularly along the disputed Río Negro/Neuquén and Chile frontier sectors) have not been checked here against the law's text or against INDEC/IGN historical boundary records.

### oq-sibling-verdicts-need-revision

**ARG-CHACO and ARG-FORMOSA verdicts likely still carry the pre-elevation unroutable gap this entry avoids**

The routing decision's own routing_concerns flags that ARG-CHACO and ARG-FORMOSA verdicts treated their pre-elevation years (pre-1951/pre-1955) as unroutable under the same reasoning that was corrected here and for ARG-CHUBUT. If those verdicts have not yet been revised to start at each territory's own 1884 (or 1951, for Chaco/Formosa under Ley 14294) creation date, the pipeline will leave those provinces' early 20th-century data unrouted while Neuquén's and Chubut's are fully covered — an inconsistency across otherwise-identical Argentine national-territory-to-province histories.

### oq-gadm-argentina-not-fetched

**No Argentine provincial boundary is present locally; gadm-4.1-adm1 excludes ARG**

polygon_route is registered_source_unfetched: GADM 4.1's admin-1 layer is registered in sources.yaml and does publish Argentine provincial boundaries globally, but the locally fetched subset is curated to 81 countries and does not include Argentina (0 features for ARG). polygon_status is therefore unassigned rather than proxy or assigned, and no construction from other registered sources is possible: cshapes, the only other Argentina-relevant registered source, carries only national-level ARG polygons and cannot be subdivided into provinces. Fetching Argentina's GADM adm1 layer (or registering IGN's official provincial limits) would resolve this.

### oq-boundary-stability-1884-1955

**Whether Neuquén's pre-1955 territorial limits match the modern province is unverified**

Even once a modern provincial boundary is fetched, using it as a proxy for the 1884-1955 Territorio Nacional period carries the same moderate vintage risk noted for Chubut: Argentine national-territory boundaries were adjusted after their initial 1884 partition (in Neuquén's case, disputes along the Andean frontier with Chile were not fully settled until the early 20th century, and the Río Negro/Neuquén boundary was also subject to adjustment), and it is not confirmed here whether the original 1884 limits differ materially from the present-day province's extent.
