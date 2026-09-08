---
polity_code: ARG-TIERRADELFUEGO-1884-2025
polity_name: Tierra del Fuego (territory/province of Argentina)
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
    basis: Territorio Nacional de Tierra del Fuego, Islas de los Estados y del Atlántico Sur, created by Ley 1532 (1884) in the same act that organized Chubut, Santa Cruz, Neuquén, Río Negro and La Pampa; administered as a national territory inside Argentina's pre-1899 national chain
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: continuation of the same Territorio Nacional inside Argentina during the short 1899-1902 national-chain segment bounded by the Puna de Atacama award and the 1902 British arbitral award
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: continuation of the Territorio Nacional (to 1990) and then Provincia de Tierra del Fuego, Antártida e Islas del Atlántico Sur (from Ley 23.775, effective 1991) inside Argentina's 1902-2025 national chain, through to the present
---

# Tierra del Fuego (territory/province of Argentina)

## Summary

Tierra del Fuego is Argentina's southernmost administrative division, occupying the eastern (Argentine) portion of the Isla Grande de Tierra del Fuego together with Isla de los Estados and other islands in the far South Atlantic, and — as a legal jurisdictional claim rather than an effectively administered area — an Antarctic sector and the Falklands/Malvinas, South Georgia and South Sandwich Islands. This entry spans 1884, when Ley 1532 organized it as a Territorio Nacional in the same legislative act that created the neighboring Territorio Nacional del Chubut, through to the present, following Ley 23.775 (1990, effective 1991) which elevated it to full provincial status as Provincia de Tierra del Fuego, Antártida e Islas del Atlántico Sur. `type: subnational` is used because Argentina has held continuous sovereignty over the effectively administered territory throughout this span (contested only vis-à-vis Chile over the island partition, settled by treaty in 1881, and vis-à-vis the UK over the South Atlantic islands, which remain outside effective Argentine administration) — what changed at 1990/1991 was Tierra del Fuego's internal constitutional status within Argentina, from national-territory governorship to provincial self-government, not its sovereign owner. This mirrors the treatment already given to the sibling Ley 1532 territories ARG-CHUBUT-1884-2025 (provincialized 1955) and ARG-SANTACRUZ-1955-2025 (also provincialized 1955, but that sibling page chose to start its own span only at its 1955 provincialization rather than its 1884 territorio origin) — this entry follows the Chubut precedent of spanning the full territorio-to-province lifetime in one row, because Ley 1532 documents 1884 as Tierra del Fuego's own organization date just as it does for Chubut.

**Why this entry exists.** Per the routing decision for unit_id ARG-TIERRADELFUEGO (admin_name "Tierra del Fuego", country Argentina): the decision identifies this as a territory that must be routed to a dedicated polity because governing policy treats provinces and national territories as equally qualifying reporting units, and no existing ARG row before this entry represented Tierra del Fuego specifically — the only candidates were Argentina's national-level totals (the ARG-1800-1899/1899-1902/1902-2025 chain), which conflate a single province's statistics with all-Argentina figures. That is the wrong container for data collected at the Tierra del Fuego administrative level, exactly as it would be wrong for Chubut or Santa Cruz data. What confirms Tierra del Fuego was a distinct, continuously identifiable administrative entity across this span is its unbroken legal existence: named and organized as a Territorio Nacional by Ley 1532 in 1884 (the same act that created the sibling Territorio Nacional del Chubut, already given its own polity row ARG-CHUBUT-1884-2025) and continued without interruption — only a change in constitutional status, not in territory or identity — as the Provincia de Tierra del Fuego, Antártida e Islas del Atlántico Sur under Ley 23.775 in 1990/1991. The routing decision itself did not supply a specific source table, row count, or year range for the input data being routed here (its `routing_reasoning` argues the general policy case rather than citing a specific dataset excerpt), which is flagged as a gap for whoever next ingests actual Tierra del Fuego statistics into this row.

## Territorial extent

**Polygon status:** Not yet assigned. `polygon_source: gadm-4.1-adm1` with `polygon_status: unassigned` (registered_source_unfetched route, per the routing decision) — GADM 4.1's admin-1 layer is the registered source family this repository uses for first-order subdivisions of a sovereign state, and it does publish Argentine provincial boundaries globally, but the locally fetched subset at data/geodata/gadm-4.1/gadm41_adm1.gpkg is curated to 81 countries and Argentina is not among them (0 features). No feature_id can be supplied until the global adm1 layer or an Argentina-inclusive subset is fetched; no construction from other registered sources is possible either, since cshapes-2.0 (the other Argentina-relevant registered source) carries only national-level ARG polygons that cannot be subdivided into provinces. This is the same gap already documented on ARG-CHUBUT-1884-2025 and ARG-SANTACRUZ-1955-2025.

**Territory description:** A reader can locate Tierra del Fuego on a modern map as the province occupying the eastern half of Isla Grande de Tierra del Fuego (the western half belongs to Chile, per the 1881 boundary treaty), plus the smaller Isla de los Estados to the east, with its capital and largest city at Ushuaia on the Beagle Channel — the southernmost city of its size in the world. The effectively administered mainland/island area (excluding the disputed Antarctic and South Atlantic island claims described below) is commonly cited at approximately 21,300 km2. Separately, the province's legal jurisdiction also nominally extends over an Argentine Antarctic Sector claim and over the Falklands/Malvinas, South Georgia and South Sandwich Islands — none of which Argentina effectively administers and none of which are internationally recognized as Argentine territory, so they are not part of the area figure above and almost certainly are not what any routed statistical data describes (see open questions). No area figure is measured from an attached geometry here, since no polygon is yet assigned to this entry.

## Predecessors and successors

Tierra del Fuego has no predecessor entry: it was created directly by Ley 1532 in 1884 as a national territory, carved from Patagonian land Argentina asserted sovereignty over (contested with Chile until the 1881 boundary treaty fixed the Isla Grande partition along the 68°34'W meridian, giving Argentina the eastern portion and Chile the western portion of the island). It has no successor entry either: the entity persists to the present as the Provincia de Tierra del Fuego, Antártida e Islas del Atlántico Sur, one of Argentina's 23 provinces since Ley 23.775 (1990, effective 1991). That provincialization is treated as an internal status change within this single polity row rather than a predecessor/successor boundary, exactly as ARG-CHUBUT-1884-2025 treats its own 1955 provincialization under Ley 14408 — the territory and its administered population did not change hands at that date, only its constitutional status within Argentina did.

## Sourced claims

- Ley 1532 (16 October 1884) organized several Argentine Patagonian and Chaco national territories in a single act, including the Territorio Nacional de Tierra del Fuego, Islas de los Estados y del Atlántico Sur, alongside Chubut, Santa Cruz, Río Negro, Neuquén and La Pampa.
- The 1881 Boundary Treaty between Argentina and Chile fixed the partition of Isla Grande de Tierra del Fuego along the 68°34'W meridian, with Argentina retaining the eastern portion (and Chile the western portion) — the boundary this polity's Argentine-administered territory has followed since before its 1884 organization as a national territory.
- Ley 23.775 (1990, effective 1991) elevated the Territorio Nacional de Tierra del Fuego, Antártida e Islas del Atlántico Sur to full provincial status, giving it its own constitution, legislature and elected governor for the first time, with its capital at Ushuaia.

## Decisions

### d-code-follows-iso3-subunit-pattern

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern, matching the Chubut/Santa Cruz siblings**

338 of 351 subnational rows in the table follow <ISO3>-<SUBUNIT>-<start>-<end> (e.g. ARG-CHUBUT-1884-2025, ARG-SANTACRUZ-1955-2025), and Tierra del Fuego is an ordinary first-order Argentine administrative division with no separate sovereign or pre-incorporation identity of its own — unlike the bespoke cases (ALK, CAL, HAW), it was never anything other than an Argentine national territory/province. The chosen code is ARG-TIERRADELFUEGO-1884-2025, following the same pattern as its Patagonian sibling rows created under the same 1884 law.

### d-span-starts-1884-not-1900

**Span starts at the 1884 Ley 1532 creation, departing from the routing decision's proposed 1900 start**

The routing decision proposed start_year 1900 but flagged this as unverified in routing_concerns ('I could not independently verify the exact date Tierra del Fuego's national territory was first organized as a distinct unit'). Ley 1532 (16 October 1884) is the same act that created the sibling Territorio Nacional del Chubut (see ARG-CHUBUT-1884-2025, container edge starting 1884) and organized nine Argentine national territories in one act, including 'Tierra del Fuego, Islas de los Estados y del Atlántico Sur' by name. Since the same law that grounds Chubut's 1884 start also names Tierra del Fuego, treating this unit as founded in 1900 rather than 1884 would be inconsistent with the sibling precedent and with the primary legal act itself. I therefore use 1884, matching Chubut's treatment, and add the ARG-1899-1902 container edge (missing from the routing decision's single proposed edge) so the container chain tiles 1884-2025 without a gap, as the containment gate requires.

## Open questions

### oq-antarctic-south-atlantic-claim-scope

**Does the Argentine national-territory/province jurisdiction over the claimed Antarctic Sector and South Atlantic islands belong in this polity's territorial extent?**

The modern Provincia de Tierra del Fuego, Antártida e Islas del Atlántico Sur legally includes an Argentine Antarctic claim sector and a claim over the Falklands/Malvinas, South Georgia and South Sandwich Islands, none of which Argentina effectively administers or which are recognized internationally as Argentine territory. Any statistical series routed to this polity (agricultural, demographic, etc.) almost certainly describes only the effectively administered mainland/island territory (the Argentine portion of Isla Grande plus Isla de los Estados), not the disputed claims. This page's territory description and any future km2/polygon work should be scoped to the administered area only, but that scoping has not been confirmed against the actual data this row will receive.

### oq-1884-vs-later-separate-organization

**Was Tierra del Fuego administered as a fully separate territorio from 1884, or initially bundled with Santa Cruz before a later separate governorship?**

Ley 1532 (1884) named Tierra del Fuego among the territories it organized, matching the treatment used for ARG-CHUBUT-1884-2025, but some secondary accounts describe the far south (Santa Cruz and Tierra del Fuego) as sharing an early joint or minimal administrative apparatus before a governor was separately seated for Tierra del Fuego specifically (commonly cited as 1904, when Ushuaia's governorship was substantively established). If the 1884-1904 window in fact had no distinct Tierra del Fuego administration separate from Santa Cruz, the effective start of a genuinely separate reporting unit may need to move later than 1884, which would also require re-checking whether any data routed to this row in that window actually distinguishes Tierra del Fuego from Santa Cruz.

### oq-gadm-argentina-adm1-missing

**GADM 4.1 admin-1 is the intended polygon source but the locally fetched subset excludes Argentina entirely**

polygon_source is set to gadm-4.1-adm1 with polygon_status unassigned (registered_source_unfetched), matching the same open gap already documented on the sibling pages ARG-CHUBUT-1884-2025 and ARG-SANTACRUZ-1955-2025: the locally fetched GADM 4.1 adm1 layer (data/geodata/gadm-4.1/gadm41_adm1.gpkg) is curated to 81 countries and Argentina is not among them (0 features). Until the full/global adm1 layer or an Argentina-inclusive subset is fetched, no feature_id can be assigned, and this affects every Argentine subnational row created in this pass, not just this one.
