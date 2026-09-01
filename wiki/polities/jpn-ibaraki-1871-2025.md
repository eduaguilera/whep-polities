---
polity_code: JPN-IBARAKI-1871-2025
polity_name: Ibaraki (prefecture of Japan)
start_year: 1871
end_year: 2025
type: subnational
iso3: JPN
continent: Asia
cow: NA
status: draft
last_ingest: 2026-09-01
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: JPN.14_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: JPN-1800-1895
    start_year: 1871
    end_year: 1895
    basis: prefecture inside JPN-1800-1895 for those years
  - code: JPN-1895-1945
    start_year: 1895
    end_year: 1945
    basis: prefecture inside JPN-1895-1945 for those years
  - code: JPN-1945-1952
    start_year: 1945
    end_year: 1952
    basis: prefecture inside JPN-1945-1952 for those years
  - code: JPN-1952-2025
    start_year: 1952
    end_year: 2025
    basis: prefecture inside JPN-1952-2025 for those years
---

# Ibaraki (prefecture of Japan)

## Summary

Ibaraki, a prefecture of Japan. This is a **subnational reporting unit, not a
sovereign state**: `type: subnational` keeps it out of the matcher's family/sovereignty ranking, so
it cannot compete with the national JPN chain.

**Why this entry exists.** The harmonized subnational compilation reports
prefecture figures for this unit as `JPN-IBARAKI` — **2,455 valued rows**,
1883–2022, covering area, production, yield. Under the policy decided on
[issue 400](https://github.com/eduaguilera/whep-polities/issues/400), a reporting unit qualifies for
a polity row when statistics were collected on it. Without this row those figures can only attach to
the national row, which is roughly forty times the territory they measure.

## Territorial extent

**Polygon status:** assigned from `gadm-4.1-adm1` feature `JPN.14_1` (Ibaraki). GADM 4.1 admin-1
is the present-day boundary; the prefecture system has been stable in outline since 1888,
which is why a modern feature is used without an ESTIMATE flag. This is neither a copied proxy nor an
absence — the two cases the wiki-page spec enumerates — so it is stated as a fourth form: a boundary
taken directly from a registered source at this unit's own level.

**Territory description.** Ibaraki covers roughly **6,105 km2**, centred near
36.33°N 140.26°E, which places it on a modern map of Japan. For scale, that is
about 1.6% of Japan's land area, and the figure is a **measurement of
the attached polygon**, not an independent statement about the territory.

`polygon_area_km2` is deliberately **left undeclared in the frontmatter**. Declaring it there would
put a number in the column that check A compares against the geometry it was read from, which is
self-referential and cannot be evidence (issue 195). No independently stated area for this unit
exists in this repository, so the measurement appears here in prose, labelled as such.

## Predecessors and successors

None. This unit neither succeeds nor is succeeded by another polity — its relation to the national
row is **containment**, not succession, which is precisely the distinction whep#51 exists to record.

## Sourced claims

- Japan is divided into prefectures under the modern prefecture system established by the 1871 abolition of the han (haihan-chiken), with the present configuration settled in 1888.
- The compilation reports this unit continuously across 1883–2022.

## Decisions

### d-span-follows-the-administration

`1871`–`2025` follows the modern prefecture system established by the 1871 abolition of the han (haihan-chiken), with the present configuration settled in 1888, not the data's
1883–2022 extent. A data-driven span would have to be re-spanned every time an
extract grows, and issue 308 records what re-spanning costs: banked verdicts orphaned by span drift.

### d-containment-not-succession

The national relation is expressed as 4 containment edge(s), one per era of the national
chain, rather than as a `predecessor`. A single parent field could not express it: this unit outlives
every individual national row.
