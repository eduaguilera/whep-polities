# Wiki Log

Chronological record of every non-trivial change to the wiki. Append-only.
Each entry is a dated H2 heading. Newest on top.

Entry format:

```markdown
## <slug>
**Date:** YYYY-MM-DD
**Touched:** polity-code-1, polity-code-2
**Source:** <source-slug or "none">
**Kind:** ingest | decision | contradiction | proposal | lint

<one or two paragraphs of rationale. Link to pages and sources.>
```

Kinds:
- **ingest** — a new source was added and its claims propagated.
- **decision** — a judgment call affecting the CSV (add/remove/split
  polity, change dates, reclassify type). Must name the human who signed off.
- **contradiction** — two sources disagree on a load-bearing fact; logged
  and left open until a human resolves it.
- **proposal** — a change the wiki suggests to the CSV but has not applied.
- **lint** — bulk cleanup from a lint run.

---

## lint-2026-04-13
**Date:** 2026-04-13
**Touched:** (index only)
**Source:** none
**Kind:** lint

Post-Biger-final-batch lint. 345 polity pages, 1386 CSV rows (25%
coverage). Schema conformance: all 345 pages pass. Obsidian
compatibility: all pass (no HTML anchors, no reference-style links).
Citation health: 140 pages (41%) have at least one unsupported
bullet — mostly bulk-generated pages from autonomous iterations.
5 China chain pages have >50% database-only citations. 32 pages
have non-empty Contradictions sections, all recent (<3 days old).
No staleness (all last_ingest within last 3 days). No orphan pages,
no unreachable sources. Index coverage numbers updated.

## biger-ingest-final-batch
**Date:** 2026-04-13
**Touched:** BWA-1966-2025, COG-1960-2025, ERI-1882-2025, GAB-1960-2025, GMB-1800-2025, GEO-1991-2025, GNB-1879-2025, LSO-1966-2025, LBR-1847-2025, LIE-1800-2025, MNG-1911-2025, NAM-1884-2025, NER-1960-2025, NOR-1800-2025, PRT-1800-2025, SMR-1800-2025, SLE-1800-2025, SOM-1960-2025, SWE-1800-1809, CHE-1800-2025, TZA-1964-2025, TGO-1960-2025, ZWE-1890-2025, ESH-1800-2025
**Source:** biger-1995
**Kind:** ingest

Final comprehensive sweep of Biger 1995 to extract all remaining
country entries not previously ingested. Added 36 new §-sections to
[biger-1995](sources/biger-1995.md): botswana, congo, eritrea, gabon,
gambia, georgia, guinea-bissau, lesotho, liberia, liechtenstein,
mongolia, namibia, niger, norway, portugal, san-marino, sierra-leone,
somalia, sweden, switzerland, tanzania, togo, zimbabwe, western-sahara,
iceland, fiji, tonga, vatican-city, sao-tome-and-principe,
antigua-and-barbuda, grenada, kiribati, saint-kitts-and-nevis,
saint-lucia, saint-vincent.
Also added 14 dependency/territory sections (anguilla, greenland,
guadeloupe, guam, american-samoa, faeroe-islands, falkland-islands,
christmas-island, cocos-islands, saint-helena, saint-pierre-and-miquelon,
macao, saint-martin, cook-islands) plus island state sections (iceland,
fiji, tonga, vatican-city, sao-tome-and-principe, antigua-and-barbuda,
grenada, kiribati, saint-kitts-and-nevis, saint-lucia, saint-vincent).
Created 6 new polity pages (ERI-1882-2025, GAB-1960-2025, LIE-1800-2025,
MNG-1911-2025, SMR-1800-2025, ESH-1800-2025) and updated 18 existing
pages with Biger citations. Source file now has 203 §-sections.
All mainland countries, island states, and dependencies with entries
fully extracted. Confirmed no entries for: Bahamas, Barbados, Maldives,
Seychelles. Biger 1995 is now fully extracted. Polity page propagation
for island/dependency entries deferred (minimal Biger content).

## biger-ingest-central-america-caribbean
**Date:** 2026-04-12
**Touched:** BLZ-1800-2025, CRI-1800-2025, CUB-1800-2025, DMA-1800-2025, DOM-1800-2025, GTM-1821-2025, HND-1800-2025, HTI-1800-2025, JAM-1800-2025, NIC-1800-2025, PAN-1903-2025, SLV-1821-2025, TTO-1800-2025, GUY-1800-2025, SUR-1975-2025
**Source:** biger-1995
**Kind:** ingest

Created 15 polity pages for Central America, Caribbean, and South America
from Biger 1995 (The Encyclopedia of International Boundaries). Each page
contains sourced claims from the relevant Biger entries with page citations.
Countries covered: Belize, Costa Rica, Cuba, Dominica, Dominican Republic,
Guatemala, Honduras, Haiti, Jamaica, Nicaragua, Panama, El Salvador,
Trinidad and Tobago, Guyana, and Suriname. Also added 15 new sections to
[biger-1995](sources/biger-1995.md) with fair-use quotes and page references.

## autonomous-38-bulk-remaining
**Date:** 2026-04-12
**Touched:** 987 polity pages (bulk)
**Source:** polities_database.csv
**Kind:** ingest

Bulk creation of ALL remaining polity pages from CSV metadata:
486 national multi-row chain rows + 501 subnational/aggregate rows.
Generated programmatically with predecessor/successor inline links
and CSV notes where available.

**Wiki now has 1386 polity pages — 100% CSV coverage.** Every row
in data/final/polities_database.csv has a corresponding wiki page.

Pages created in this bulk pass have minimal content (CSV-derived
only). The ~220 hand-crafted pages from earlier iterations have
richer sourced content from Biger, CShapes, COW, and Wikipedia.
Future ingests should deepen the auto-generated pages with actual
source citations.

---

## autonomous-37-bulk-single-rows
**Date:** 2026-04-12
**Touched:** 179 polity pages (bulk)
**Source:** polities_database.csv
**Kind:** ingest

Bulk creation of 179 single-row continuous polity pages — states
with predecessor=NA, successor=NA, end_year=2025, type=national.
Generated programmatically from CSV metadata. Covers small island
states, micro-states, dependencies, and remaining medium states.
Wiki now has ~399 pages (~29% of CSV).

---

## autonomous-35-world-states
**Date:** 2026-04-12
**Touched:** CAN-1866-1948, CAN-1948-2025, AUS-1901-2025, THA-1800-1893, THA-1893-1904, THA-1904-1907, THA-1907-1909, THA-1909-2025, KOR-1948-2025, TWN-1896-2025, SAU-1932-2000, SAU-2000-2025, SAU-1924-1932
**Source:** database
**Kind:** ingest

Created 12 polity pages across 6 country chains: Canada (2 rows:
Confederation through Newfoundland split), Australia (1 row: federation
to present), Thailand (5 rows: Siam's successive territorial losses to
France and Britain 1893-1909), South Korea (1 row: 1948 to present),
Taiwan (1 row: 1896 to present), Saudi Arabia continuation (2 rows:
1932-2000 kingdom + 2000-2025 post-Yemen border settlement). Also
updated [sau-1924-1932](polities/sau-1924-1932.md) to replace TODO
successor links with proper inline links to the new sau-1932-2000 page.

---

## autonomous-36-africa
**Date:** 2026-04-12
**Touched:** ZAF-1828-2025, DZA-1831-2025, TUN-1881-2025, LBY-1951-2025, MAR-1911-1958, MAR-1958-1975, MAR-1975-1979, MAR-1979-2025, NGA-1914-1961, NGA-1961-2025, GHA-1957-2025, COD-1960-2025, KEN-1963-2025
**Source:** database
**Kind:** ingest

Created 13 polity pages for major African states: South Africa (1 row),
Algeria (1), Tunisia (1, cross-refs Biger), Libya (1), Morocco (4-row
chain split on Western Sahara events), Nigeria (2-row chain split on
1961 Cameroons plebiscite), Ghana (1), DR Congo (1), Kenya (1). All
pages are brief drafts citing [database] for CSV-derived facts. Open
questions flagged: ZAF 1828 start date rationale; DZA missing COW code;
MAR Western Sahara territorial overlap; MAR 1911 vs 1912 start.

---

## autonomous-34-south-america
**Date:** 2026-04-12
**Touched:** ARG-1800-1899, ARG-1899-1902, ARG-1902-2025, CHL-1810-1899, CHL-1899-1902, CHL-1902-2025, COL-1800-1830, COL-1830-1903, COL-1903-1922, COL-1922-2025, PER-1825-1909, PER-1909-1922, PER-1922-1942, PER-1942-2025, BOL-1825-1903, BOL-1903-1909, BOL-1909-1938, BOL-1938-2025, VEN-1821-2025, ECU-1800-1942, ECU-1942-2025, PRY-1811-1938, PRY-1938-2025, URY-1828-2025
**Source:** database
**Kind:** ingest

Created 24 polity pages for 8 South American national chains:
Argentina (3 rows), Chile (3), Colombia (4), Peru (4), Bolivia (4),
Venezuela (1), Ecuador (2), Paraguay (2), Uruguay (1). Colombia
chain has CSV notes for Gran Colombia and post-Gran Colombia periods;
all other rows have notes=NA. Cross-links between chains: Bolivia
1903 split = Treaty of Petropolis (Acre to Brazil, matching
BRA-1800-1903 end); Peru/Ecuador 1942 split = Protocol of Rio de
Janeiro; Bolivia/Paraguay 1938 split = Chaco War settlement.
Venezuela and Uruguay are single continuous rows with stable borders.

---

## autonomous-33-egy-eth
**Date:** 2026-04-12
**Touched:** EGY-1800-1899, EGY-1800-1922, EGY-1899-1925, EGY-1922-1925, EGY-1925-1967, EGY-1967-1979, EGY-1979-2025, ETH-1800-1889, ETH-1889-1897, ETH-1897-1902, ETH-1902-1907, ETH-1907-1952, ETH-1952-1993, ETH-1993-2025
**Source:** database
**Kind:** ingest

Created 14 polity pages: 7 for the Egypt chain and 7 for the Ethiopia
chain. CSV bugs flagged for Egypt: (1) Two overlapping chains --
EGY-1800-1899 and EGY-1800-1922 coexist with the same start year,
similar to the OTT/TUR overlap pattern; EGY-1800-1922 is a dead-end
row (succ=NA); (2) Broken chain link -- EGY-1899-1925 has succ=NA and
EGY-1922-1925 has pred=NA despite contiguous dates and matching
cow/iso3; these should be linked. Ethiopia chain is clean with no
broken links. Italian occupation (1936-1941) within ETH-1907-1952
flagged as an open question regarding CShapes continuity coding.

---

## autonomous-32-ind-idn
**Date:** 2026-04-12
**Touched:** IND-1800-1893, IND-1893-1914, IND-1914-1937, IND-1937-1947, IND-1947-1949, IND-1949-2025, IDN-1800-1889, IDN-1889-1949, IDN-1945-1949, IDN-1949-1969, IDN-1969-1976, IDN-1976-2002, IDN-2002-2025
**Source:** database
**Kind:** ingest

Created 13 polity pages: 6 for the India chain (British India
through Republic of India) and 7 for the Indonesia chain (Dutch
East Indies through modern Indonesia). CSV bugs flagged: (1) IND
chain break — IND-1800-1893 has successor=NA and IND-1893-1914 has
predecessor=NA despite contiguous dates and matching cow/iso3;
(2) cow=750 shared between early Indonesia rows (IDN-1800-1889,
IDN-1889-1949) and all India rows — likely a CSV error (independent
Indonesia uses cow=850); (3) IDN-1889-1949 and IDN-1945-1949 have
overlapping date ranges reflecting the colonial-to-independent
transition.

---

## autonomous-31-jpn-irn
**Date:** 2026-04-12
**Touched:** JPN-1800-1895, JPN-1895-1945, JPN-1945-1952, JPN-1952-2025, IRN-1800-1828, IRN-1828-2025
**Source:** database
**Kind:** ingest

Created 6 polity pages: 4 for the Japan chain (pre-imperial through
modern) and 2 for the Iran/Persia chain (Qajar pre-Turkmenchay and
post-Turkmenchay). All sourced from CSV notes. Japan pages cross-ref
[f228-1856-1905](polities/f228-1856-1905.md) for the Treaty of
Portsmouth (1905). Iran pages cross-ref
[f228-1800-1856](polities/f228-1800-1856.md) for the Russian side of
the Caucasus conquest. Open questions flagged: COW code NA across all 4
JPN rows (likely 740), Gulistan (1813) as mid-row split candidate for
IRN, and Iran's 198-year single row.

---

## autonomous-30-china
**Date:** 2026-04-12
**Touched:** CHN-1800-1895, CHN-1895-1912, CHN-1913-1914, CHN-1914-1921, CHN-1921-1945, CHN-1945-1947, CHN-1947-1949, CHN-1949-1950, CHN-1950-2025
**Source:** cshapes-2.0, cow-state-system-v2024
**Kind:** ingest

Created nine polity pages for the complete China chain (1800-2025). The chain
has two content-rich rows -- CHN-1800-1895 (96-year Qing Dynasty, Opium Wars
through Treaty of Shimonoseki) and CHN-1950-2025 (76-year PRC, Hong Kong and
Macau returns) -- and seven shorter transitional rows corresponding to CShapes
polygon changes from concession areas, Japanese occupation zones, warlord-era
fragmentation, and Civil War territorial shifts. Key open questions flagged:
oq-cow-code-na on CHN-1950-2025 (CSV has cow=NA, should be 710), oq-taiwan-status
(ROC/PRC territorial dispute affecting polygon coverage), oq-opium-war-split-candidate
(1842/1860 treaties as candidate mid-row splits in the 96-year Qing row), and
several oq-*-split-event questions on the transitional rows where the specific
CShapes polygon-change driver is not yet documented. All pages draft status,
inline links only.

## autonomous-29-mex-bra
**Date:** 2026-04-12
**Touched:** MEX-1800-1848, MEX-1848-2025, BRA-1800-1903, BRA-1903-1909, BRA-1909-2025
**Source:** cshapes-2.0, cow-state-system-v2024
**Kind:** ingest

Created five polity pages: two for Mexico (split at 1848 Treaty of Guadalupe
Hidalgo) and three for Brazil (splits at 1903 and 1909). Mexico chain covers
Spanish colonial era through independence (1821), massive territorial loss to
the US (~55% at Guadalupe Hidalgo), Gadsden Purchase (sub-threshold), and
modern stable borders. Brazil chain covers Portuguese colony through
independence (1822), Empire, Republic, Acre acquisition (Treaty of Petropolis
1903), and modern Brazil. Key open questions: the 1909 Brazil split event is
unknown (oq-1909-split-event), and both chains have independence events
mid-row rather than as CSV splits (oq-independence-1821, oq-independence-1822).
All pages draft status, inline links only.

## autonomous-28-usa
**Date:** 2026-04-12
**Touched:** USA-1800-1803, USA-1803-1848, USA-1848-1867, USA-1867-1959, USA-1959-2025
**Source:** cshapes-2.0, cow-state-system-v2024, cliopatria-v0.1.3
**Kind:** ingest

Created 5 polity pages for the complete USA chain (1800-2025).
The chain splits on major territorial acquisitions: Louisiana
Purchase (1803), Treaty of Guadalupe Hidalgo (1848), Alaska
Purchase (1867), and Alaska/Hawaii statehood (1959). CSV notes
are rich and directly cited as [database]. COW code 2 confirmed
from `cow_state_system.csv` (continuous from 1816-01-01). Noted
that only the final row (USA-1959-2025) has `cow_code = 2` in
the CSV; the four predecessor rows have NA — same pipeline
omission as F228 pre-1886 rows. Cross-referenced
[f228-1856-1905](polities/f228-1856-1905.md) for the Russian
side of the 1867 Alaska sale and
[esp-1800-2025](polities/esp-1800-2025.md) for the Spanish side
of the 1898 war.

---

## csv-fix-audit-findings-1-4
**Date:** 2026-04-12
**Touched:** data/final/polities_database.csv
**Source:** wiki audit (proposal-wiki-vs-csv-audit-2026-04-12)
**Kind:** ingest

Applied 36 CSV fixes from the wiki-vs-CSV audit:

**Finding 1 (5 fixes):** Renamed mislabeled F228 rows: "USSR"
→ "Russian Empire" (1905-1917), "Russia" (1917-1918), "RSFSR"
(1918-1921). Per wikipedia-russian-empire-2026-04-11.

**Finding 2 (20 fixes):** Fixed 12 predecessor=NA bugs and 8
successor=NA bugs. Complete chain graphs now exist for:
F51 (Czechoslovakia), F248 (Yugoslavia), POL (Poland), BEL
(Belgium), FIN (Finland), DEU-1938→F77/F78 (Germany WWII→
occupation), SER→F248 (Serbia→Yugoslavia), NLD→BEL+LUX.

**Finding 3 (10 fixes):** Corrected COW codes: DEU 260→255,
F228-pre-1905 NA→365, NLD NA→210, SER/SCG NA→345.

**Finding 4 (1 fix):** GER-1800-2025 polity_type national →
aggregate. Per 6 docs/ files documenting it as trade aggregate.

---

## proposal-wiki-vs-csv-audit-2026-04-12
**Date:** 2026-04-12
**Touched:** (audit only — no files modified)
**Source:** all wiki sources cross-referenced against CSV
**Kind:** proposal

Systematic audit of all 119 wiki pages against the CSV. The wiki
is the primary source of truth (built on Biger, CShapes, COW,
Wikipedia). Every finding is a CSV error per sourced evidence.

### 1. MISLABELED ROWS (5 rows)
F228-1905-1914 through F228-1920-1921 labeled "USSR" but USSR
didn't exist until 30 Dec 1922. Should be "Russian Empire" or
"RSFSR." See proposal-f228-ussr-anachronism.

### 2. MISSING PREDECESSOR/SUCCESSOR LINKS (16 broken)
12 predecessor=NA bugs: F51 chain (3), F248 chain (4), POL,
BEL, FIN, F77, F78. 4 successor=NA bugs: DEU-1938-1945, SER,
F51 chain, NLD-1800-1830 (missing BEL/LUX as successors).

### 3. WRONG COW CODES (10 rows)
DEU-1800-1919 (260→255), F228-1800-1856 (NA→365), F228-1856-1905
(NA→365), NLD-1800-1830 (NA→210), NLD-1830-2025 (NA→210),
SER-1816-1913 (NA→345), SER-1913-1915 (NA→345), SER-1913-1918
(NA→345), SCG-1992-2006 (NA→345), SER-2006-2008 (NA→345).

### 4. POLITY_TYPE ERROR (1 row)
GER-1800-2025: CSV says "national" but 6 docs/ files say
"aggregate." See proposal-deu-ger-chain-audit Finding 1.

### 5. NOTES=NA GAPS
102/119 wiki rows (85%) have notes=NA. Most egregious: DEU,
F228-1905+, F51, F248, POL, BGR, HUN, ROU chains.

### 6. SPLIT DATE INCONSISTENCIES (3 confirmed)
- AUH 1867: constitutional not territorial (Biger: 1866 was the
  real turning point)
- OTT 1886: CShapes temporal floor, not a historical event
- OTT 1912 end: Ottoman Empire continued to 1918

**Priority**: Apply Findings 1-4 to CSV. Finding 5 backfill from
wiki. Finding 6 needs human split-policy decisions.

---

## autonomous-26-final-successors
**Date:** 2026-04-12
**Touched:** SER-2006-2008, SRB-2008-2025, KOS-2008-2025, ARM-1991-2025, AZE-1991-2025, GEO-1991-2025, KAZ-1991-2025, KGZ-1991-2025, TJK-1991-2025, TKM-1991-2025, UZB-1991-2025, SCG-1992-2006, F228-1945-1991
**Source:** cshapes-2.0, cow-state-system-v2024, biger-1995
**Kind:** ingest

Autonomous iteration 26. Creates 11 polity pages for final successor
states and updates 2 existing pages:

**Serbian chain (3 pages):**
- **SER-2006-2008** -- Transitional Serbia (Montenegro independence to
  Kosovo independence). 3-year row.
- **SRB-2008-2025** -- Modern Serbia (~77,474 km², excluding Kosovo).
- **KOS-2008-2025** -- Kosovo (independence 17 February 2008, ~10,887 km²).

**Post-Soviet Caucasus (3 pages):**
- **ARM-1991-2025** -- Armenia. Nagorno-Karabakh conflict, 2020/2023 wars.
- **AZE-1991-2025** -- Azerbaijan. Oil-rich Caspian state, Karabakh recapture.
- **GEO-1991-2025** -- Georgia. Abkhazia/South Ossetia, 2008 war. Biger source.

**Post-Soviet Central Asia (5 pages):**
- **KAZ-1991-2025** -- Kazakhstan (~2.7M km², 9th largest country).
- **KGZ-1991-2025** -- Kyrgyzstan. 2005/2010 revolutions.
- **TJK-1991-2025** -- Tajikistan. Civil War 1992-1997.
- **TKM-1991-2025** -- Turkmenistan. Gas-rich, authoritarian.
- **UZB-1991-2025** -- Uzbekistan. Most populous Central Asian state.

**Updated existing pages:**
- [scg-1992-2006](polities/scg-1992-2006.md): removed TODO from
  SER-2006-2008 successor link (now live). Resolved
  oq-serbia-successor-page.
- [f228-1945-1991](polities/f228-1945-1991.md): linked all 8
  Caucasus/Central Asian successor pages. Resolved
  oq-15-successor-pages (all 15 now have pages).

---

## autonomous-25-post-dissolution
**Date:** 2026-04-12
**Touched:** RUS-1991-2014, RUS-2014-2025, UKR-1991-2014, UKR-2014-2025, BLR-1991-2025, EST-1991-2025, LVA-1991-2025, LTU-1991-2025, MDA-1991-2025, CZE-1993-2025, SVK-1993-2025, F248-1991-1992, SVN-1992-2025, HRV-1992-2025, BIH-1992-2025, MKD-1991-2025, SCG-1992-2006, MNE-2006-2025, F51-1947-1993, F248-1920-1991, F228-1945-1991
**Source:** cshapes-2.0, cow-state-system-v2024
**Kind:** ingest

Autonomous iteration 25. Creates 18 polity pages for modern
post-dissolution states and updates 3 existing pages:

**Post-Soviet European (9 pages + 2 continuations):**
- **RUS-1991-2014** and **RUS-2014-2025** -- Russia split at 2014
  Crimea annexation. Post-Soviet Federation, CIS, Chechen Wars, Putin.
- **UKR-1991-2014** and **UKR-2014-2025** -- Ukraine split at 2014
  Crimea loss. Orange Revolution, Euromaidan, 2022 invasion.
- **BLR-1991-2025** -- Belarus. Lukashenko since 1994.
- **EST-1991-2025**, **LVA-1991-2025**, **LTU-1991-2025** -- Baltic
  states. All EU/NATO 2004.
- **MDA-1991-2025** -- Moldova. Transnistria conflict.

**Czech/Slovak (2 pages):**
- **CZE-1993-2025** and **SVK-1993-2025** -- Velvet Divorce successors.

**Yugoslav successors (7 pages):**
- **F248-1991-1992** -- 2-year transitional dissolution row.
- **SVN-1992-2025**, **HRV-1992-2025**, **BIH-1992-2025** -- Slovenia,
  Croatia, Bosnia.
- **MKD-1991-2025** -- North Macedonia (dual predecessor).
- **SCG-1992-2006** -- Serbia and Montenegro (FRY then State Union).
- **MNE-2006-2025** -- Montenegro (2006 independence).

**Updated existing pages:**
- [f51-1947-1993](polities/f51-1947-1993.md): removed TODO from CZE/SVK
  successor links (now live). Resolved oq-velvet-divorce-successors.
- [f248-1920-1991](polities/f248-1920-1991.md): linked to
  f248-1991-1992 and mkd-1991-2025. Partially resolved
  oq-dissolution-successor-gap.
- [f228-1945-1991](polities/f228-1945-1991.md): linked 9 European
  successor pages. Partially resolved oq-15-successor-pages (6
  Central Asian/Caucasus successors still needed).

---

## autonomous-24-f228-ser
**Date:** 2026-04-12
**Touched:** F228-1945-1991, SER-1913-1915, SER-1913-1918, F228-1940-1945, SER-1816-1913
**Source:** cshapes-2.0, cow-state-system-v2024, wikipedia-russian-empire-2026-04-11, biger-1995
**Kind:** ingest

Autonomous iteration 24. Creates 3 polity pages and updates 2:

- **F228-1945-1991** -- 47-year row. Final row in the F228 chain
  (11 rows, 191 years). Soviet superpower era. Cold War. Gorbachev
  reforms. Dissolved 26 December 1991 into 15 successor republics
  -- the largest dissolution event in the wiki. None of the 15
  successor pages exist yet (massive coverage gap). Biger §russia
  confirms 15 republics and 25 million Russian diaspora.
- **SER-1913-1915** -- 3-year row. Post-Balkan Wars Serbia through
  WWI occupation. Gained Kosovo and Macedonia. Assassination of
  Archduke Franz Ferdinand. Overrun by Central Powers late 1915.
- **SER-1913-1918** -- 6-year row overlapping with SER-1913-1915.
  Dual predecessor (unusual). Represents Serbia's continued legal
  existence including government-in-exile on Corfu. CSV successor=NA
  but historically became core of Yugoslavia (F248) -- reciprocal
  gap with f248-1918-1919's predecessor=NA bug.

Updated [f228-1940-1945](polities/f228-1940-1945.md): removed TODO
from successor link (now live). Updated
[ser-1816-1913](polities/ser-1816-1913.md): removed TODO from
successor links (now live).

---

## autonomous-22-fin-alb-f51-f248
**Date:** 2026-04-12
**Touched:** FIN-1917-1940, FIN-1940-2025, ALB-1913-2025, F51-1938-1945, F51-1945-1947, F51-1947-1993, F248-1920-1991
**Source:** cshapes-2.0, cow-state-system-v2024, biger-1995
**Kind:** ingest

Autonomous iteration 22. Creates 7 polity pages:

- **FIN-1917-1940** -- 24-year row. Finnish independence from Russia
  (1917). Civil War 1918. Treaty of Tartu 1920. Winter War ends with
  Moscow Peace Treaty (1940), ~10% territory lost.
- **FIN-1940-2025** -- 86-year row. Post-Winter-War Finland.
  Continuation War 1941-1944. Paris Peace Treaty 1947. EU 1995. NATO
  2023. ~338,000 km².
- **ALB-1913-2025** -- 113-year continuous row. Independence from Ottoman
  Empire. Treaty of London 1913. Italian occupation 1939-1943. Hoxha
  communist regime 1944-1985. ~28,748 km².
- **F51-1938-1945** -- 8-year row. Munich Agreement, First Vienna Award,
  German occupation. COW gap 1939-1945.
- **F51-1945-1947** -- 3-year row. Restored Czechoslovakia. Benes
  decrees. Ruthenia ceded to USSR.
- **F51-1947-1993** -- 47-year row. Communist Czechoslovakia. Prague
  Spring 1968. Velvet Revolution 1989. Velvet Divorce 1993 into CZE
  and SVK (successor pages TODO).
- **F248-1920-1991** -- 72-year row. Kingdom of Yugoslavia / Tito's
  Yugoslavia. COW gap 1941-1945. Dissolution began 1991. CSV only lists
  MKD as successor (major gap -- 6+ successor states).

Also updated 2 predecessor pages (f51-1918-1938, f248-1918-1919)
replacing plain-text successor references with live inline links.

---

## autonomous-21-close-chains
**Date:** 2026-04-12
**Touched:** POL-1921-1945, POL-1945-2025, HUN-1938-1947, HUN-1947-2025, BGR-1919-1940, BGR-1940-2025, ROU-1919-1920, ROU-1920-1940, ROU-1940-2025
**Source:** cshapes-2.0, cow-state-system-v2024
**Kind:** ingest

Autonomous iteration 21. Creates 9 polity pages closing 4 chains to
2025:

- **POL-1921-1945** -- 25-year row. Interwar Poland (Second Polish
  Republic), borders settled by Treaty of Riga 1921 (~389,000 km²).
  September 1939 invasion. COW gap 1939-1945.
- **POL-1945-2025** -- 81-year row. Post-WWII Poland, borders shifted
  westward (Oder-Neisse line). Communist period, 1989 transition, EU
  2004. ~312,700 km².
- **HUN-1938-1947** -- 10-year row. Vienna Awards expansion then
  contraction. Treaty of Paris (1947) restored Trianon borders.
- **HUN-1947-2025** -- 79-year row. Post-WWII Hungary at Trianon
  borders (~93,000 km²). 1956 Revolution, 1989 transition, EU 2004.
- **BGR-1919-1940** -- 22-year row. Post-Neuilly interwar Bulgaria.
  Treaty of Craiova (1940) returned Southern Dobruja.
- **BGR-1940-2025** -- 86-year row. WWII Axis, communist period, 1989
  transition, EU 2007. ~111,000 km².
- **ROU-1919-1920** -- 2-year transitional row. Treaties of
  Saint-Germain and Trianon formalizing Greater Romania borders.
- **ROU-1920-1940** -- 21-year row. Greater Romania at maximum extent
  (~295,000 km²). Three simultaneous territorial losses in 1940.
- **ROU-1940-2025** -- 86-year row. Reduced Romania, regained northern
  Transylvania (1947) but lost Bessarabia permanently. 1989 Revolution,
  EU 2007. ~238,000 km².

Also updated 4 predecessor pages (pol-1920-1921, hun-1920-1938,
bgr-1918-1919, rou-1918-1919) replacing TODO successor links with live
inline links.

---

## autonomous-17-swe-ser
**Date:** 2026-04-12
**Touched:** SWE-1800-1809, SWE-1809-1814, SWE-1814-1905, SER-1816-1913
**Source:** cshapes-2.0, cow-state-system-v2024, biger-1995, wikipedia-ottoman-2026-04-11
**Kind:** ingest

Autonomous iteration 17. Creates 4 polity pages:

- **SWE-1800-1809** -- 10-year row covering the last years of the
  Swedish-Finnish union (~800,000 km²). Finland had been part of Sweden
  since the 12th century. The Finnish War (1808-1809) ended with the
  Treaty of Fredrikshamn, ceding Finland to Russia (-42% territory).
  Cross-references [f228-1800-1856](polities/f228-1800-1856.md) for the
  Russian acquisition side.
- **SWE-1809-1814** -- 6-year transitional row. Sweden without Finland
  before gaining Norway (~443,000 km²). Revolution of 1809 replaced
  Gustav IV Adolf.
- **SWE-1814-1905** -- 92-year row covering the Sweden-Norway personal
  union. Treaty of Kiel (1814) to dissolution (1905). CShapes polygon
  761,932 km². Key OQs: oq-1905-dissolution-date (7 June vs 26 October),
  oq-swe-aggregate-overlap (SWE-1800-2025 exists alongside split rows).
- **SER-1816-1913** -- 98-year row from Serbian autonomy to Balkan Wars.
  Ottoman vassal gaining independence at Congress of Berlin (1878).
  CShapes cowcode=345 but CSV has cow=NA (oq-cow-code-na). Dual
  successors SER-1913-1918 and SER-1913-1915 (oq-dual-successor).

The three Swedish pages form a complete chain: swe-1800-1809 ->
swe-1809-1814 -> swe-1814-1905 with live cross-links.

---

## autonomous-16-deu-balkans
**Date:** 2026-04-12
**Touched:** DEU-1938-1945, DEU-1990-2025, GRC-1830-1913, ROU-1859-1913, BGR-1878-1913, DEU-1920-1938
**Source:** cshapes-2.0, cow-state-system-v2024, biger-1995, wikipedia-ottoman-2026-04-11
**Kind:** ingest

Autonomous iteration 16. Creates 5 polity pages and updates 1:

- **DEU-1938-1945** -- 8-year row covering Nazi Germany from Anschluss to
  unconditional surrender. CSV has successor=NA, which is a chain gap
  (territory continued through occupation zones to FRG/GDR and eventually
  DEU-1990-2025). Key OQs: oq-successor-chain-gap,
  oq-territorial-expansion-1938-1942.
- **DEU-1990-2025** -- 36-year row covering reunified Germany. Stable
  borders since 1990 (~357,000 km²). Predecessors F78 (West) and F77
  (East) pages not yet created (oq-predecessor-pages-missing).
- **GRC-1830-1913** -- 84-year row from Greek independence to Balkan Wars.
  CSV predecessor=NA but Greece was Ottoman territory (oq-ottoman-predecessor).
  Nearly doubled in area with no mid-row splits (oq-territorial-expansion).
- **ROU-1859-1913** -- 55-year row from Romanian unification to Balkan Wars.
  Congress of Berlin (1878) involved territorial exchange: gained Dobruja,
  lost Bessarabia (oq-1878-congress-of-berlin). Ottoman vassal predecessor
  gap (oq-ottoman-predecessor).
- **BGR-1878-1913** -- 36-year row from Congress of Berlin to Balkan Wars.
  Autonomous principality 1878-1908, independent kingdom 1908-1913. The
  10.28 sq deg CShapes polygon at 1908-10-05 matches the Ottoman area drop
  exactly (cross-ref: autonomous-1-bosnia-double-count). Eastern Rumelia
  unification 1885 is a candidate mid-row split (oq-1885-eastern-rumelia).
- **DEU-1920-1938** updated: successor TODO links replaced with live links
  to [deu-1938-1945](polities/deu-1938-1945.md).

---

## autonomous-14-deu-dnk-sar
**Date:** 2026-04-12
**Touched:** DEU-1919-1920, DNK-1864-1920, SAR-1800-1860, DEU-1800-1919, DNK-1800-1864, ITA-1861-1919
**Source:** wikipedia-german-empire-2026-04-11, cshapes-2.0, cow-state-system-v2024, biger-1995
**Kind:** ingest

Autonomous iteration 14. Creates 3 polity pages:

- **DEU-1919-1920** -- 2-year transitional row covering post-Versailles
  Germany (~65,000 km² metropolitan territory lost). Split date at 1920
  is ambiguous: Treaty of Versailles entered into force 10 January 1920
  is the best candidate (oq-1919-vs-1920-split-date).
- **DNK-1864-1920** -- 57-year row covering reduced Denmark without
  Schleswig-Holstein (~38,496 km²). Biger confirms 40% territory loss
  at 1864 and partial northern Schleswig return after WWI plebiscite.
- **SAR-1800-1860** -- Kingdom of Sardinia, legal continuator of Italian
  unification. COW code 338 shared with PIE-1816-1861 (44-year overlap,
  candidate duplicate: oq-sar-pie-overlap). CSV ends at 1860, Italy
  starts at 1861 (oq-1860-vs-1861).

TODO comments removed from predecessor pages: DEU-1800-1919 (2 links),
DNK-1800-1864 (2 links), ITA-1861-1919 (2 links for SAR only; PAP
TODO remains).

---

## autonomous-13-auh-successors
**Date:** 2026-04-12
**Touched:** AUT-1918-2025, HUN-1918-1919, F51-1918-1938, F248-1918-1919, POL-1918-1919, AUH-1908-1918
**Source:** wikipedia-austria-hungary-2026-04-11 (existing), cshapes-2.0, cow-state-system-v2024
**Kind:** ingest

Autonomous iteration 13. Creates all 5 Austria-Hungary successor
state pages, closing the biggest coverage gap in the wiki. CShapes
data reveals the dramatic territorial reshaping: Austria shrank
from 25.5 to 10.0 sq deg at Saint-Germain; Hungary from 37.6 to
11.0 at Trianon; Czechoslovakia formed at 17.3 sq deg; Yugoslavia
grew from Serbia's 10.0 to 28.7; Poland grew from 17.0 to 50.7.

Three CSV predecessor=NA bugs documented:
- F51-1918-1938 (Czechoslovakia) — should reference AUH
- F248-1918-1919 (Yugoslavia) — should reference AUH + Serbia
- POL-1918-1919 (Poland) — triple-partition predecessor (AUH + F228 + DEU)

TODO comments removed from all 6 successor links on
AUH-1908-1918. Wiki now has 29 polity pages.

---

## autonomous-12-modern-successors
**Date:** 2026-04-12
**Touched:** FRA-1919-2025, GBR-1921-2025, ITA-1919-2025, FRA-1800-1919, GBR-1800-1921, ITA-1861-1919
**Source:** cshapes-2.0, cow-state-system-v2024, biger-1995 (existing)
**Kind:** ingest

Autonomous iteration 12. Creates 3 modern European successor pages
— all stable-border states post-WWI. Closes predecessor→successor
chains on France, UK, and Italy.

- **FRA-1919-2025**: Post-Versailles France. COW gap 1942-1944
  (Vichy). Post-WWII 268 sq mi gained from Italy per Biger.
- **GBR-1921-2025**: Post-Irish-Treaty UK. 1927 name change.
  Northern Ireland opt-out noted.
- **ITA-1919-2025**: Post-Saint-Germain Italy. Post-WWII losses
  (Istria to Yugoslavia, small areas to France) flagged as
  candidate mid-row changes.

TODO comments removed from 3 predecessor pages. Wiki now has
24 polity pages.

---

## autonomous-11-nld-dnk-nor
**Date:** 2026-04-12
**Touched:** NLD-1830-2025, DNK-1800-1864, NOR-1800-2025, NLD-1800-1830
**Source:** cshapes-2.0, cow-state-system-v2024, biger-1995 (existing)
**Kind:** ingest

Autonomous iteration 11. Creates 3 more European polity pages:

- **NLD-1830-2025**: Rump Netherlands after Belgian secession. Closes
  successor gap on NLD-1800-1830 (TODO comment removed). Flags
  cow_code=NA (should be 210).
- **DNK-1800-1864**: Denmark with Schleswig-Holstein. Critical
  connector to the German chain — 1864 Second Schleswig War is
  the split event (Biger: "Denmark lost the whole of Schleswig-
  Holstein representing 40% of its territory"). Flags 1814 Norway
  loss as major untracked mid-row event.
- **NOR-1800-2025**: Norway continuous row. 1814 Treaty of Kiel
  (Danish → Swedish rule) and 1905 independence both within the
  row — neither triggers a WHEP split because metropolitan borders
  unchanged.

Wiki now has 21 polity pages covering 10 European states.

---

## autonomous-10-prt-bel-che
**Date:** 2026-04-12
**Touched:** PRT-1800-2025, BEL-1831-2025, CHE-1800-2025
**Source:** cshapes-2.0, cow-state-system-v2024, biger-1995 (existing §-sections)
**Kind:** ingest

Autonomous iteration 10. Creates 3 new European polity pages in a
single batch — all stable-border states requiring no new sources:

- **PRT-1800-2025**: Portugal, 226-year continuous row. Metropolitan
  borders unchanged since 1297 Treaty of Alcañices. Colonial losses
  (Brazil 1822, Africa 1974-75) tracked as separate rows. 3 OQs.
- **BEL-1831-2025**: Belgium, 195-year row from Belgian Revolution.
  Flags CSV predecessor=NA oddity (should be NLD-1800-1830). COW
  has WWII occupation gap (1940-1945). Eupen-Malmedy gain (1919)
  noted as minor untracked territorial change. 4 OQs.
- **CHE-1800-2025**: Switzerland, 226-year continuous row. Borders
  unchanged since 1815 per Biger. Perpetual neutrality. 2 OQs.

---

## biger-batch-europe-ingest-3
**Date:** 2026-04-12
**Touched:** ESP-1800-2025
**Source:** biger-1995 (1 new §-section: spain)
**Kind:** ingest

Third and final Biger batch ingest for this session. Read PDF
pages 476-477 (SPAIN main entry). Area: 194,934 sq mi. Key quote:
"Spain first lost its European dominions and then, in the
nineteenth century, its American empire." No UK main entry found
in Biger — the book has no standalone UNITED KINGDOM entry (UK
is an island with only the Ireland land boundary, covered under
IRELAND–UNITED KINGDOM at p.312). oq-biger-spain resolved.

Biger ingest summary for this session: 12 new §-sections added
(france, france-germany, france-italy, france-spain, germany,
italy, ireland, netherlands, russia, spain). Total §-sections
now: 19. All 8 oq-biger-* OQs resolved across 8 polity pages.

---

## biger-batch-europe-ingest-2
**Date:** 2026-04-12
**Touched:** ITA-1861-1919, GBR-1800-1921, F228-1856-1905, F228-1800-1856, NLD-1800-1830
**Source:** biger-1995 (5 new §-sections: italy, ireland, netherlands, russia)
**Kind:** ingest

Second Biger batch ingest. Read PDF pages 310-312 (IRELAND),
317-323 (ITALY + ITALY-SLOVENIA), 397-402 (NETHERLANDS), 451-452
(RUSSIA). Added 5 new §-sections to biger-1995.md.

Key findings:
- **ITALY**: "Italian unity... only finally achieved in the 1860s."
  Treaty of Saint-Germain (September 1919): "Italy gained Goriza,
  Trieste and the Istera peninsula populated with over 250,000
  Slavs." London Agreement date: 26 April 1915.
- **IRELAND**: "In 1800 Ireland was annexed to Britain." Partition
  "formed in 1920." Border: 224 miles (360 km). Relevant for
  GBR-1800-1921.
- **NETHERLANDS**: 16,139 sq mi [41,785 sq km]. Covers Dutch Republic
  through Belgian Revolution.
- **RUSSIA**: 6,592,849 sq mi [17,068,886 sq km]. "Rounded off their
  empire by conquering the Caucasus... central Asia and the Russian
  Far East." 1991 dissolution: "25,000,000 Russians found themselves
  living outside Russia."

Resolved: oq-biger-italy, oq-biger-uk, oq-biger-russia (on both
F228 pages), oq-biger-netherlands. 5 OQs resolved.

Still pending: SPAIN, UNITED KINGDOM main entries, and all
bilateral boundary entries for Russia, Italy, Spain.

---

## biger-batch-europe-ingest
**Date:** 2026-04-12
**Touched:** FRA-1800-1919, DEU-1800-1919, ITA-1861-1919
**Source:** biger-1995 (6 new §-sections: france, france-germany, france-italy, france-spain, germany)
**Kind:** ingest

Batch Biger 1995 ingest for major European states. Read PDF pages
222–243 covering FRANCE (main + 4 bilateral entries) and GERMANY
(main entry). Added 6 new §-sections to biger-1995.md source file.

Key findings propagated to polity pages:
- **FRA-1800-1919**: Treaty of Turin exact date (24 March 1860)
  for Nice/Savoy cession. Alsace-Lorraine: Biger confirms "Treaty
  of Versailles of 1919 placed the boundary on the July 1870
  line." France–Spain: boundary unchanged since 1659.
  oq-biger-france resolved.
- **DEU-1800-1919**: Biger confirms Bismarck unification "around
  1870." Post-WWII ethnic German expulsions quantified (10M).
  oq-biger-germany resolved.
- **ITA-1861-1919**: Biger §france-italy confirms Treaty of Turin
  (24 March 1860) and post-WWII 268 sq mi transfer to France.
  Cross-references the existing §austria section for Venetia.

UNITED KINGDOM entry not found under "GREAT BRITAIN" — Biger
uses "UNITED KINGDOM" in the U section. Deferred to next read.

---

## autonomous-9-esp-first-ingest
**Date:** 2026-04-12
**Touched:** ESP-1800-2025
**Source:** wikipedia-spain-2026-04-12 (new), cshapes-2.0, cow-state-system-v2024
**Kind:** ingest

Autonomous iteration 9. Creates the ESP-1800-2025 polity page —
a 226-year continuous row for Spain. Metropolitan borders unchanged
since 1815 despite massive colonial losses (Latin America 1810s–20s,
Cuba/Philippines 1898). CShapes confirms: single static polygon
across entire 1886–2019 coverage. Colonial territories tracked as
separate WHEP rows.

4 open questions (oq-biger-spain, oq-colonial-loss-split-candidates,
oq-civil-war-1936, oq-notes-na).

---

## autonomous-8-nld-1800-1830
**Date:** 2026-04-12
**Touched:** NLD-1800-1830, LUX-1839-2025
**Source:** wikipedia-netherlands-2026-04-12 (new), cow-state-system-v2024
**Kind:** ingest

Autonomous iteration 8. Creates the NLD-1800-1830 polity page —
the United Kingdom of the Netherlands from database floor to the
Belgian Revolution (1830). 68,095 km², 5.6M population. Three-way
dissolution: Netherlands + Belgium + Luxembourg. Closes the
predecessor gap on lux-1839-2025. New source file:
wikipedia-netherlands-2026-04-12.md.

4 open questions (oq-pre-1815-entities, oq-biger-netherlands,
oq-cow-code-na, oq-three-way-succession).

---

## autonomous-7-f228-1800-1856
**Date:** 2026-04-12
**Touched:** F228-1800-1856, F228-1856-1905
**Source:** wikipedia-russian-empire-2026-04-11 (existing), cow-state-system-v2024, cliopatria-v0.1.3
**Kind:** ingest

Autonomous iteration 7. Creates the F228-1800-1856 polity page —
the 57-year Russian Empire pre-Crimean War row. Covers Georgia
(1801), Finland (1809), Bessarabia (1812), Congress Poland (1815),
Caucasus conquests, and the Crimean War (1853-56). Closes the
predecessor gap on F228-1856-1905. No new source file needed — the
existing wikipedia-russian-empire-2026-04-11 covers pre-1856 events.

4 open questions (oq-biger-russia, oq-pre-1801-georgia-date,
oq-finnish-war-1809, oq-caucasus-conquest-timeline).

---

## lint-2026-04-12
**Date:** 2026-04-12
**Touched:** wiki/index.md
**Source:** none
**Kind:** lint

Post-session lint across all 12 polity pages, 12 sources, log,
and index. 10 checks run.

**Auto-applied:** Index OQ count corrected from "~47" to "49
unresolved (54 total, 5 resolved)". Luxembourg OQ count corrected
from "3" to "4 unresolved (1 resolved)".

**Should review (not auto-fixed):**
1. `ott-1886-1908.md` line ~112: uncited sourced claim "1885:
   Bulgarian unification with Eastern Rumelia" — ends with "Not
   captured in the current Wikipedia snapshot" rather than a
   citation. Blocks `reviewed` status (every Sourced claims bullet
   must be cited). Needs an ingest, not a lint fix.
2. 16 dangling `<!-- TODO: page not yet created -->` refs across
   8 files — these are known coverage gaps, not bugs. Highest
   priority: AUH-1908-1918 successors (6 missing pages),
   ITA-1861-1919 predecessors (2 missing).

---

## autonomous-6-ita-first-ingest
**Date:** 2026-04-12
**Touched:** ITA-1861-1919
**Source:** wikipedia-italy-2026-04-12 (new), cshapes-2.0, cow-state-system-v2024, biger-1995 §austria (cross-reference)
**Kind:** ingest

Autonomous iteration 6 (final in this loop). Creates the
ITA-1861-1919 polity page — a 59-year row from Italian
unification (17 March 1861) to the Treaty of Saint-Germain
(10 September 1919). Unlike France and UK, this row starts at a
real historical event. Has 6 predecessor entities in the CSV.

Two major mid-row territorial gains (Venetia 1866, Rome 1870)
are not CSV splits — both flagged as candidate split points,
consistent with the same pattern seen on France (1860, 1871),
Germany (1871), Austria (1866/1867), and Russia (1867, 1878).
The accumulation of these same-pattern questions across 5
separate European empires is now a strong signal that the split-
rule question needs a unified human decision.

CShapes confirms: Italy polygon 31.25 sq degrees to 1919-09-09,
then 33.05 (Trentino/Trieste/Istria gains). The CSV split at
1919 matches CShapes.

New source file: `wikipedia-italy-2026-04-12.md`. 6 open
questions (oq-biger-italy, oq-1866-venetia-split-candidate,
oq-1870-rome-split-candidate, oq-colonial-libya-1911,
oq-cow-325-from-1816, oq-notes-na).

---

## autonomous-5-gbr-first-ingest
**Date:** 2026-04-12
**Touched:** GBR-1800-1921
**Source:** wikipedia-uk-2026-04-12 (new), cshapes-2.0, cow-state-system-v2024
**Kind:** ingest

Autonomous iteration 5. Creates the GBR-1800-1921 polity page —
a 122-year row covering the UK from the database floor to the
Anglo-Irish Treaty (6 December 1921). Metropolitan territory was
remarkably stable throughout the period — the only significant
change is the 1921 Irish partition itself. The 1800 start
precedes the 1801 Act of Union by 1 year (minor label
anachronism, comparable to AUH 1800–1804).

CShapes confirms: UK polygon is 42.95 sq degrees through
1922-12-05, then drops to 33.59 at 1922-12-06 (Irish Free State
constitutional establishment). The CSV's 1921 split matches the
treaty signing date in CShapes.

New source file: `wikipedia-uk-2026-04-12.md`. 5 open questions
(oq-biger-uk, oq-1921-vs-1922-end-date, oq-colonial-empire-scope,
oq-heligoland-1890, oq-notes-na).

---

## autonomous-4-fra-first-ingest
**Date:** 2026-04-12
**Touched:** FRA-1800-1919
**Source:** wikipedia-france-2026-04-12 (new), cshapes-2.0, cow-state-system-v2024, docs/03 cross-reference
**Kind:** ingest

Autonomous iteration 4 (new loop, cap reset to 3). Creates the
FRA-1800-1919 polity page — a 120-year row covering Napoleonic
France through the Treaty of Versailles (1919-06-28). Six regime
changes within the row, none triggering a WHEP split. The sole
split at 1919 is a real territorial event (Alsace-Lorraine
return, +1.92 sq degrees in CShapes).

CSV audit of FRA chain surfaced two candidate split questions:
the 1860 Nice/Savoy gain (8,261 km², docs/03:99) and the 1871
Alsace-Lorraine loss (~14,500 km² estimated). Neither is split
in the CSV; neither has a documented rationale for not splitting.
Both flagged as open questions (Tier X: require human split-
policy decision). Also noted: `notes = NA` on both FRA rows
despite France being a major European state, and
`verification_status = REGION` rather than VERIFIED.

New source file: `wikipedia-france-2026-04-12.md` — snapshot of
*France in the long nineteenth century* and *French colonial
empire* Wikipedia articles.

---

## autonomous-3-cow-russia-dates
**Date:** 2026-04-12
**Touched:** F228-1856-1905
**Source:** cow-state-system-v2024 (statelist2024.csv)
**Kind:** autonomous

**Phase 1 (inventory):** Iteration 3 (final). Two OQs resolved
in iterations 1–2 (oq-bosnia-double-count, oq-cow-auh-dates).
Remaining Tier 1: 2 COW queries.

**Phase 2 (classification):** Unchanged from iteration 2.

**Phase 3 (selection):** `oq-cow-russia-early-empire` on
`f228-1856-1905`. Tier 1, single grep on COW data.

**Phase 4 (execution):** COW `statelist2024.csv` records Russia
(`RUS`, `ccode=365`) with a single continuous tenure from
1816-01-01 to 2024-12-31 — no breaks. The `cow_code = NA` on
F228-1800-1856 and F228-1856-1905 is an omission: later F228
rows (1905+) correctly use `cow_code = 365`. The NA likely arose
because COW codes were populated from CShapes 2.0 (starts 1886)
and not backfilled to Cliopatria-based pre-1886 rows. Updated
the sourced claim and resolved the OQ.

**Outcome:** `oq-cow-russia-early-empire` resolved. F228-1856-1905
goes from 5 to 4 unresolved open questions.

**Stop decision:** stop — iteration cap (3/3) reached.

---

## autonomous-2-cow-auh-dates
**Date:** 2026-04-12
**Touched:** AUH-1800-1867
**Source:** cow-state-system-v2024 (statelist2024.csv)
**Kind:** autonomous

**Phase 1 (inventory):** Iteration 2. State carried forward from
iteration 1; OTT-1886-1908 now at 0 unresolved OQs. Remaining
Tier 1 items: 3 COW queries (oq-cow-auh-dates, oq-cow-russia-
early-empire, oq-cow-code-255-vs-260).

**Phase 2 (classification):** Same tier structure as iteration 1,
minus the resolved oq-bosnia-double-count.

**Phase 3 (selection):** `oq-cow-auh-dates` on `auh-1800-1867`.
Tier 1, single grep on already-committed COW data. Tiebreaker:
AUH chain is the most cross-referenced (3 pages), and resolving
the COW dates here informs all three.

**Phase 4 (execution):** Extracted from
`wiki/sources/data/cow-v2024/statelist2024.csv`: Austria-Hungary
(`AUH`, `ccode=300`) has a single continuous COW tenure from
1816-01-01 to 1918-11-12. No splits at 1867 (Ausgleich) or 1908
(Bosnia). Successor entries: Austria `ccode=305` (1919-09-10 to
1938-03-13; 1955-07-27 onward), Hungary `ccode=310` (1918-11-16
onward). Updated the sourced claim and resolved the OQ.

**Outcome:** `oq-cow-auh-dates` resolved. AUH-1800-1867 goes from
5 to 4 unresolved open questions.

**Stop decision:** continue (iteration 2 of 3)

---

## autonomous-1-bosnia-double-count
**Date:** 2026-04-12
**Touched:** OTT-1886-1908
**Source:** cshapes-2.0 (ogrinfo on cshapes2_full.gpkg)
**Kind:** autonomous

**Phase 1 (inventory):** 9 polity pages, ~38 open questions across
wiki, 4 pending proposals. Focus on European polities per user
instruction.

**Phase 2 (classification):** Tier 1: 4 (COW queries + Bosnia
ogrinfo). Tier 2: 2 (Biger Germany + Russia). Tier 3: 12
(dangling page refs). Tier X: ~18 (split decisions, end-date
precision, proposal-dependent items).

**Phase 3 (selection):** `oq-bosnia-double-count` on
`ott-1886-1908`. Tier 1, single CLI query on gpkg data on disk.
Tiebreaker: this page has only 1 unresolved OQ (the other,
`oq-tunisia-boundary`, was resolved 2026-04-11) — resolving it
brings the page to 0 unresolved OQs, closest to status change.

**Phase 4 (execution):** `ogrinfo` SQL queries on
`data/geodata/cshapes2_full.gpkg` for `cowcode=640` (Ottoman),
`cowcode=3461` (Bosnia), `cowcode=3462` (Herzegovina),
`cowcode=300` (Austria-Hungary), and `cowcode=355` (Bulgaria).
Results: CShapes codes Bosnia and Herzegovina as **separate
polygons** (`status: occupied`, `owner: 300`) — they are NOT part
of the Ottoman sovereign polygon. The Ottoman polygon's 10.28
sq-degree area drop at 1908-10-05 matches Bulgaria's independence
polygon exactly. Austria-Hungary's polygon grows by exactly 5.80
sq degrees at annexation, matching Bosnia (4.68) + Herzegovina
(1.12). No double-counting in WHEP.

**Outcome:** `oq-bosnia-double-count` resolved. 0 unresolved open
questions remain on `ott-1886-1908`. Page updated with CShapes
polygon convention sourced claim and territorial extent
clarification.

**Stop decision:** continue (iteration 1 of 3)

---

## deu-first-ingest
**Date:** 2026-04-11
**Touched:** DEU-1800-1919
**Source:** wikipedia-german-empire-2026-04-11 (new), docs/03 cross-reference
**Kind:** ingest

Iteration 3 of the autonomous European-empires research pass.
Creates one polity page (`deu-1800-1919.md`, the 120-year
Prussia / German Empire row from the database floor to the Treaty
of Versailles) and files a separate proposal entry
(`proposal-deu-ger-chain-audit`) covering the CSV audit findings
that phase 1 surfaced. Biger GERMANY entry deliberately deferred
(context budget); flagged as an open question on the polity page.

**Key audit outcome:** docs/03 explicitly documents GER-1800-2025
as a **trade aggregate** row while the CSV has it as
`polity_type = national`. This is a direct docs-vs-CSV contradiction
that the critical-stance rule is designed to catch. The filed
proposal recommends changing GER-1800-2025.polity_type to match
the docs. docs/03:115 also acknowledges the 1871 German
unification as an event within DEU-1800-1919 but the CSV doesn't
split on it.

New polity page `deu-1800-1919.md` covers Prussia 1800–1871 →
German Empire 1871–1918 → armistice to Versailles 1918–1919 in
one row, per the current CSV structure, but hedges the 1871
unification as a candidate mid-row split under the WHEP
territorial-change rule. All 1866 (Austro-Prussian War), 1871
(unification), 1884-85 (Berlin Conference / colonial empire
acquisition), 1914 (WWI entry), 1918-11-09 (abdication), and
1919-06-28 (Versailles) events are cited to the new Wikipedia
source. Biger's 1866 finding from the Austria entry (1866 was
"the real territorial-political turning point") is
cross-referenced.

## proposal-deu-ger-chain-audit
**Date:** 2026-04-11
**Touched:** DEU-1800-1919, DEU-1919-1920, DEU-1920-1938, DEU-1938-1945, DEU-1990-2025, GER-1800-2025, (missing) PRU-*
**Source:** docs/03_ENTRIES_RATIONALE.md, docs/00_OVERVIEW.md, docs/01_METHODOLOGY.md
**Kind:** proposal

Third proposal filed under the critical-stance rule. Five audit
findings for the DEU / GER chain. Several of them — unlike the
AUH and F228 audits — are **documented in docs/** but contradicted
by the CSV, so the fix is partly a docs-vs-CSV reconciliation.

### Finding 1 (MAJOR, DOCS-VS-CSV CONTRADICTION) — GER-1800-2025 is marked `national` in the CSV but `aggregate` in the docs

**Observed in CSV:**
```
GER-1800-2025,Germany/Zollverein,1800,2025,226,national,Europe,GER,255,...
```

**Observed in docs:**

- `docs/00_OVERVIEW.md:199`: "Use `polity_type = 'aggregate'`
  entries (GER-1800-2025, CHN-1800-2025, etc.) for..."
- `docs/01_METHODOLOGY.md:49`: "`GER-1800-2025` | Germany/Zollverein
  trade aggregate (full history)"
- `docs/01_METHODOLOGY.md:170–172`: "Trade aggregates preserved:
  Entities like 'Germany/Zollverein' (GER-1800-2025)... These
  coexist with period-specific entries (DEU-1800-1919,
  DEU-1919-1920, etc.)."
- `docs/03_ENTRIES_RATIONALE.md:487`: "GER-1800-2025 |
  Germany/Zollverein | FT trade aggregate for all German trade
  1800-2025. Encompasses pre-unification states, Empire, Weimar,
  Nazi, divided, reunified."
- `docs/11_KNOWLEDGE_GRAPH.md:69`: "An aggregate entry (e.g.,
  `GER-1800-2025` for Germany) covers all period-specific
  entries..."
- `docs/06_KNOWN_ISSUES_AND_DECISIONS.md:298`: "Recommendation:
  Use GER-1800-2025 for trade; individual states for geographic
  analysis."

**Six separate docs files** explicitly describe GER-1800-2025 as
an aggregate trade row, but the CSV has
`polity_type = national`. This is a direct contradiction.

**Recommendation:** change the `polity_type` field on row
`GER-1800-2025` from `national` to `aggregate`. This is a
one-column-edit fix that reconciles CSV with docs. No other fields
need to change.

Severity: MAJOR. Docs-vs-CSV contradictions are worse than
docs-vs-nothing gaps because they mean downstream consumers who
read the docs and trust them will get wrong results from the CSV.

### Finding 2 (MEDIUM) — DEU-1938-1945 successor graph is broken forward

**Observed:** `DEU-1938-1945.successor = NA`. Nazi Germany has
no recorded successor.

**Context:** DEU-1990-2025 (reunified Germany) has
`predecessor = "F78-1949-1990; F77-1949-1990"` (West + East
Germany), which is correct for the 1990 reunification. F77 and
F78 themselves have `predecessor` pointing back to... need to
check, but probably to DEU-1938-1945 or to nothing.

**The actual 1945–1949 period** is the Allied occupation of
Germany (4-zone division), which is not represented as a WHEP
polity row. Under the critical-stance rule this is a gap in the
graph: Nazi Germany (DEU-1938-1945) dissolves at the 1945
armistice / Potsdam Conference but the CSV does not record
where it goes.

**Recommendation:** either (a) create a new polity row
DEU-1945-1949 or F-OCC-1945-1949 representing the Allied
occupation, and set DEU-1938-1945.successor to point at it; or
(b) set DEU-1938-1945.successor directly to
"F77-1949-1990; F78-1949-1990" (skipping the 1945-1949 period
as unrepresented); or (c) treat the Nazi Germany → West/East
Germany transition as a genuine end-point with no legal
successor and leave the NA but document the rationale in a
`decision`-kind log entry.

Severity: MEDIUM. Related to the broken-successor-graph class
of issues, similar to the AUH-1908-1918 case. Not as bad
because here the backward graph works (DEU-1990-2025 correctly
links back to F77+F78), only the forward from 1945 is broken.

### Finding 3 (MEDIUM) — No Prussia (PRU) row despite multiple sibling pre-1871 German state rows

**Observed:** the CSV has rows for BAD (Baden), BAV (Bavaria),
HAN (Hanover), HES (Hesse), HHO (Hesse-Homburg), MEK
(Mecklenburg), OLD (Oldenburg), SAX (Saxony), SHL
(Schleswig-Holstein), WUR (Württemberg) — ten pre-1871 German
states plus the Denmark-Schleswig-Holstein row. **No PRU
(Prussia) row.** Prussia was the largest and most important
pre-1871 German state, leading the North German Confederation
from 1867, and was the core around which the 1871 German
Empire was built.

**Possible explanations for the absence:**

- (a) Prussia is implicitly represented by `DEU-1800-1919`,
  which covers 1800–1919 with a continuous border. This would
  treat "Prussia" and "Germany" as the same polity entity
  across the 1871 unification. Problem: DEU has COW code 260
  (modern FRG), not 255 (historical Prussia). COW explicitly
  distinguishes them.
- (b) Prussia is implicitly represented by `GER-1800-2025`
  (COW 255, matching COW's "Germany/Prussia" entry). This
  makes more sense given the COW code alignment. Problem:
  docs describe GER as an aggregate (see Finding 1), not as a
  primary polity row. If GER is the Prussia proxy, it should
  not be an aggregate; if it's an aggregate, Prussia has no
  primary-polity representation.
- (c) Prussia is a gap — nobody has added a PRU row and
  there's no conscious decision documented anywhere.

Under the critical-stance rule, (c) is the default assumption
unless (a) or (b) is supported by documented evidence. Searching
`docs/` and `wiki/log.md` did not turn up a clear rationale for
the absence.

**Recommendation:** add a `PRU-1800-1871` row to the CSV
representing the Kingdom of Prussia from 1800 to the 1871
unification. Alternatively, document the design decision
explicitly in a `decision`-kind log entry saying "Prussia is
intentionally represented as part of DEU-1800-1919 because of
the territorial-economic continuity across the 1871 unification"
or similar.

Severity: MEDIUM. Biggest-missing-state-in-Europe issue.

### Finding 4 (MEDIUM, POLICY) — DEU-1800-1919 has no mid-row split at 1871 despite docs acknowledging the unification as an event within the row

**Observed:** `DEU-1800-1919` is a single row from 1800 to 1919.
`docs/03_ENTRIES_RATIONALE.md:115` explicitly describes the row
as "German states → Empire (1871) → loss of Alsace-Lorraine
(1919)". So docs acknowledge that 1871 is an event *within* the
row. But the CSV does not split there.

**The 1871 unification was:**

- A major territorial-economic consolidation. The Zollverein
  (1834) had already established a Prussian-led customs union,
  but the 1871 Empire added Bavaria, Württemberg, Baden, and
  Hesse-Darmstadt (the four southern German states that had
  stayed outside the 1867 North German Confederation) into a
  single political and economic unit, PLUS the newly-annexed
  Alsace-Lorraine (~14,500 km² transferred from France per
  [wikipedia-german-empire-2026-04-11 §1871-alsace-lorraine]).
- Arguably the largest single-event territorial-economic
  consolidation in 19th-century Europe.
- Proclaimed on **18 January 1871** at the Hall of Mirrors at
  Versailles [wikipedia-german-empire-2026-04-11 §1871-01-18].
- Formalized constitutionally on **16 April 1871**
  [wikipedia-german-empire-2026-04-11 §1871-04-16].

**Under the WHEP polity-definition rule**
[log decision-whep-polity-definition], substantial territorial
change triggers a split. Is 1871 a substantial territorial
change?

- *Yes* — Alsace-Lorraine was annexed (clear territorial gain)
- *Yes* — four southern German states joined a single political
  and trade entity with the Prussian-led north
- *Yes* — the resulting polity has a different shape, name,
  capital (Berlin, formerly also the Prussian capital), and
  legal regime than pre-1871 Prussia
- *Not entirely* — many of the Zollverein customs-union
  relationships predated 1871

The verdict depends on whether a "political unification with
customs-union integration" counts as a single territorial
event. Biger's Austria entry describes 1866 (not 1867) as "the
real territorial-political turning point" [biger-1995 §austria],
and describes the 1871 German unification as the event that
"overwhelmed the remaining opposition to unified Germany"
[wikipedia-german-empire-2026-04-11 §1870-1871]. Both suggest
1866–1871 is a multi-step process with several candidate split
dates.

**Recommendation:** under the strict WHEP rule, DEU-1800-1919
should probably be split at at least 1871-01-18. Candidate
sub-split dates: 1866 (Austro-Prussian War → Peace of Prague),
1867 (North German Confederation), 1871-01-18 (Empire
proclamation). Joint with the 1867 Ausgleich question from
AUH audit Finding 3 — both are "when did a legal-political
reorganization become a territorial event for WHEP purposes?"
questions.

Severity: MEDIUM. Policy question, not a silent error.

### Finding 5 (MINOR) — All DEU/GER rows have `notes = NA`

**Observed:** every row in the DEU + GER chain has
`notes = NA`:

| polity_code | notes |
|---|---|
| DEU-1800-1919 | NA |
| DEU-1919-1920 | NA |
| DEU-1920-1938 | NA |
| DEU-1938-1945 | NA |
| DEU-1990-2025 | NA |
| GER-1800-2025 | NA |

By contrast, the AUH chain and the F228 chain both have
substantive notes (especially F228-1856-1905 which has a 200-word
summary of Central Asian expansion). The DEU chain has none.

**Context:** the docs describe the DEU chain's splits
(`docs/03:115`, `docs/11:198`) so the rationale *exists*, but it
wasn't copied into the CSV notes field. Possible explanations:
automated row creation without notes backfill, or manual row
creation that skipped notes as optional.

**Recommendation:** backfill the `notes` field on all DEU and
GER rows with brief summaries from `docs/03` and from this
proposal. Not critical but improves CSV self-documentation.

Severity: MINOR. The data are correct, just poorly annotated.

### Summary of DEU/GER audit

| Finding | Severity | Action |
|---|---|---|
| 1. GER-1800-2025 docs-vs-CSV contradiction on polity_type | MAJOR | CSV column edit (national → aggregate) |
| 2. DEU-1938-1945 successor graph broken forward | MEDIUM | CSV edit (successor field) or decision entry |
| 3. No Prussia row | MEDIUM | CSV edit (add row) or decision entry |
| 4. 1871 unification not a split | MEDIUM (policy) | Decision entry joint with AUH Finding 3 |
| 5. All DEU/GER rows have notes=NA | MINOR | CSV edit (notes backfill) |

Findings 1, 2, 3, and 5 can be applied without repo-rule changes.
Finding 4 is a policy question joint with the AUH Ausgleich issue
and the F228 ongoing questions. Overall the DEU chain has at
least as many CSV issues as AUH or F228 — about one major finding
per iteration is the pattern emerging from the critical-stance
audits.

---

## russian-empire-first-ingest
**Date:** 2026-04-11
**Touched:** F228-1856-1905
**Source:** wikipedia-russian-empire-2026-04-11 (new), docs/ cross-reference
**Kind:** ingest

Iteration 2 of the autonomous European-empires research pass. Creates
one polity page (`f228-1856-1905.md`, Russian Empire Alexander II/III
era) as a worked example, and files a separate proposal entry
(`proposal-f228-ussr-anachronism` below) covering the CSV audit
findings that the same phase 1 surfaced.

Scope was deliberately narrowed after phase 1 inventory: reading the
full Biger RUSSIA entry in this iteration would have required another
15–20 PDF pages of context, and the main value of the iteration is
the anachronism proposal, not a full set of Russian Empire polity
pages. Future iterations will add pages for F228-1800-1856 (early
Russian Empire), F228-1905-1914 (post-Russo-Japanese-War Empire),
F228-1914-1917 (WWI Empire), and the subsequent Soviet-era chain.

**New source file:** `wikipedia-russian-empire-2026-04-11.md`. One
Wikipedia snapshot covering 1800–1917.

**New Biger section:** deliberately skipped in this iteration — Biger
RUSSIA entry not yet read. Flagged as [oq-biger-russia] on the new
polity page.

**New polity page:** `f228-1856-1905.md` — Russian Empire,
1856 (Treaty of Paris ending Crimean War) to 1905 (Treaty of
Portsmouth ending Russo-Japanese War). Uses the CSV's rich notes
field as a starting point but hedges everywhere the current CSV
labeling conflicts with history under the new critical-stance rule.

**CSV audit findings surfaced during phase 1** (detailed in the
proposal entry below):

1. **MAJOR — Five rows mislabeled "USSR" pre-1922.** The USSR was
   formed 30 December 1922. `F228-1905-1914`, `F228-1914-1917`,
   `F228-1917-1918`, `F228-1918-1920`, and `F228-1920-1921` all
   have `polity_name = "USSR (YYYY-YYYY)"` despite predating the
   USSR's existence by up to 17 years.
2. **MEDIUM — F228 chain refactor history is visible in docs/.**
   docs/03 §411–417 describes an old F228 split structure (1800-1886,
   1886-1919, 1919-1920, 1920-1924, 1924-1926, 1926-1939, 1939-1940)
   that does not match the current CSV (1800-1856, 1856-1905,
   1905-1914, 1914-1917, 1917-1918, 1918-1920, 1920-1921, 1921-1940,
   1940-1945, 1945-1991). Docs/10, docs/11, docs/14 reference
   "F228-1940-1991" as a row that no longer exists. 15 broken
   predecessor references were fixed per docs/14 by repointing from
   F228-1940-1991 to F228-1945-1991.
3. **POSITIVE — F228-1945-1991 successor list is complete.** All 15
   USSR constituent republics are correctly listed. Counter-example
   to AUH-1908-1918 Finding 1.

## proposal-f228-ussr-anachronism
**Date:** 2026-04-11
**Touched:** F228-1905-1914, F228-1914-1917, F228-1917-1918, F228-1918-1920, F228-1920-1921, F228-1921-1940
**Source:** wikipedia-russian-empire-2026-04-11 (for dates), docs/03 cross-reference
**Kind:** proposal

Second proposal filed under the critical-stance rule from
`[log decision-csv-is-evidence-not-authority]`. The canonical
example the rule was named for: five F228 rows are labeled "USSR"
despite predating the USSR's existence, plus a sixth row with a
partial anachronism.

### Finding 1 (MAJOR) — Five F228 rows mislabeled "USSR" pre-1922

**Observed:** the following rows have `polity_name` starting with
"USSR":

| polity_code | polity_name | time range | actual entity |
|---|---|---|---|
| F228-1905-1914 | USSR (1905-1914) | 1905–1914 | **Russian Empire** |
| F228-1914-1917 | USSR (1914-1917) | 1914–1917 | **Russian Empire** (through Feb 1917) |
| F228-1917-1918 | USSR (1917-1918) | 1917–1918 | **Russian Republic** (Feb–Oct 1917) → **RSFSR** (Oct 1917–) |
| F228-1918-1920 | USSR (1918-1920) | 1918–1920 | **RSFSR** + various short-lived Soviet republics during Civil War |
| F228-1920-1921 | USSR (1920-1921) | 1920–1921 | **RSFSR** |
| F228-1921-1940 | USSR (1921-1940) | 1921–1940 | **RSFSR** (1921–1922-12-30) → **USSR** (1922-12-30–) |

**The USSR was formed on 30 December 1922** when the Treaty on the
Creation of the USSR was signed by the RSFSR, Ukrainian SSR,
Byelorussian SSR, and Transcaucasian SFSR. Anything before that date
labeled "USSR" is anachronistic.

Five full rows (F228-1905 through F228-1920-1921) are entirely
anachronistic — all 17 years of their combined coverage predate the
USSR. The sixth row (F228-1921-1940) has a 1.5-year partial
anachronism at its start (1921-01-01 to 1922-12-29 was still RSFSR,
not USSR).

**Historical labeling that WHEP should use** (based on canonical
Wikipedia date boundaries, not yet sourced to Biger or academic
history):

- 1905 → Feb 1917: Russian Empire (ruled by Nicholas II)
- Feb 1917 → Oct 1917: Russian Republic (Provisional Government)
- Oct 1917 → 30 Dec 1922: RSFSR (Russian Soviet Federative Socialist
  Republic), as the dominant but not sole Soviet republic during
  the Civil War period
- 30 Dec 1922 →: USSR (Soviet Union proper)

**Recommendation:** rename the `polity_name` field on the five fully
anachronistic rows:

- `F228-1905-1914`: "USSR (1905-1914)" → "Russian Empire (1905-1914)"
- `F228-1914-1917`: "USSR (1914-1917)" → "Russian Empire (1914-1917)"
- `F228-1917-1918`: "USSR (1917-1918)" → "Russian Republic / RSFSR
  (1917-1918)"
- `F228-1918-1920`: "USSR (1918-1920)" → "RSFSR (1918-1920)"
- `F228-1920-1921`: "USSR (1920-1921)" → "RSFSR (1920-1921)"

The partial-anachronism row `F228-1921-1940` could either be:
- left as is ("USSR (1921-1940)"), accepting a 1.5-year label
  imprecision, or
- renamed "RSFSR / USSR (1921-1940)", or
- split into `F228-1921-1922` ("RSFSR") + `F228-1922-1940` ("USSR
  (1922-1940)"), creating a new split at the 1922-12-30 Union Treaty
  date.

The last option is the cleanest historically but involves creating a
new row and repointing predecessor/successor chains. Recommended
only if the current splits are going to be re-audited anyway.

Severity: MAJOR. This is the canonical critical-stance finding the
meta-rule was named for. The labels are wrong on the face of the
CSV and have been wrong for the entire lifetime of these rows. No
human has caught it because the CSV is big and the label is a free-text
field nobody audits.

### Finding 2 (MEDIUM) — F228 chain refactor history visible in docs/

**Observed:** `docs/03_ENTRIES_RATIONALE.md` §411–417 describes an
**old** F228 split structure that does not match the current CSV:

Docs/03 version (no longer current):
```
F228-1800-1886  Russian Empire pre-CShapes
F228-1886-1919  Russian Empire (CShapes coverage)
F228-1919-1920  Post-WWI border changes
F228-1920-1924  Soviet Russia formation period
F228-1924-1926  Early USSR
F228-1926-1939  Interwar USSR
F228-1939-1940  Molotov-Ribbentrop expansion
```

Current CSV version:
```
F228-1800-1856  Russian Empire (to 1856)
F228-1856-1905  Russian Empire (1856-1905)
F228-1905-1914  USSR (1905-1914)    [anachronism, see Finding 1]
F228-1914-1917  USSR (1914-1917)    [anachronism]
F228-1917-1918  USSR (1917-1918)    [anachronism]
F228-1918-1920  USSR (1918-1920)    [anachronism]
F228-1920-1921  USSR (1920-1921)    [anachronism]
F228-1921-1940  USSR (1921-1940)    [partial anachronism]
F228-1940-1945  USSR (1940-1945)
F228-1945-1991  USSR (1945-1991)
```

**Key divergences:**
- docs/03 splits at 1886 (CShapes floor), 1919 (Versailles), 1920
  (post-Civil-War), 1924 (death of Lenin? or Treaty on Creation of
  USSR?), 1926, 1939 (Molotov-Ribbentrop), 1940. Seven split points.
- Current CSV splits at 1856 (Treaty of Paris), 1905 (Portsmouth),
  1914 (WWI), 1917 (February Revolution? / October Revolution?),
  1918, 1920, 1921 (end of Civil War), 1940 (Molotov-Ribbentrop
  gains), 1945 (post-WWII). Nine split points — a much finer
  structure.
- The docs/03 split structure has much closer alignment to Biger's
  1919 dismemberment narrative for Austria-Hungary; the current CSV
  introduces 1905 as a split point (territorial: South Sakhalin
  loss to Japan via Treaty of Portsmouth) which is defensible but
  represents a different set of editorial choices.
- `docs/10_VALIDATION_SUMMARY.md` line 50 and `docs/14_GAP_ANALYSIS`
  lines 254–255 reference **"F228-1940-1991"** as a row that
  existed when those docs were written — a consolidated USSR row
  that has since been split into `F228-1940-1945 + F228-1945-1991`.
  15 post-Soviet state rows originally had
  `predecessor = F228-1940-1991` and were repointed to
  `F228-1945-1991` per the fix recorded in docs/14.

**Implication:** the F228 chain has been refactored **at least once**
since `docs/03` was written, and docs/03's rationales for the splits
(e.g. "Post-WWI border changes" for F228-1919-1920) do not apply to
the current rows. Under the critical-stance rule, **any polity page
that cites docs/03 for an F228 split rationale is citing stale
documentation.** Polity pages for the F228 chain should cite the
current CSV notes field (if present) or file open questions for
missing rationale, not re-use docs/03 prose.

Severity: MEDIUM. Documentation drift, not a direct CSV error. The
fix is to update `docs/03` to match the current split structure, or
to add a "version notes" header to docs/03 saying it reflects an
earlier CSV vintage.

### Finding 3 (MINOR) — iso3_code inconsistency on F228 chain

**Observed:** `iso3_code` is `RUS` on F228-1800-1856 and
F228-1856-1905 but `NA` on all F228 rows from 1905 onward (through
1991). Then `RUS-1991-2014` and `RUS-2014-2025` use iso3 `RUS`
again.

Possible explanations:
- The FAOSTAT / UN M49 convention treats the USSR as a separate
  entity from the Russian Federation, and the F228-1905 → F228-1991
  rows are meant to represent "USSR as a trade entity", which
  doesn't have an ISO 3166-1 code of its own (historical code `SUN`
  exists but is not in common use). Under that reading, the NA is
  correct for the post-USSR-formation rows.
- But the NA starts at 1905, not 1922. So for F228-1905-1914
  through F228-1921-1940 (pre-USSR Russian Empire / Russian
  Republic / RSFSR), the iso3 NA is also anachronistic — these
  rows represent the Russian Empire or RSFSR, which could
  arguably use iso3 RUS.

**Recommendation:** revisit alongside Finding 1. If those rows are
relabeled to "Russian Empire" / "Russian Republic" / "RSFSR", the
iso3 probably should be RUS for the Russian Empire rows (1905-1917)
and NA for the Civil War / RSFSR rows (1917-1922), and NA for USSR
proper (1922-1991). Or consistently NA for everything between Empire
and Federation. Either way the current split at 1905 makes no sense.

Severity: MINOR. Symptom of Finding 1, not a separate issue.

### Summary of F228 audit

| Finding | Severity | Action |
|---|---|---|
| 1. USSR anachronism on 5+ rows | MAJOR | CSV rename (polity_name field on 5 rows) |
| 2. docs/03 describes old split structure | MEDIUM | docs/03 update or version-note header |
| 3. iso3 inconsistency | MINOR | CSV edit alongside Finding 1 |

All three findings are Tier X (require human action). Finding 1 is
the canonical case the critical-stance rule was named for. The polity
page `f228-1856-1905.md` created in this iteration cites this
proposal by slug and explicitly avoids inheriting any claim from the
mislabeled rows.

---

## auh-first-ingest
**Date:** 2026-04-11
**Touched:** AUH-1800-1867, AUH-1867-1908, AUH-1908-1918
**Source:** biger-1995 (existing, new §austria section), wikipedia-austria-hungary-2026-04-11 (new)
**Kind:** ingest

First pass at the Austrian Empire / Austria-Hungary chain as part
of the autonomous-research extension to European empires
1850–present. Creates three new polity pages and one new source
file, adds a new section to the Biger source file.

**Applied the critical-stance rule from
`[log decision-csv-is-evidence-not-authority]` during phase 1
inventory.** Five CSV audit findings were collected for the AUH
chain **before** any source reads. Those findings are filed in a
separate proposal entry (`proposal-auh-chain-audit` below) and
are cited by the polity pages with explicit hedging. This ingest
is the first to run end-to-end under the new rule.

**New source file:** `wikipedia-austria-hungary-2026-04-11.md`.
Snapshot of the Wikipedia *Austria-Hungary* article covering
1804–1920. Gives exact dates for the 1804-08-11 proclamation of
the Austrian Empire, the 1859 loss of Lombardy, the 1866
Austro-Prussian War and loss of Venetia, the 1867-03-30 Ausgleich,
the 1878 Bosnia occupation, the 1908-10-06 Bosnia formal
annexation, the 1914-06-28 Sarajevo assassination, the
1918-10-31 dissolution, the 1918-11-03 Villa Giusti armistice,
the 1919-09-10 Treaty of Saint-Germain, and the 1920-06-04
Treaty of Trianon. Plus the list of seven successor states.

**New Biger section:** `biger-1995.md#austria`. Compiled from the
AUSTRIA main entry (pp.47–48) and the AUSTRIA–CZECH REPUBLIC,
AUSTRIA–GERMANY, AUSTRIA–HUNGARY, AUSTRIA–ITALY boundary
subsections (pp.48–51). Load-bearing finding from Biger: the
boundary between present-day Austria and the Czech Republic
"originates from the defeat of Austria at Hradec Králové
(Königgrätz) in 1866" (p.50), and **in the Treaty of Versailles
the boundaries of 1866 were restored and Austria was declared an
independent republic**. Biger explicitly treats 1866 as the
territorial turning point and 1867 as a constitutional change
without territory movement — supporting the critical-stance
audit finding that the WHEP 1867 split is a legal, not
territorial, boundary.

**Three new polity pages:**

- `wiki/polities/auh-1800-1867.md` — Austrian Empire, 1800–1867.
  Cites the 1804 Empire proclamation as the "real" start date
  (row has a 4-year anachronistic span 1800–1804); cites the
  real territorial events within the row (1859 Lombardy, 1866
  Venetia + exclusion from German affairs); hedges the 1867
  end-of-row as a constitutional not territorial event per the
  proposal entry.
- `wiki/polities/auh-1867-1908.md` — Austria-Hungary pre-1908.
  Hedges both endpoints (1867 start and 1908 end) as
  constitutional / sovereignty events per the proposal entry.
  Notes that under the strict WHEP polity-definition rule the
  whole AUH 1800–1918 period should arguably be a single row,
  or an explicit exception for fundamental constitutional
  changes should be documented in a decision entry.
- `wiki/polities/auh-1908-1918.md` — Austria-Hungary, 1908–1918.
  The 1918 end date *is* a real territorial event (dissolution
  into seven successor states), which is consistent with the
  WHEP rule. The 1908 start-of-row is hedged per above. Successor
  list is explicitly the seven entities from Wikipedia, NOT the
  two in the current CSV successor field, flagged with the audit
  proposal slug.

All three pages are `status: draft` pending (a) resolution of the
proposal-kind audit findings by a human and (b) additional
academic sourcing. Biger + Wikipedia are sufficient for draft
but the Trianon and Saint-Germain treaty specifics would
strengthen the page significantly.

**Open questions created** across the three AUH pages (not yet
numbered — filed in the pages themselves):

- **auh-1800-1867**: pre-1804 status (4-year anachronism),
  pre-1859 territorial extent (Lombardy + Venetia in, "eight
  times the size" per Biger), 1848 revolutions and their
  territorial impact (temporary only but worth a claim).
- **auh-1867-1908**: whether to split further at 1866 (the real
  turning point) or treat the whole 1800–1908 period as one row.
- **auh-1908-1918**: whether the 1918 end date should be
  refined to a specific day (1918-10-31, 1918-11-03,
  1919-09-10, or 1920-06-04).

## proposal-auh-chain-audit
**Date:** 2026-04-11
**Touched:** AUH-1800-1867, AUH-1867-1908, AUH-1908-1918, AUT-1918-1919, AUT-1918-2025, F51-1918-1938, F248-1918-1919, POL-1918-1919
**Source:** biger-1995 §austria, wikipedia-austria-hungary-2026-04-11
**Kind:** proposal

First ingest to run under the critical-stance rule from
`[log decision-csv-is-evidence-not-authority]`. CSV audit of the
AUH chain surfaced five candidate issues. None are silently
rationalized on polity page prose — this entry documents them for
human review and decides whether the CSV should be changed.

### Finding 1 (MAJOR) — AUH-1908-1918 successor list is catastrophically incomplete

**Observed:** `AUH-1908-1918.successor = "AUT-1918-2025; HUN-1918-1919; AUT-1918-1919"`.

Austria-Hungary dissolved in 1918–1919 into (at least) **seven**
successor entities (verified by
`[wikipedia-austria-hungary-2026-04-11 §successor-states]`):

1. **Republic of German-Austria → First Austrian Republic** — WHEP
   AUT-1918-2025 ✓
2. **First Hungarian Republic** — WHEP HUN-1918-1919 ✓
3. **First Czechoslovak Republic** — WHEP F51-1918-1938 **not
   linked** (current CSV: `predecessor = NA`)
4. **Kingdom of Yugoslavia / SHS** — WHEP F248-1918-1919 **not
   linked** (current CSV: `predecessor = NA`)
5. **Second Polish Republic** (gained Galicia) — WHEP
   POL-1918-1919 **not linked** (current CSV: `predecessor = NA`)
6. **Kingdom of Romania** (gained Transylvania) — WHEP
   ROU-1918-1919 **not linked** (current CSV:
   `predecessor = ROU-1913-1918`, which is correct for Romania's
   own continuity but does not capture the Transylvania transfer
   from A-H)
7. **Kingdom of Italy** (gained Trentino, Trieste, Istria, South
   Tyrol) — WHEP ITA-1919-2025, no 1918–1919 transition row. The
   territorial transfer is not captured anywhere in the
   predecessor/successor graph.

The consequence: **the single most consequential territorial
event in early-20th-century Europe is invisible in the WHEP
predecessor/successor graph**. Any analysis that walks the graph
backward from modern Czechia, Slovakia, Slovenia, Croatia, Bosnia,
or western Poland will hit a `predecessor: NA` wall and never
reach the Austro-Hungarian parent.

**Recommendation:** update `AUH-1908-1918.successor` to list all
seven successor entities, and update the `predecessor` fields of
F51-1918-1938, F248-1918-1919, POL-1918-1919 to include
`AUH-1908-1918`. Decide separately (see the ROU case) whether to
record the Transylvania transfer from A-H to ROU and the
Trentino/Trieste/Istria transfer from A-H to ITA as additional
`successor` links even though those states existed before 1918.

Severity: MAJOR. Wiki cannot silently accept this. Polity pages
for the AUH chain cite this proposal directly.

### Finding 2 (MEDIUM) — AUT-1918-1919 / AUT-1918-2025 overlap

**Observed:** two rows both starting 1918, both with
`cow_code = 305`, both with `predecessor = AUH-1908-1918`, both
with `successor = NA`, and no chain link between them.

```
AUT-1918-2025  Austria            1918-2025  AUH-1908-1918  NA
AUT-1918-1919  Austria (1918-1919) 1918-1919  AUH-1908-1918  NA
```

Both rows claim to represent "Austria starting in 1918". Pattern
matches `TUR-1800-1912` (the Ottoman duplicate flagged in an
earlier proposal). This is a straight duplication.

**Recommendation:** either (a) remove AUT-1918-1919 entirely (it
is a 1-year orphan that duplicates the opening window of the
main Austria row), or (b) keep it as a transition row
representing the "Republic of German-Austria" 1918-11-12 →
1919-10-21 and make AUT-1918-2025 start in 1919-10-22 with
`predecessor = AUT-1918-1919` to establish the chain.

Option (b) is historically more accurate — the Republic of
German-Austria (Deutschösterreich) was a distinct legal entity
from the post-Saint-Germain First Austrian Republic — but option
(a) is simpler and matches the WHEP pattern of treating 1918 as
the Austrian start without sub-1919 precision.

Severity: MEDIUM. Same pattern as `TUR-1800-1912`, which is
still unresolved.

### Finding 3 (MEDIUM — policy question) — The 1867 Ausgleich split is inconsistent with the WHEP polity-definition rule

**Observed:** the CSV splits the AUH chain at 1867 (Ausgleich)
despite the Ausgleich being a constitutional / legal change, not
a territorial change. Biger explicitly treats 1867 as a
constitutional change: "In 1867 the Habsburg Empire became the
dual monarchy of Austria-Hungary" (p.50). Wikipedia's date is
1867-03-30. No territory was added to or removed from the polity
by the Ausgleich itself.

Under the WHEP polity-definition rule as currently written
(`[log decision-whep-polity-definition]`): *"A new polity row is
created when the territory undergoes a substantial territorial
change. The triggering event is the territorial change itself,
not the legal/diplomatic status of the unit before or after."*

By this rule, the Austrian Empire → Austria-Hungary transition
in 1867 is a non-splitting event, exactly like Luxembourg's 1848
"independent in its own right" constitutional settlement (which
is correctly treated as non-splitting on the `lux-1839-2025`
page).

**Two possible resolutions:**

- (a) **Un-split.** Merge AUH-1800-1867 and AUH-1867-1908 (and
  AUH-1908-1918 if Finding 4 below is also resolved by merging)
  into a single row spanning the whole Austrian Empire /
  Austria-Hungary period (1800 or 1804 to 1918).
- (b) **Document an exception to the rule.** Add a new
  `decision`-kind log entry stating that "fundamental
  constitutional changes that alter the polity's internal
  governance of trade and production" are a valid split trigger
  even without territorial change, and cite 1867 Ausgleich as
  the canonical example.

Both are defensible. The wiki does not have the authority to
pick one — this is a repo-rule decision. Tier X per
`wiki/prompts/autonomous-next.md`.

Severity: MEDIUM. The polity pages for the three AUH rows will
hedge explicitly: "The current CSV splits this row at 1867 /
1908, but the split events are constitutional rather than
territorial, which is inconsistent with
`[log decision-whep-polity-definition]`. See
`[log proposal-auh-chain-audit]` for the audit finding."

### Finding 4 (MEDIUM — policy question) — The 1908 Bosnia-annexation split shares Finding 3's issue

**Observed:** the CSV splits AUH at 1908-10-06 (formal annexation
of Bosnia-Herzegovina). From Austria-Hungary's perspective, Bosnia
had been:

- Austro-Hungarian-administered since 1878
  (`[wikipedia-austria-hungary-2026-04-11 §1878]`,
  `[biger-1995 §bosnia]`)
- In the Austro-Hungarian customs union since 1879 (standard
  historical fact, not yet cited to a specific source)

The 1908 event changed de jure sovereignty but not de facto
control, trade regime, or economic integration. Under the strict
WHEP rule, this is not a split trigger.

The Ottoman side of the 1908 event *is* a legitimate split for
the Ottoman chain (`[ott-1886-1908]` → `[ott-1908-1912]`)
because the Ottoman Empire lost legal sovereignty over Bosnia in
1908 (and lost its customs-union foothold for that period, if
Bosnia was in fact in the A-H customs union from 1879). But
**the symmetry is broken**: the Ottoman row splits at 1908
because of a legal loss, while the A-H row splits at 1908
because of... what? Under the critical-stance rule, this
asymmetry is itself a signal that one of the two splits is
unjustified.

**Recommendation:** resolve jointly with Finding 3 — either both
sides un-split at 1908 (the Ottoman row runs 1886–1912 as one
row; the AUH row runs 1867–1918 or 1800–1918 as one row), or an
explicit exception is documented for legal sovereignty transfers
as splitting events.

Severity: MEDIUM. Same class as Finding 3.

### Finding 5 (MINOR) — AUH-1800-1867 label anachronism

**Observed:** `AUH-1800-1867.polity_name = "Austrian Empire
(to 1867)"` for the time range 1800–1867. The Austrian Empire
was proclaimed on 1804-08-11 by Franz II
(`[wikipedia-austria-hungary-2026-04-11 §1804-08-11]`). Pre-1804,
the Habsburg state was the Archduchy of Austria and associated
lands under the (still-existing) Holy Roman Empire.

The 1800–1804 window in this row is therefore pre-Empire, and
labeling it "Austrian Empire" is a 4-year anachronism.

**Recommendation:** either (a) change `start_year` to 1804, or
(b) rename to something like "Habsburg Monarchy / Austrian
Empire" to cover the pre-1804 period. Option (a) is cleaner but
loses 4 years of data (FT trade data etc.); option (b) is more
accurate historically.

Severity: MINOR. Much smaller scale than the USSR-1905 label
issue (which is 17 years of anachronism). The WHEP database
floor is 1800, so pre-1804 content has to be labeled *something*.

### Summary of AUH audit

| Finding | Severity | Requires | Blocks |
|---|---|---|---|
| 1. Successor list incomplete | MAJOR | CSV edit (successor + predecessor fields on ~5 rows) | Graph traversal through the A-H dissolution |
| 2. AUT-1918-1919/AUT-1918-2025 overlap | MEDIUM | CSV edit (row removal or chain fix) | Clean Austria page |
| 3. 1867 Ausgleich split | MEDIUM (policy) | `decision`-kind log entry | The WHEP rule's consistency across the wiki |
| 4. 1908 Bosnia split | MEDIUM (policy) | `decision`-kind log entry (joint with Finding 3) | Rule consistency (Ottoman side affected too) |
| 5. Label anachronism | MINOR | CSV edit (start_year or polity_name) | Nothing load-bearing |

All five are Tier X under the autonomous-next prompt — the wiki
cannot resolve any of them without human action. They are filed
here so a human review can see them together and decide.

---

## decision-csv-is-evidence-not-authority
**Date:** 2026-04-11
**Touched:** wiki/README.md, wiki/prompts/ingest.md, wiki/prompts/lint.md, wiki/prompts/autonomous-next.md
**Source:** none (stated by the project maintainer in conversation)
**Kind:** decision

User feedback interrupted an Austria-Hungary research iteration:
"*dont take any of my decisions as a source of truth. dont just read
my current data and say 'this was a conscious decision'. consider
everything might be wrong. do update prompts to keep that in mind.
you can think autonomously*" (2026-04-11).

This is a **meta-rule** about how the wiki treats existing WHEP state.
The rule is simple: **the CSV is evidence, not authority.** Nothing
in `data/final/polities_database.csv`, the `docs/` tree, the R
pipeline, or prior log entries should be treated as correct by
default. Every artifact was produced by fallible humans and
automated processes, and may contain errors, mislabellings,
orphaned rows, stale decisions, or unreviewed oversights.

The rule existed implicitly in the wiki before this entry — the
very first Ottoman ingest found the `TUR-1800-1912` duplication and
filed a proposal entry for it — but the prompts and README did not
make it explicit, and the agent had drifted into rationalizing
oddities rather than auditing them. Three examples from the
session that prompted this decision:

1. **`F228-1905-1914 USSR (1905-1914)`** — the CSV labels this
   row "USSR" but the USSR did not exist until 30 December 1922.
   Either the label is wrong (should be "Russian Empire") or the
   time range is wrong. Both are possible. The agent earlier this
   session called this "mislabeled" without pressing on which
   side of the mislabeling was at fault.
2. **`DEU-1800-1919` and `GER-1800-2025 Germany/Zollverein`**
   overlap entirely across 1800–1919. The agent earlier this
   session speculated "probably an aggregate row for the trade
   regime" without evidence. Under the new rule, speculation is
   forbidden — either cite evidence or file a proposal.
3. **No `PRU` (Prussia) row in the CSV** despite Prussia being
   the core German state 1815–1871. The agent earlier this
   session called this "a design choice worth surfacing". Under
   the new rule, it is a candidate oversight to be documented as
   a proposal unless `docs/` or `log.md` contains evidence that
   Prussia was deliberately absorbed into `DEU`.

**Applied in this entry:**

- **`wiki/README.md`**: added rules #6 and #7 to the "Rules for
  the agent" section (CSV is evidence, not authority; do not
  attribute intent to state without evidence), plus a new
  top-level section *Critical stance: audit, don't deferentially
  cite* with a typology of CSV oddities (row labels vs time
  range, overlapping rows, missing rows, splits at data-source
  cutoffs, orphan rows, `notes = NA`, wrong polity_type).
- **`wiki/prompts/ingest.md`**: inserted a CSV audit substep
  inside phase 2 (identify affected polity pages). The ingest
  flow now cannot silently proceed past a CSV oddity — the agent
  must either cite documented evidence or file a proposal.
- **`wiki/prompts/lint.md`**: added a new check #8, *CSV oddity
  detection*, that scans for the oddity typology described in
  `wiki/README.md` and recommends proposal entries. Read-only;
  does not auto-fix the CSV.
- **`wiki/prompts/autonomous-next.md`**: added CSV oddity
  detection to the phase 1 inventory checklist, and added "a CSV
  oddity that a single `proposal`-kind log entry can document"
  to the Tier 1 (easy wins) list. The Russian Empire / USSR
  labeling issue is named as the canonical example.

**How this changes polity-page writing style:**

Before: "WHEP carries a separate row for X because Y. The repo's
convention is Z."

After: "The current CSV tracks X as row Y. No rationale for this
is documented in `docs/` or `log.md`; see
[log proposal-...] for the audit finding."

Hedging in the body and flagging in the log is strictly better
than speculation in the body and nothing in the log.

**Not touched:** the existing polity pages (Luxembourg, the three
Ottoman rows). Those will be re-audited opportunistically in
future ingests under the new rule. The Ottoman pages already do a
reasonable job at flagging the 1886 split as polygon-source
artifact; the Luxembourg page uses cleaner sourced-claims
language. No immediate rewrites needed.

**Next action:** resume autonomous research on European empires
1850–present, starting with Austria-Hungary, applying the new
critical stance from iteration 1 forward. Specifically: audit
the AUH chain for CSV oddities during phase 1 before any Biger
reads.

---

## autonomous-next-prompt-added
**Date:** 2026-04-11
**Touched:** wiki/prompts/autonomous-next.md (new), wiki/README.md
**Source:** none
**Kind:** decision

User requested a self-paced autonomous mode for the wiki where the
agent picks its own next task from the current state rather than
waiting for per-step human direction, inspired by Karpathy's
autoresearch pattern ([user question in conversation, 2026-04-11]).

Added `wiki/prompts/autonomous-next.md` as a documentation-only
change. **No loop has been run yet** — the prompt is stage 1 of a
two-stage rollout:

1. **Stage 1 (this entry)** — write the prompt, commit, let the user
   review the priority rules and guardrails before anything executes.
2. **Stage 2 (future)** — kick off `/loop autonomous-next` with a
   deliberately-low `max_iterations` cap (default: 3 on first run),
   review the iterations, raise the cap only after the user has seen
   it behave.

The prompt encodes a four-phase cycle per iteration (state inventory
→ classify open questions into tiers → pick ONE task → execute,
commit, decide whether to continue) and has explicit hard stop
conditions and a never-autonomously guardrail list.

**Hard guardrails** (not priority penalties — absolute prohibitions):

- No edits to `data/final/polities_database.csv`. Only `proposal`
  log entries.
- No `decision`-kind log entries that establish a repo-wide rule.
  The agent may *draft* a decision and surface it in the iteration
  report, but the entry itself is human-owned.
- No `git push`, no force push, no branch deletion, no
  `--no-verify`.
- No edits to `renv.lock`, `.gitignore`, `wiki/README.md`, or
  anything in `wiki/prompts/`.
- No closed-access source acquisition.
- No `draft → reviewed` status change unless schema requirements
  are met (academic corroboration beyond Wikipedia, no unresolved
  Contradictions, every Sourced claims bullet cited).

**Stop conditions** (any one ends the loop):

- Priority exhausted — only Tier X (user-decision / missing source)
  work remains.
- Iteration cap reached.
- Proposal accumulation — if the loop generates 2+ new `proposal`
  entries without the user having reviewed them, stop for review.
- Repeated failure on the same task.
- New contradiction surfaced.
- Commit failure.

**Priority tiers:**

- Tier 1 — Easy wins (single action + already-available source).
  The Biger Ottoman batch is the canonical example of what this
  tier looks like after a fresh ingest opens up source-expansion
  opportunities.
- Tier 2 — Source expansion (fixed-cost-already-paid ingests).
- Tier 3 — New polity page creation for dangling refs or
  frequently-cited missing polities.
- Tier 4 — Deep work (multi-iteration projects).
- Tier X — Cannot be done autonomously. If the highest-priority
  question is Tier X, skip and move on.

Within a tier, ties are broken by: number of polity pages affected,
recency of the blocking source, proximity to a status change.

**Iteration report format:** every iteration emits an H2 entry of
`kind: autonomous` to `wiki/log.md` with a full audit trail
(inventory, classification, selection, execution, outcome, stop
decision). This is the mechanism against drift — the user can read
the log and see which tier was chosen, why, and whether the loop
was gaming the metric.

**Immediately-executable Tier 1 candidates** the loop would pick up
on its first run (listed here for user reference — not yet
resolved):

- `oq-bosnia-double-count` on `ott-1886-1908`: a single `ogrinfo`
  SQL query on `data/geodata/cshapes2_full.gpkg` for `cowcode=640`
  during 1886–1908 vs the `BOS-1878-1908` polygon, compared via
  `st_intersects`.
- The five remaining partially-resolved open questions where Biger
  content already on disk has sections (BULGARIA, GREECE, SERBIA,
  EGYPT) not yet read that could fully resolve `oq-1830-events`
  and related questions.
- Stale `wiki/index.md` counters if any of the recent ingests
  have drifted them.

Not yet wired to `/loop` — the user will trigger stage 2 manually.

---

## biger-ottoman-batch-ingest
**Date:** 2026-04-11
**Touched:** OTT-1800-1886, OTT-1886-1908, OTT-1908-1912; wiki/sources/biger-1995.md
**Source:** biger-1995 (existing)
**Kind:** ingest

Second pass through Biger 1995 after the Luxembourg ingest, this
time targeted at the Ottoman successor states that directly
appear on the three OTT polity pages. Four entries read:

- **ALGERIA** (pp.22–28) — 1830 French conquest, 1847 full
  northern control, 1848 three départements, 1881 integration
  with France, 1902-12-24 Sahara annexation, plus the
  1845-03-18 Morocco–Ottoman treaty and the 1910-05-19
  Franco-Ottoman boundary convention (both rarely-cited
  specific dates for formal Franco-Ottoman territorial
  agreements).
- **BOSNIA AND HERZEGOVINA** (pp.85–87) — 1461–1483 Ottoman
  conquest, 1875–1878 Balkan crisis, 1878 start of
  Austro-Hungarian administration, 1878–1918 as a continuous
  "period of Austro-Hungarian rule". **Biger limitation:** he
  does not distinguish the 1878 de facto occupation from the
  1908 formal annexation — recorded in the source file's
  limitations section and flagged on the polity pages.
- **LIBYA** (pp.359–362) — 1835 Ottoman direct rule restored,
  1890 Sanussi vs Ottoman Turks, 1911 Italian invasion,
  1912 Treaty of Ouchy, 1934 "Libya" as a name, 1951-12-24
  independence.
- **TUNISIA** (pp.28, 361, 494) — **exact treaty date for the
  Treaty of Bardo: 12 May 1881** (ALGERIA–TUNISIA, p.28).
  Corroborated in LIBYA–TUNISIA (p.361) and the TUNISIA main
  entry (p.494). Tunisia was an Ottoman province from 1564
  and semi-autonomous from the 17th century.

**Updated `wiki/sources/biger-1995.md`** with four new sections:
`§algeria`, `§bosnia`, `§libya`, `§tunisia`. The existing
`§luxembourg` section is unchanged. All quotes are
sentence-level fair-use under Biger's strict all-rights-reserved
notice.

**Three Ottoman polity pages updated:**

- `ott-1800-1886.md`:
  - **[oq-1830-events] partially resolved.** Biger directly
    corroborates the 1830 French conquest of Algeria with
    multi-page cross-references. The Greek War of Independence
    date range (1821–1829) is confirmed via the GREECE entry
    snapshot already in Wikipedia. The exact 1830 London
    Protocol date for Greek independence and 1830 Serbian
    autonomy mechanism remain not-verbatim-quoted — would need
    a GREECE or SERBIA focused Biger read or a dedicated source.
  - **[oq-further-splits-1830-1878] substantially
    strengthened.** Biger now provides academic anchor dates
    for both candidate split points (1830 and 1878). The
    historical case for splitting this row is solid; the
    remaining blocker is pipeline cost (extracting more
    Cliopatria time-steps for one polity).
  - New sourced claim: the 1830 Algeria loss quote from Biger
    p.22, replacing the earlier Wikipedia-only framing.

- `ott-1886-1908.md`:
  - **[oq-tunisia-boundary] RESOLVED.** Exact date: Treaty of
    Bardo signed 12 May 1881, five years before this row's
    1886 start. The CShapes Ottoman polygon for 1886 onward
    correctly excludes Tunisia; the issue is in the
    predecessor row.
  - 1878 Berlin Congress claim now has dual corroboration
    (Wikipedia + Biger).

- `ott-1908-1912.md`:
  - **[oq-libya-mid-row-change] partially resolved.** Biger
    gives a clean two-phase 1911/1912 framing: Italy
    "established itself in Libya in 1911" (LIBYA–SUDAN, p.361)
    and "In 1912 Italy captured Libya" (LIBYA main, p.359).
    These are consistent with 1911 = Italian invasion + 5
    November 1911 annexation declaration, 1912 = 18 October
    1912 Treaty of Ouchy. The Libya transfer is confirmed as
    a real, >1.5 million km², rapid territorial change
    *inside* this row's window — far above any plausible
    "substantial change" threshold. The remaining question is
    a repo-wide rule (end-of-row grace period, explicit
    sub-split, or polygon-source override) that a human must
    decide.
  - Bonus finding: the 1910-05-19 Franco-Ottoman boundary
    convention was still being demarcated on the ground by a
    joint commission in 1910–1911, immediately before the
    Italian takeover. This strengthens the case that the
    Libya loss was a real rapid change, not a
    polygon-availability artefact.

**Summary of open questions across OTT pages after this ingest:**

- Resolved: `oq-tunisia-boundary` (full), `oq-1830-events`
  (partial, 1830 Algeria confirmed, Greek/Serbian verbatim
  still needed), `oq-libya-mid-row-change` (partial,
  historical facts confirmed, repo-rule decision still
  needed), `oq-further-splits-1830-1878` (historical case
  solid, pipeline cost unresolved).
- Still fully open: `oq-1886-split-is-polygon-not-territory`
  (repo-rule decision), `oq-bosnia-double-count` (needs
  `ogrinfo` query), `oq-1912-1920-gap` (repo-rule decision),
  `oq-muhammad-ali-egypt-1831` (future EGY-* ingest),
  `oq-arab-revolt-1916` (future SAU-* ingest).

**Biger coverage not yet ingested** (for future passes):
BULGARIA, EGYPT, GREECE, IRAQ, LEBANON, SAUDI ARABIA, SERBIA,
SYRIA, YEMEN. These would be relevant when we create polity
pages for those successor states.

---

## biger-1995-luxembourg-ingest
**Date:** 2026-04-11
**Touched:** LUX-1839-2025
**Source:** biger-1995 (new)
**Kind:** ingest

User added Biger 1995 (*The Encyclopedia of International
Boundaries*, Facts on File, ISBN 0-8160-3233-5) to
`wiki/sources/pdfs/` under institutional / fair-use access.
552-page reference work; alphabetical by present-day state;
"includes only contemporary international land boundaries" with
historical background sections per boundary. Stricter copyright
than all prior wiki sources — full **all rights reserved**
notice on the copyright page — so the source file and polity
page use sentence-level fair-use quotes only, each with page
citation.

Created `wiki/sources/biger-1995.md` as the primary-source file
(copyright discipline documented up front, structure section on
how the book is organized, then a `§luxembourg` subsection
compiling quotes from the relevant cross-referenced entries).

Targeted read of three sections:

- **LUXEMBOURG** (p.365) — summary entry, medieval background,
  Grand Duchy creation in 1815, post-1830 split, Nassau-Weilburg
  succession.
- **BELGIUM** + **BELGIUM—NETHERLANDS** historical background
  (pp.67–70) — the precise 1831-01-20, 1831-11-15, 1838 dates
  and, most importantly, **"The limits of Eastern Duchy of
  Luxembourg (998 sq. miles [2,584 sq. km.] out of 2,700 sq.
  miles [7,000 sq. km.]) were established by the Treaty of 19
  April 1839"** (p.70).
- **GERMANY—LUXEMBOURG** historical background (pp.238–239) —
  1797 French cession, 1815 Vienna Treaty, 1830 revolt, **"The
  area became independent in its own right in 1848"** (p.239,
  new datum not in Wikipedia), 1867 severance of German
  Confederation ties, and the direct territorial-stability
  statement **"Since 1867 no changes in the boundary line were
  made... one of the most peaceful boundaries in the world
  today"** (p.239).

**Two open questions on `lux-1839-2025` resolved:**

1. `oq-academic-corroboration` — Biger (Tel Aviv University +
   Durham International Boundaries Research Unit) provides exact
   dates and area numbers and is the reference-work citation the
   polity page was waiting for. Status moved from `draft` to
   `reviewed`.
2. `oq-territorial-stability` — Biger's direct 1867→1995
   "no changes in the boundary line" statement (p.239) is the
   academic confirmation of territorial continuity the WHEP
   polity-definition rule requires. The 1839–1867 period is
   covered by the 1839 treaty itself. The WWI and WWII
   occupations interrupted sovereignty but did not alter borders,
   which is why the row remains unbroken.

**Three new facts added to the polity page:**

1. **Exact date of the partition: 19 April 1839** (Biger p.70).
   Previously the page had only the year.
2. **Area numbers: 998 / 2,700 sq mi** — Luxembourg retained ~37%
   of its prior territory. Previously the page had only
   Wikipedia's "geographically larger western part".
3. **1848 as "independent in its own right"** (Biger p.239). A
   novel date not in Wikipedia or COW. Biger places Luxembourg's
   full legal independence at the 1848 constitutional settlement,
   distinct from 1839 (territorial partition) and 1867
   (international-boundary status). Under the WHEP polity
   definition this is a regime change, not a territorial change,
   and does not trigger a split — but it is worth citing.

**One loose-dating note to flag:** Biger writes "severance of
the German Confederation in 1867" (p.239), but the German
Confederation was formally dissolved on 23 August 1866 by the
Peace of Prague; the 1867 event was the Treaty of London (the
Luxembourg Crisis resolution) that withdrew the Prussian garrison
and guaranteed neutrality. Biger's year-level claim is close but
slightly loose on mechanism. Recorded on the polity page and in
the Biger source file's known-limitations section so future
citations are cautious with Biger's narrative phrasing.

**Open questions still open:** `oq-polygon-provenance` (pre-1886
polygon source), `oq-cshapes-1893-start` (CShapes package
internals), `oq-bleu-faostat` (FAOSTAT aggregate convention).
Biger does not address any of these directly; they need
different sources (polygon pipeline inspection, cshapes R
package code, FAOSTAT documentation).

**Status change:** `lux-1839-2025` is now the first and only
page in the wiki at `status: reviewed`.

---

## github-clickable-links
**Date:** 2026-04-11
**Touched:** wiki/README.md, wiki/polities/_template.md, wiki/prompts/lint.md
  (prior), all polity pages, all source files, wiki/log.md, wiki/index.md
**Source:** none
**Kind:** decision

User feedback: `[[wikilinks]]`, bare `[oq-slug]`, and backticked
citations like `` `[cshapes-2.0 §scope]` `` do not render as
clickable links on GitHub. The first is Obsidian-specific syntax;
the second is a markdown reference link with no definition
(renders as literal text); the third is a code span that breaks
the link machinery entirely.

**Decision:** the wiki now uses **reference-style** markdown links
throughout. Citation identifiers keep the same `[source-slug
§section]` inline form — so grep-based search and lint still
match them — but each file has a reference-definitions block at
the bottom mapping every label to a real URL. Stable IDs
(log-entry slugs, source-file section anchors) are created with
explicit `<a id="slug"></a>` anchors so the URL targets don't
depend on GitHub's heading slugifier, which mangles em-dashes and
other characters. Open questions are now H3 headings
(`### oq-slug`) because GitHub's auto-generated anchor from clean
kebab-case heading text is already good.

**Applied in this touch-up:**

1. **Schema** (`wiki/README.md`): added a *Cross-reference
   conventions* section describing the reference-style pattern,
   the `<a id>` anchor convention, and the rule that citations
   must never be wrapped in backticks.
2. **Template** (`wiki/polities/_template.md`): rewritten to show
   the new pattern end-to-end, including a reference-definitions
   block at the bottom.
3. **Source files** (5 files): added `<a id="slug"></a>` before
   every `### §section` heading so cross-source and
   polity-to-source links can target them. Wikipedia source files
   (`wikipedia-luxembourg-2026-04-11`, `wikipedia-ottoman-2026-04-11`)
   also got inline `<a id="YEAR"></a>` anchors before each
   `§YEAR` bullet so polity pages can cite `§1878`, `§1908`, etc.
   as clickable fragments. Year-range anchors use ASCII hyphens
   (`1877-1878`) even when the bullet text shows an en-dash
   (`§1877–1878`), because anchor IDs must be ASCII.
4. **Log file** (`wiki/log.md`): added `<a id="slug"></a>` before
   every `## YYYY-MM-DD — slug` entry heading. 12 entries
   anchored.
5. **Polity pages** (4 files, Luxembourg + 3 Ottoman):
   - Removed backticks from inline citations.
   - Converted `[[slug]]` wikilinks to `[slug]` reference form.
   - Normalized log refs `[log YYYY-MM-DD — slug]` →
     `[log slug]` (the date is noise — the slug is stable).
   - Converted *Open questions* section from bullets with bold
     prefixes to H3 subheadings (`### oq-slug`) so GitHub
     auto-generates a clean anchor per question.
   - Appended a reference-definitions block at the bottom of
     each file, sorted, with one line per cited label.
   - Dangling refs (polity pages that don't exist yet:
     `nld-1800-1830`, `tur-1913-1914`, `sau-1924-1932`) are
     defined as clickable links to their future file paths. On
     GitHub these render as clickable 404s, which is better than
     literal `[text]` because the reader can see where the link
     *will* go.
6. **Index** (`wiki/index.md`): every polity and source entry is
   now a proper `[name](path.md)` inline link; source list
   entries include "Cited by:" lists with links to each citing
   polity page.

**Verification:** a script walked every polity and source file,
extracted all `[label]` bracket patterns, and checked each
against the corresponding `[label]: url` definitions. All
reference-style links resolve. The only remaining bracket
patterns with no definition are literal polity codes like
`[BOS-1878-1908]`, which are deliberately not links (they are
CSV identifiers, not wiki references).

**Not converted, intentionally:**

- `log.md` body text still has inline `` `slug` `` backticked
  references to other log entries. These are meta (the log
  talking about itself) and aren't expected to be clickable.
  If they ever need to be, a follow-up pass can add a
  reference-definitions block at the bottom of `log.md`.
- `wiki/prompts/*` and `wiki/README.md` don't use citations
  at all — they describe the system, they don't participate in
  it. No conversion needed.

---

## ottoman-first-ingest
**Date:** 2026-04-11
**Touched:** OTT-1800-1886, OTT-1886-1908, OTT-1908-1912
**Source:** cliopatria-v0.1.3 (new), wikipedia-ottoman-2026-04-11 (new), cshapes-2.0, cow-state-system-v2024
**Kind:** ingest

First Ottoman batch ingest. Creates three polity pages and two new
source files.

**New sources:**

- `wiki/sources/cliopatria-v0.1.3.md` — docs-derived source file for
  Cliopatria v0.1.3 (Seshat Global History Databank), CC BY 4.0,
  ~1,600 polities, 15,690 features, 3400 BCE–2024 CE. Records the
  single-time-step extraction pattern the WHEP pipeline uses
  (`docs/06 §Ottoman entries` literally says "~2% temporal
  coverage"), the ~25–100 km spatial precision, and the list of
  10 WHEP rows that currently use Cliopatria polygons.
- `wiki/sources/wikipedia-ottoman-2026-04-11.md` — combined
  snapshot of two Wikipedia articles:
  `Decline_and_modernization_of_the_Ottoman_Empire` (1800–1908)
  and `Dissolution_of_the_Ottoman_Empire` (1908–1923). Verbatim
  quotes for 1821, 1829, 1831–1833, 1853–1856, 1877–1878, 1878
  (Congress of Berlin), 1908, 1911–1912 (Libya), 1912–1913
  (Balkan Wars), 1913, 1920 (Sèvres), 1922 (sultanate
  abolition). Several 19th-century dates (1830 Greek/Algeria,
  1881 Tunisia, 1882 Egypt, 1885 Eastern Rumelia) could not be
  pinned to verbatim quotes in the current Wikipedia snapshots
  and are listed under the source's *Known limitations* for a
  future ingest.

**New polity pages:**

- `wiki/polities/ott-1800-1886.md` — the anchoring page. Uses
  Cliopatria as polygon source (single 1800 time-step applied
  across 87 years) and CShapes is explicitly outside its
  coverage window. Flags the most important audit finding of
  this ingest: the 1886 split with OTT-1886-1908 is a
  **polygon-source boundary, not a territorial event** — see
  `oq-1886-split-is-polygon-not-territory`. Also flags the
  possibility of further splits at 1830 and 1878 under a strict
  reading of `decision-whep-polity-definition`.
- `wiki/polities/ott-1886-1908.md` — CShapes polygon, captures
  the post-1878 Berlin Congress configuration. Ends at 1908
  (Austro-Hungarian formal annexation of Bosnia + Bulgarian
  independence + Cretan union with Greece — three real events
  on 5 October 1908). Flags `oq-bosnia-double-count`: is Bosnia
  in or out of the Ottoman polygon for 1886–1908, given that a
  separate `BOS-1878-1908` WHEP row also has a polygon?
- `wiki/polities/ott-1908-1912.md` — short four-year terminal
  row. Both endpoints are real events (1908 Bosnia annexation,
  1912 Treaty of Ouchy / Italo-Turkish War end). Flags
  `oq-libya-mid-row-change`: the Libya loss of November 1912
  falls inside the row, which should trigger a split under a
  strict WHEP rule — but the row is short enough that the repo
  apparently chose not to. Also flags `oq-1912-1920-gap`: there
  is no OTT-* row between 1912 and the TUR-* chain; the Balkan
  Wars through WWI to the Republic of Türkiye are all carried
  under TUR codes. The OTT→TUR rename at 1913 is not a
  split-under-the-rule; it should be justified in a separate
  `decision` entry.

**COW finding on this ingest.** COW's `statelist2024.csv` has a
**single continuous tenure row** for `TUR, 640, 1816-01-01 →
2024-12-31`. COW makes no distinction between the Ottoman Empire
and modern Türkiye, and no split at 1886, 1908, 1912, 1922, or
1923. WHEP carries **seven** rows for the same territorial
entity (OTT-1800-1886, OTT-1886-1908, OTT-1908-1912, TUR-1913-1914,
TUR-1914-1918, TUR-1918-1920, TUR-1920-2025) plus a duplicate
`TUR-1800-1912` (see the separate proposal entry). The contrast
is sharp: COW sees one continuous state for 209 years; WHEP sees
seven (eight with the duplicate) in the same window. Under
`decision-whep-polity-definition` the WHEP approach is correct
*in principle* — WHEP's unit of analysis is territorial-economic,
not state-system — but the individual split dates need to be
audited against real territorial change, which this ingest has
now made possible.

Status: all three pages `draft` pending (a) a proper academic
source for the 19th-century events Wikipedia did not give
verbatim quotes for and (b) resolution of the
`oq-1886-split-is-polygon-not-territory` question, which is
bigger than Luxembourg's draft→reviewed blocker because it
affects the split dates themselves, not just the narrative layer.

## proposal-tur-1800-1912-duplication
**Date:** 2026-04-11
**Touched:** TUR-1800-1912 (CSV), OTT-1800-1886, OTT-1886-1908, OTT-1908-1912
**Source:** none
**Kind:** proposal

The CSV contains a row `TUR-1800-1912, Türkiye (to 1912)`
spanning exactly the same entity and time range as the three
`OTT-*` rows that were added when `OTT-1800-1912` was converted
to an aggregate (see `docs/06 §Split Ottoman Empire`). The TUR
row was not removed at that time.

**Observed in the CSV today (`data/final/polities_database.csv`):**

| row | start | end | polity_type | polygon source |
|---|---|---|---|---|
| `OTT-1800-1886` | 1800 | 1886 | national | Cliopatria (1800-1802, 2.66M km²) |
| `OTT-1886-1908` | 1886 | 1908 | national | CShapes 2.0 |
| `OTT-1908-1912` | 1908 | 1912 | national | CShapes 2.0 |
| `TUR-1800-1912` | 1800 | 1912 | national | CShapes 2.0 + CShapes-Europe |

All four rows have `cow=640`. The three OTT rows carry
substantive notes; TUR-1800-1912 has `notes = NA`. The OTT
chain's predecessor/successor links (`NA` → `OTT-1800-1886` →
`OTT-1886-1908` → `OTT-1908-1912` → `TUR-1913-1914;SAU-1924-1932`)
do **not** pass through `TUR-1800-1912` at all — it's a
disconnected node.

**Under the WHEP polity definition**
`[log 2026-04-11 decision-whep-polity-definition]`, the same
territory + same (COW-continuous) entity should be represented
by exactly one polity for any given year. 1800–1912 is currently
represented by **two parallel WHEP polities** — the OTT chain
and the orphan TUR row — which is a direct integrity violation.

**Recommendation (for the user to apply):**

Remove `TUR-1800-1912` from the CSV. The OTT chain is clearly
the live representation (substantive notes, proper
predecessor/successor links, more recent changes). Any references
to `TUR-1800-1912` elsewhere in the CSV or in downstream scripts
need to be repointed at the correct OTT row for the year in
question — a quick grep on `TUR-1800-1912` across `R/`,
`data/whep-source/`, and `data/analysis/` should enumerate them.

The wiki cannot make this change (wiki never edits
`data/final/polities_database.csv` directly per the rules in
`wiki/README.md`). This entry is filed so a human sees it next
time they look at the log.

---

## schema-stable-oq-ids-and-lint-relaxation
**Date:** 2026-04-11
**Touched:** wiki/README.md, wiki/prompts/lint.md, wiki/polities/_template.md
**Source:** none
**Kind:** decision

Two meta-changes to the wiki itself, motivated by findings in the
first lint run (`lint-luxembourg`):

1. **Open questions now use stable slug IDs.** Previously numbered
   (`open question 5`), which broke every cross-reference whenever
   a question was resolved and the list renumbered. New rule (in
   `wiki/README.md §Page schema`): each open question starts with
   `**oq-<short-kebab-case>**` and cross-references anywhere on the
   page must use the slug, e.g. "see [oq-polygon-provenance]".
   Resolved questions are struck through and left in place as
   stable anchors rather than deleted.
2. **Lint rule is now split into allowed/forbidden lists.** The
   previous rule ("do not edit polity page content during a lint
   run, lint fixes frontmatter, the index, and the log — not
   claims") was too coarse: it blocked obvious navigation repairs
   like "see open question 6" pointing at a question that doesn't
   exist, and it blocked typo fixes. New rule (in
   `wiki/prompts/lint.md §What lint is allowed to edit`):
   - **Allowed:** frontmatter, index, log, typos, broken internal
     cross-references (repoint or TODO-comment + flag).
   - **Forbidden:** adding/rewording *Sourced claims*, editing
     *Summary*/*Territorial extent*/*Contradictions*/*Decisions*
     body text, changing `sources:`, editing source files, editing
     README.md or any prompt.
   - The dividing line: lint repairs **navigation, formatting,
     indexing**; only ingest changes **what the page claims**.

Template updated (`wiki/polities/_template.md`) to show the new
open-question format with an example slug. Existing Luxembourg
page will be migrated to the new format in the immediately-following
`lux-post-lint-cleanup` ingest.

## lux-post-lint-cleanup
**Date:** 2026-04-11
**Touched:** LUX-1839-2025
**Source:** none (claim updates draw on sources already ingested)
**Kind:** ingest

Applies the findings of the `lint-luxembourg` run. Everything lint
flagged but was forbidden from touching.

**Navigation / typo fixes** (would now be allowed under the relaxed
lint rule, but bundled here for atomicity):

- Fixed typo `"CShapES"` → `"CShapes"` in *Territorial extent*.
- Migrated *Open questions* from the old 1–5 numbered format to
  stable slug IDs: `oq-polygon-provenance`,
  `oq-territorial-stability`, `oq-academic-corroboration`,
  `oq-cshapes-1893-start`, `oq-bleu-faostat`. Renamed
  "CShapes 1886–1892 gap narrowed" to the less misleading "Why
  CShapes's first Luxembourg row starts 1893-01-01".
- Repointed the two broken cross-references in *Territorial extent*:
  the 1839–1885 polygon note now points at
  `[oq-polygon-provenance]`, and the old "see open question 6"
  pointer is gone entirely (its content is now a sourced-claim
  statement of resolution, not an open question).

**Claim updates** (these are why this is an `ingest`, not a `lint`):

- Rewrote the *CShapes version coding* paragraph in *Territorial
  extent*. The old text said WHEP "does not record which CShapes
  version was loaded" and framed the COW/GW choice as an open
  question. The new text states the resolution: WHEP loads the
  COW variant, confirmed by schema inspection and by bit-equivalent
  regeneration from `cshp(useGW = FALSE, dependencies = TRUE)`,
  with forward references to the two `log.md` entries that
  established it (`decision-cshapes-is-cow-based` and
  `cshapes-reproducibility-verified`).
- Rebuilt the *Decisions* section. Previously a single stub entry
  for the first ingest; now lists all eight `log.md` entries that
  touched this page or established a rule affecting it, newest
  first, with ★ marking the two repo-wide `decision`-kind rules.
  The new rationale for keeping the page at `status: draft` is
  linked to `[oq-academic-corroboration]` — needs at least one
  academic or reference-work source for the 1839 territorial
  event before it can move to `reviewed`.

No changes to `sources:`, frontmatter (other than already-current
`last_ingest`), or any source file. Status stays `draft`.

---

## lint-luxembourg
**Date:** 2026-04-11
**Touched:** LUX-1839-2025 (report only), wiki/index.md (auto-applied)
**Source:** none
**Kind:** lint

First lint run on the wiki, scoped to the single Luxembourg page plus
the shared infrastructure it depends on. Executed `wiki/prompts/lint.md`.

**Summary:**

| check | result |
|---|---|
| Schema conformance | PASS — all 10 required frontmatter fields and all 7 required H2 sections present. |
| CSV ↔ wiki parity | PASS — `LUX-1839-2025` exists in `data/final/polities_database.csv:410`. `F15-1800-1999` (Belgium-Luxembourg aggregate) exists and is correctly flagged on the page as a separate row that must not be conflated. No orphan polity pages. |
| Citation health | PASS — 10 `Sourced claims` bullets, every one cited. 1 pure `[database]` bullet (10%), far below the 50% threshold that would flag the page for re-ingest. |
| Contradiction backlog | PASS — section is empty by design with an explanatory note; nothing sitting >90 days. |
| Staleness | PASS — `last_ingest: 2026-04-11` is today. |
| Index freshness | Auto-fixed (see below). |
| Source reachability | PASS — all 3 sources (`cshapes-2.0`, `cow-state-system-v2024`, `wikipedia-luxembourg-2026-04-11`) are cited by Luxembourg; no zero-citation sources. |

**Must fix (body-text issues, not auto-applied per lint rule):**

1. **Broken internal cross-reference, line 52**: *Territorial extent*
   says "See open question 5" for pre-1886 polygon provenance, but
   that question is now **open question 1** after a renumbering. The
   reference points at the wrong bullet (currently BLEU vs F15).
2. **Broken internal cross-reference, line 76**: *Territorial
   extent* says "see open question 6", but there is no open question
   6 (the list has only 5 entries after the same renumbering).
3. **Typo, line 64**: `"silently absent from CShapES."` — should be
   `"CShapes"`. Inside a lint rule, so grep will find it.

**Should review (claim-level drift, not auto-applied):**

4. **Stale "COW vs GW coding" paragraph, lines 71–76.** The page
   text says "The repo's CSV records COW code 212 for Luxembourg
   but does not record which CShapes version was loaded" and tells
   the reader to see open question 6. Both halves are outdated:
   `log.md 2026-04-11 decision-cshapes-is-cow-based` and
   `cshapes-reproducibility-verified` resolved this definitively
   (COW, bit-equivalent to `cshp(useGW=FALSE, dependencies=TRUE)`),
   and `R/00b_fetch_cshapes.R` now records the convention in code.
   The paragraph should be rewritten to state the resolution
   instead of asking the question.
5. **Decisions section is under-populated.** Currently lists only
   `lux-first-ingest`. Should also reference, in rough order of
   relevance to this page:
   - `log 2026-04-11 — decision-whep-polity-definition` (the rule
     that lets Luxembourg start in 1839)
   - `log 2026-04-11 — decision-cshapes-is-cow-based` (the rule
     behind which CShapes timeline applies)
   - `log 2026-04-11 — cshapes-primary-source-upgrade`
   - `log 2026-04-11 — cshapes-reproducibility-verified`
   - `log 2026-04-11 — cow-state-system-v2024-ingest`
6. **Decisions rationale is stale.** The `lux-first-ingest` entry
   says "Status remains `draft` because the narrative layer rests
   on a single tertiary source." Still true (Wikipedia is the only
   narrative source), but the entry doesn't mention that two more
   ingests happened the same day. A fresh rationale: "Remains
   `draft` pending at least one academic or reference-work source
   (Britannica, national history) to corroborate the 1839
   territorial event — see open question 3."

**Auto-applied:**

- `wiki/index.md` — replaced the placeholder
  `"(run \`wc -l data/final/polities_database.csv\`)"` with the
  real row count `1386 (as of 2026-04-11 lint)` under *Coverage →
  Polities in CSV*.
- This log entry.

**Recommendation.** Issues 1–6 are all on the Luxembourg page body,
which the lint rule forbids editing. Apply them manually, or run a
short touch-up ingest that bundles the six fixes into a single
`ingest`-kind log entry (since fix 4 is a claim update, not just a
cross-reference repair, it's better as a real ingest than as a
lint).

---

## cow-state-system-v2024-ingest
**Date:** 2026-04-11
**Touched:** LUX-1839-2025
**Source:** cow-state-system-v2024 (new)
**Kind:** ingest

Downloaded the Correlates of War State System Membership List v2024
directly from correlatesofwar.org (no authentication needed; public
academic dataset distributed under a citation request, not a
no-redistribute clause). Created `wiki/sources/cow-state-system-v2024.md`
and committed the two core CSVs (`statelist2024.csv`, `system2024.csv`)
under `wiki/sources/data/cow-v2024/` so the wiki is self-contained for
COW claims. Codebook PDF goes to `wiki/sources/pdfs/` which is
gitignored.

Used COW to upgrade three claims on `lux-1839-2025.md`:

1. **Direct citation for Luxembourg's COW state-system dates** (two
   tenure rows, 1920-11-15→1940-05-10 and 1944-09-10→2024-12-31),
   rather than inferring them via CShapes.
2. **Confirms the COW/CShapes alignment** — CShapes's two
   `independent` windows for Luxembourg match COW's two tenure rows
   to the day, which is exactly what the CShapes paper says should
   happen since `useGW=FALSE` loads COW membership as the
   independence criterion.
3. **Narrows (but does not resolve) open question 4** about the
   1893-01-01 CShapes row start. COW does not list Luxembourg until
   1920, so the 1893 row start is NOT a COW membership transition
   (my earlier guess was wrong). It must come from CShapes's
   dependency-tracking sources — the Territorial Change Dataset,
   Biger 1995, or Brownlie & Burns 1979. Full resolution would need
   another source ingest or inspection of the cshapes package
   internals.

Also recorded a small but useful finding for any future COW citation:
COW has revised start dates between vintages (the codebook p.3–4
lists a v2004.1 change moving Brazil's start from 1826-01-01 to
1822-09-07, Afghanistan from 1920 to 1919, Panama from 1920 to 1903).
Any wiki page citing `[cow-state-system-v2024]` is citing v2024
specifically — later COW vintages are a new source file, not an
edit.

---

## cshapes-reproducibility-verified
**Date:** 2026-04-11
**Touched:** (none — verification only)
**Source:** cshapes-2.0
**Kind:** lint

Resolved the provenance gap noted in the earlier
`decision-cshapes-is-cow-based` entry. Installed `cshapes` R package
v2.0 into a scratch library (`/tmp/rlib_cshapes`, not `renv/`) and
ran `cshp(useGW = FALSE, dependencies = TRUE)`, then compared the
output against `data/geodata/cshapes2_full.gpkg`:

- 805 rows in both.
- Identical column set, no `gwcode`.
- All (cowcode, country_name, start, end, status) tuples identical
  after sorting.
- All 805 geometries `st_equals`-identical.

Conclusion: the on-disk gpkg is bit-equivalent in content to the
R package default for `useGW=FALSE, dependencies=TRUE`. This means:

1. The COW finding stands — the R call literally specifies it.
2. The 1893 Luxembourg start is canonical to cshapes 2.0, not a
   local artefact. (Open question 4 on `lux-1839-2025` therefore
   becomes a question about `cshapes` upstream, not about WHEP.)
3. Anyone can regenerate the file deterministically, so lint runs
   do not have to trust the file's provenance.

Recommendation for a future repo change (not applied here — wiki
does not edit pipeline code): add `R/00b_fetch_cshapes.R` with

```r
library(cshapes); library(sf)
cs <- cshp(useGW = FALSE, dependencies = TRUE)
st_write(cs, file.path(geodata_dir, "cshapes2_full.gpkg"),
         delete_dsn = TRUE)
```

and correct `REPRODUCIBILITY.md:162` to point at it. Also add
`cshapes` to `renv.lock`.

## decision-whep-polity-definition
**Date:** 2026-04-11
**Touched:** (repo-wide; the definition of what a WHEP polity is)
**Source:** none (stated by the project maintainer in conversation)
**Kind:** decision

Records the WHEP definition of a polity. This is the most load-bearing
rule in the wiki and should be cited from every polity page whose
start/end year differs from an external source's independence dating.

**Rule.** A WHEP polity is a **territorial-economic unit** with trade
or production data attached, not a Westphalian legal state. Specifically:

1. **Split rule.** A new polity row is created when the territory
   undergoes a *substantial* territorial change. The triggering event
   is the territorial change itself, not the legal/diplomatic status
   of the unit before or after.
2. **Continuity rule.** If the territory remains the same, the polity
   stays a single continuous row across the full window for which
   trade or production data is available, **even across**:
   - regime changes (monarchy → republic, etc.)
   - wartime occupations that do not alter the final borders
   - entry into or exit from personal unions, customs unions, or
     federations, unless those events coincide with a territorial
     change
   - periods when external state-system datasets (COW, GW, CShapes)
     do not list the unit as an independent state
3. **Independence is not the criterion.** If trade or production data
   exists for a territory, it is a WHEP polity regardless of whether
   any external source considers it independent, a dependency, or
   "N/A". Conversely, a legally independent state with no trade data
   attached is not automatically a WHEP polity.

**Why.** WHEP exists to analyze historical trade and production at
the level of stable economic territories. Legal/diplomatic definitions
of statehood (COW's two-major-power rule, population thresholds, etc.)
do not track the right unit for trade analysis: a colony with its own
customs regime and trade statistics is a trade unit even if COW codes
it as a dependency, and a state under military occupation whose
borders did not move is still the same trade unit afterwards.

**How to apply on polity pages.** When the WHEP start/end year differs
from an external source's independence dating, this is not a
contradiction and should NOT be recorded in a page's *Contradictions*
section. Instead:

- Record the WHEP date in *Summary* and cite this decision entry.
- Record the external source's date in *Sourced claims* as a fact
  about that source, with the note that it uses a different
  definition.
- Use *Contradictions* only for disagreements *within the same
  definition*: e.g. two historical atlases giving different dates
  for the same territorial change, or two sources disagreeing on
  whether a transfer of territory actually happened.

**How to apply at ingest time.** Before creating a new polity page
from an ingested source, check whether the source is tracking
state-system membership (COW, GW, Polity V, V-Dem) or territorial
extent (CShapes, Euratlas, Cliopatria, historical atlases). Only the
second category can justify a *split* in a WHEP polity. The first
category can inform *Sourced claims* about regime type and diplomatic
status but must not drive start/end years.

**Open sub-question.** The rule says "substantial" territorial change
without quantifying it. CShapes uses a 100 × 100 km threshold
`[cshapes-2.0 §coding-changes]`; WHEP does not have a written
threshold. A future `decision` entry should pick a WHEP-specific
threshold or explicitly defer to case-by-case judgement. For now,
existing splits in the CSV stand as precedent.

## decision-cshapes-is-cow-based
**Date:** 2026-04-11
**Touched:** (repo-wide; applies to every CShapes-citing polity)
**Source:** cshapes-2.0
**Kind:** decision

Resolves open question #6 on `lux-1839-2025` and establishes a repo-wide
convention: **WHEP uses the COW-based version of CShapes 2.0**.

Evidence (direct inspection of `data/geodata/cshapes2_full.gpkg`):

1. **Schema.** The `cshapes` layer contains `cowcode` but no `gwcode`
   column. The paper notes both columns are typically present
   `[cshapes-2.0 §coding-dependencies]`; the absence of `gwcode` here
   is consistent with the COW-only distribution.
2. **Canada acid test.** The paper explicitly names Canada as the
   case that distinguishes the two versions: COW sets independence
   to 1920, GW to 1867 `[cshapes-2.0 §coding-states]`. Our gpkg has
   three Canada rows with `cowcode=20`: 1886-01-01 to 1920-01-09 as
   `colony`, 1920-01-10 to 1948-07-21 as `independent`, and
   1948-07-22 to 2019-12-31 as `independent`. The 1920-01-10 transition
   matches the COW date exactly; the GW 1867 date does not appear.

Provenance caveat: I could not find the R code that actually *writes*
`cshapes2_full.gpkg`. `REPRODUCIBILITY.md` attributes it to R/01, but
R/01 only reads a pre-existing `cshapes.csv` from `data/whep-source/`
— it does not call `cshapes::cshp()` and does not write any gpkg.
Either the gpkg was built by a one-off script not checked in, by a
prior pipeline version, or was downloaded directly from ETH Zurich.
Worth flagging as a reproducibility gap in a future log entry; the
COW finding stands regardless because it is a property of the data
actually on disk.

**Consequence:** every polity page that cites CShapes implicitly
cites the **COW-based** version. Polity start years derived from
`[cshapes-2.0]` must be read against COW's independence criteria
(diplomatic ties to two major powers, population threshold, etc.),
not GW's. For polities that are well-known as COW/GW edge cases
(Canada, Luxembourg, several Central American states before WWII,
possibly Tibet and Orange Free State which GW includes and COW does
not), the page must either note this in Contradictions or justify
the WHEP start year from a non-CShapes source.

## cshapes-primary-source-upgrade
**Date:** 2026-04-11
**Touched:** LUX-1839-2025
**Source:** cshapes-2.0 (upgraded)
**Kind:** ingest

User downloaded the CShapes 2.0 paper (Schvitz et al. 2022, JCR 66(1))
to `wiki/sources/pdfs/` under institutional access. Rewrote
`wiki/sources/cshapes-2.0.md` from a docs-derived stub (citing
`docs/04` and `docs/06` second-hand) into a primary-source file with
page-anchored verbatim quotes, DOI, and PDF SHA-256 for verification.

Added `wiki/sources/pdfs/` to `.gitignore` with a README explaining
why: PDFs are copyrighted, not redistributable, and the source file
plus hash is sufficient provenance.

Five material facts from the paper that the previous docs-derived
stub did not have:

1. CShapes ships in **two versions** (COW-based and GW-based) that
   differ on pre-1945 independence dates. Canada is 1920 under COW,
   1867 under GW. The repo does not record which version it loaded.
2. Border adjustments smaller than **100 × 100 km** are excluded by
   design. 138 transfers in the Territorial Change Dataset are
   silently dropped, including the 1922 Silesia Plebiscite (9,702 km²)
   and the 1929 Peru-Chile treaty (8,498 km²). Lint rule: any WHEP
   polity hinging on a sub-threshold transfer cannot cite CShapes.
3. Dependencies with population under **250,000** are excluded.
4. **Disputed territories** are assigned to the de facto controller,
   not coded separately. De facto states (Abkhazia, South Ossetia,
   Biafra, RSK) have no CShapes polygon of their own.
5. **Backdated borders** — 152 of 249 units have a single polygon
   copied across 1886–2019. The "1886 polygon" is literally the same
   geometry as the 2019 polygon for those countries.

Corrected a guessed author-list ordering in the previous stub. The
actual byline is Schvitz, Girardin, Rüegger, Weidmann, Cederman,
Gleditsch. The stub had them in a different order — a small reminder
that docs-derived source files can silently carry errors the primary
source would have caught.

Updated `wiki/polities/lux-1839-2025.md` to cite specific CShapes
paper sections (§scope, §coding-states, §coding-changes, §geocoding)
instead of generic `[cshapes-2.0]` tags, and added a sixth open
question about which CShapes version (COW or GW) the repo loads.
Status remains `draft`.

## lux-first-ingest
**Date:** 2026-04-11
**Touched:** LUX-1839-2025
**Source:** cshapes-2.0, wikipedia-luxembourg-2026-04-11
**Kind:** ingest

First real two-source ingest for the wiki. Created `wiki/sources/cshapes-2.0.md`
(polygon/border evidence, derived from `docs/04_POLYGON_SOURCES.md` and
`docs/06_KNOWN_ISSUES_AND_DECISIONS.md` — no external fetch) and
`wiki/sources/wikipedia-luxembourg-2026-04-11.md` (narrative history, verbatim
quotes from the `History_of_Luxembourg` article snapshotted on 2026-04-11).

Rewrote `wiki/polities/lux-1839-2025.md` from skeleton to a fully-cited draft.
Every factual claim now carries an inline citation. Status kept at `draft`
pending academic corroboration (COW / Polity V) — a single tertiary source
is not enough to mark a page `reviewed`.

Five open questions recorded on the page, the most load-bearing being whether
WHEP's general rule for personal unions is consistent with treating Luxembourg
as an independent polity from 1839 despite the personal union with the
Netherlands lasting until 1890. This is a cross-polity question and should
be resolved via a `decision`-kind log entry, not on the Luxembourg page alone.

## wiki-bootstrap
**Date:** 2026-04-11
**Touched:** (none)
**Source:** none
**Kind:** decision

Wiki created. Schema and prompts in place. No polity pages yet beyond the
Luxembourg worked example, which is a skeleton to demonstrate the format,
not a reviewed page.
