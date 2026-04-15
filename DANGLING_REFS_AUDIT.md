# Dangling reference audit — 2026-04-15

**Status:** closed. 0 broken references in the wiki-built site CSV after this session.

## What was done

Starting point (before session): `site/polities.csv` had 468 rows and **37 dangling references** — codes cited as `predecessor` / `successor` that had no wiki page. The new Graph tab's "Orphans & broken refs" scope made this visible.

Every one of the 37 codes also existed in the master `data/final/polities_database.csv` (1,325 rows) with research-grade notes, citing sources like *Paine et al. (2024)*, Cliopatria 0.1.3, and CShapes 2.0. The task was therefore to **write wiki pages for them** (per README rule 1b — each page needs at least one external-source citation beyond `[database]`), not to author brand-new research. No Biger 1995 access this session; pages cite Wikipedia + Paine + CShapes + Cliopatria.

After writing the first 37 pages, 8 *second-order* dangling refs surfaced (predecessors named by the newly-written pages that were themselves wiki-less). I kept filling the chain until it closed:

| Pass | Pages written | Broken refs remaining |
|------|---------------|-----------------------|
| 0 (start) | — | 37 |
| 1 (originals) | 37 | 8 |
| 2 (second-order) | 8 | 4 |
| 3 (third-order) | 4 | 2 |
| 4 (fourth-order) | 2 | 1 |
| 5 (fifth-order) | 1 | **0** |

**Totals:** 52 new wiki pages, 7 new source files, 1 log entry. Site CSV grew 468 → 519 rows.

New source files (`wiki/sources/`):
- `paine-et-al-2024.md` — cited by dozens of existing pages but never had a source file.
- `wikipedia-australian-colonies-2026-04-15.md`
- `wikipedia-african-precolonial-2026-04-15.md`
- `wikipedia-african-colonial-2026-04-15.md`
- `wikipedia-europe-asia-gaps-2026-04-15.md`
- `wikipedia-self-ref-chain-2026-04-15.md`
- `wikipedia-second-order-gaps-2026-04-15.md`

Log entry: `wiki/log.md` § `dangling-refs-audit-2026-04-15`.

## Candidate CSV fixes discovered during research (not applied)

Each of these is flagged on the relevant wiki page's *Contradictions* or *Open questions* section. None applied in this session because they are too substantial to ship without human review.

### Historical errors (page label / dates wrong)
- **`TWO-1800-1860`** — Kingdom of the Two Sicilies did not exist until 8 December 1816. Either bump `start_year` to 1816 and add predecessor rows (pre-1816 Naples + Sicily as separate polities), or rename the row to something like "Naples + Sicily (to 1860)" to justify the 1800 aggregation.
- **`NAT-1843-1895`** — Wikipedia dates the Zululand annexation to Natal at **1897**, not 1895. Consider shifting NAT's boundary.
- **`KEN-1894-1902`** — `start_year=1894` does not match the East Africa Protectorate's proclamation on 1 July 1895.
- **`LBY-1943-1949`** — CShapes ruler=ITA is anachronistic; effective control from 1943 was British (Tripolitania + Cyrenaica) / French (Fezzan) / UN (from 1949).

### Chain gaps (successors or predecessors missing)
- **`MOR-1956-1958` → `MAR-1979-2025`** — 21-year gap skipping Tarfaya (1958), Ifni (1969), Western Sahara (1975). Intermediate rows (MOR-1958-1969, MOR-1969-1975, MAR-1975-1979) need to be added. Also: MOR/MAR prefix inconsistency — MAR is the ISO-3166 code, MOR is WHEP-internal.
- **`BNU-1800-1893`** — the Rabih az-Zubayr regime (1893–1900) is not modelled. Candidate: add RAB-1893-1900 row, or extend BNU `end_year` to 1900.
- **`LND-1800-1887`** — successors listed are COD-only; should also list Angolan (ANG-* or AGO-*) and Zambian successor rows (Lunda heartland was partitioned 1884 among three colonial spheres).
- **`EGB-1830-1914`** — successor field jumps directly to NGA-1961-2025, skipping 1914–1960 British Nigeria rows. Should route via SNI or NGA-1914-1960.
- **`MNE-1913-1918`** — `successor=NA`. Correct successor is SCS-1918-1929 / YUG-* (Kingdom of Serbs, Croats and Slovenes from 1 December 1918).
- **`SMO-1912-1956`** — `predecessor=SWA-1884-1912` is factually wrong. SWA is Spanish West Africa (Saharan protectorate), not pre-Morocco. Correct predecessor should be a MOR-* row.
- **`NAT-1895-1910`** — `successor=NA`. Correct successor is ZAF-1828-2025 (Union of South Africa from 31 May 1910).
- **`OYO-1800-1836`** — successor list incomplete (Ibadan is the only listed successor; should also include Egba, Ijebu, Ilorin/Sokoto, Dahomey).

### Conceptual / chain-design issues
- **`LCA-1800-1838`** and **`VCT-1800-1833`** — WHEP splits on these islands align with the **emancipation timeline**, not a territorial or sovereignty change. Under the territorial-economic-unit rule (README §what-a-whep-polity-is), these should probably be single rows LCA-1800-2025 / VCT-1800-2025. If the splits are deliberately labour-system transitions, the labelling should say so.
- **`PAN-1800-1979`** — compresses pre-1903 Colombian Panama and 1903-1979 independent Panama into one row. Big sovereignty change on roughly unchanged territory. Split at 3 November 1903 is a judgment call.
- **`MOR-1904-1956`** vs **`SMO-1912-1956`** — the two rows overlap spatially and temporally (MOR covers the full Moroccan territory; SMO covers the Spanish zone specifically). Should consolidate.
- **`SWK-1800-1894`** + **`SWZ-1894-2025`** — under the territorial-economic-unit rule, Swaziland/Eswatini has never territorially discontinued (same king, same people, same land), so the 1894 London Convention split may be an over-granularisation. Consider merging into SWZ-1800-2025.
- **`FRS-*` vs `DJI-1886-2025`** — two parallel chains for Djibouti (FRS-1884-1977 → FRS-1977-2025 in the CSV predecessor/successor; DJI-1886-2025 as a separate page). Pre-existing issue flagged in [frs-1977-2025 oq-chain-overlap](wiki/polities/frs-1977-2025.md#oq-chain-overlap).
- **`SOK-1804-1903`** — Kano, Katsina, Adamawa etc were functionally-distinct emirates under Sokoto suzerainty. Currently collapsed into one row; could be modelled as subnational rows.
- **`MOR-1800-1904`** — Cliopatria polygon does not distinguish Bled al-makhzen (governed territory) from Bled es-siba (nominal allegiance only). CSV notes already flag this.

### Cosmetic / non-blocking
- **`AUSA-1836-1900`** and **`AUWA-1829-1900`** use WHEP-internal code prefixes (`AUSA`, `AUWA`) instead of the conventional `SA`, `WA`. Deliberate disambiguation against `AUS` federation code but worth documenting explicitly somewhere.
- **`IGL-1800-1901`** — `end_year=1901` asserted by CSV notes without a specific sourced event. The Royal Niger Company lost its charter on 31 December 1899, so the 1901 incorporation would have been by Northern Nigeria Protectorate, not RNC.
- **`NUP-1800-1897`** — CSV `polygon_source=NA`. Paine et al. (2024) likely includes the Nupe polygon; worth checking.
- Multiple rows have CShapes boundary cuts (1889, 1891, 1894, 1898, 1900, 1925 in various chains) that do not correspond to named political events. These are cartographic-area changes rather than historical events and should be labelled as such so they are not mistaken for political decisions.

## Table — final status

All 37 original + 15 cascade-induced entries resolved.

| Code | Pattern | Action | Notes |
|------|---------|--------|-------|
| ANG-1800-1890 | gap | B: page written | |
| ANG-1905-1975 | gap | B: page written | Chain-overlap w/ AGO-* flagged |
| AUSA-1836-1900 | colonial-pred | B: page written | |
| AUWA-1829-1900 | colonial-pred | B: page written | |
| BKN-1800-1897 | colonial-pred | B: page written | |
| BNU-1800-1893 | colonial-pred | B: page written | Rabih gap flagged |
| CIV-1889-1893 | 2nd-order | B: page written | |
| CIV-1893-1900 | gap | B: page written | |
| COD-1885-1891 | gap | B: page written | |
| COG-1898-1900 | 2nd-order | B: page written | |
| COG-1900-1906 | gap | B: page written | |
| EGB-1830-1914 | colonial-pred | B: page written | Chain skip flagged |
| FRS-1884-1977 | self-ref | B: page written | DJI chain overlap inherited |
| GAB-1839-1912 | gap | B: page written | |
| GOB-1800-1808 | 2nd-order | B: page written | |
| IBD-1829-1893 | colonial-pred | B: page written | |
| IGL-1800-1901 | colonial-pred | B: page written | Date source flagged |
| IJB-1800-1892 | colonial-pred | B: page written | |
| KEN-1888-1891 | 4th-order | B: page written | |
| KEN-1891-1894 | 3rd-order | B: page written | |
| KEN-1894-1902 | 2nd-order | B: page written | Start-year flagged |
| KEN-1902-1906 | gap | B: page written | |
| LBA-1800-1885 | colonial-pred | B: page written | End-year flagged |
| LBY-1912-1919 | 5th-order | B: page written | |
| LBY-1919-1925 | 4th-order | B: page written | |
| LBY-1925-1934 | 3rd-order | B: page written | |
| LBY-1934-1943 | 2nd-order | B: page written | |
| LBY-1943-1949 | gap | B: page written | Ruler anachronism flagged |
| LCA-1800-1838 | self-ref | B: page written | Merge candidate |
| LND-1800-1887 | colonial-pred | B: page written | Successor list incomplete |
| MMR-1800-1826 | gap | B: page written | |
| MNE-1913-1918 | gap | B: page written | SCS successor missing |
| MOR-1800-1904 | 3rd-order | B: page written | Siba/makhzen flagged |
| MOR-1904-1956 | 2nd-order | B: page written | SMO overlap flagged |
| MOR-1956-1958 | chain | B: page written | 21-year gap flagged |
| MYS-1946-1957 | gap | B: page written | |
| NAT-1843-1895 | 2nd-order | B: page written | 1895 vs 1897 conflict |
| NAT-1895-1910 | 3rd-order | B: page written | Successor missing |
| NSW-1800-1900 | colonial-pred | B: page written | |
| NUP-1800-1897 | colonial-pred | B: page written | Polygon missing |
| OYO-1800-1836 | 2nd-order | B: page written | Partial successors only |
| PAN-1800-1979 | self-ref | B: page written | Split candidate |
| QUE-1859-1900 | colonial-pred | B: page written | |
| SMO-1912-1956 | chain | B: page written | Wrong predecessor |
| SOK-1804-1903 | colonial-pred | B: page written | Emirate split open |
| SWK-1800-1894 | colonial-pred | B: page written | Merge candidate |
| TAS-1825-1900 | colonial-pred | B: page written | |
| TUS-1800-1860 | colonial-pred | B: page written | |
| TWO-1800-1860 | colonial-pred | B: page written | **Start-year wrong** |
| VCT-1800-1833 | self-ref | B: page written | Merge candidate |
| VIC-1851-1900 | colonial-pred | B: page written | |
| ZUL-1816-1879 | colonial-pred | B: page written | End-year debate flagged |

All 52 decisions: **B (new wiki page)**. No Type A (CSV-only fix) actions were taken in this session — CSV-fix candidates were documented instead of applied, per the user's "careful, note down what you did" directive.

## Verification

```
$ bash site/build_wiki.sh
Found 517 wiki pages with frontmatter
Wrote 519 rows to site/polities.csv (2 wiki-only, no DB row)

$ python3 (check broken refs in site/polities.csv)
rows: 519, broken refs: 0
```

Open the site, go to the Graph tab, set Scope to **"Orphans & broken refs only"** — should now show only genuinely orphaned (isolated) polities, no red "missing" nodes.
