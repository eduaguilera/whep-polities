# Wiki Index

Auto-maintained catalog. Every page in `wiki/polities/` must appear here;
lint fails if the index is stale.

## Coverage

| Metric | Value |
|---|---|
| Polities in CSV | 1386 (as of 2026-04-11 lint) |
| Polity pages | 15 |
| Sources ingested | 14 |
| Pages with `status: reviewed` | 1 |
| Pages with `status: contested` | 0 |
| Open questions across wiki | 49 unresolved (54 total, 5 resolved) as of 2026-04-12 lint |
| Open `proposal`-kind log entries | 4 (tur-1800-1912-duplication, auh-chain-audit, f228-ussr-anachronism, deu-ger-chain-audit) |

## Polities by continent

### Europe

- [Italy (to 1919)](polities/ita-1861-1919.md) —
  `ITA-1861-1919`, draft, 6 open questions. 59-year row from
  unification (1861-03-17) to Saint-Germain (1919-09-10). 6
  predecessor entities. No mid-row splits at 1866 (Venetia) or
  1870 (Rome) — both flagged.
- [United Kingdom (to 1921)](polities/gbr-1800-1921.md) —
  `GBR-1800-1921`, draft, 5 open questions. 122-year row;
  metropolitan territory stable throughout. Split at 1921
  Anglo-Irish Treaty (Irish Free State secession).
- [France (to 1919)](polities/fra-1800-1919.md) —
  `FRA-1800-1919`, draft, 5 open questions. 120-year row
  covering Napoleonic France through Versailles. No mid-row
  splits at 1860 (Nice/Savoy) or 1871 (Alsace-Lorraine) — both
  flagged as candidate split points.
- [Spain](polities/esp-1800-2025.md) —
  `ESP-1800-2025`, draft, 4 open questions. 226-year continuous
  row. Metropolitan borders unchanged since 1815. Colonial losses
  (Latin America 1810s–20s, Cuba/Philippines 1898) tracked as
  separate rows.
- [United Kingdom of the Netherlands](polities/nld-1800-1830.md) —
  `NLD-1800-1830`, draft, 4 open questions. 1800–1830, includes
  Belgium and Luxembourg. Belgian Revolution 1830 splits into 3
  successor entities.
- [Luxembourg](polities/lux-1839-2025.md) — `LUX-1839-2025`,
  **reviewed**, 4 unresolved open questions (1 resolved).
- [Ottoman Empire (to 1886)](polities/ott-1800-1886.md) —
  `OTT-1800-1886`, draft, 4 open questions. Cliopatria polygon.
- [Ottoman Empire (1886–1908)](polities/ott-1886-1908.md) —
  `OTT-1886-1908`, draft, 0 unresolved open questions.
- [Ottoman Empire (1908–1912)](polities/ott-1908-1912.md) —
  `OTT-1908-1912`, draft, 3 open questions.
- [Austrian Empire (to 1867)](polities/auh-1800-1867.md) —
  `AUH-1800-1867`, draft, 4 open questions. Flagged by
  audit Findings 3 (1867 split) and 5 (label anachronism).
- [Austria-Hungary (to 1908)](polities/auh-1867-1908.md) —
  `AUH-1867-1908`, draft, 4 open questions. Flagged by audit
  Findings 3 (1867 split) and 4 (1908 split).
- [Austria-Hungary (1908–1918)](polities/auh-1908-1918.md) —
  `AUH-1908-1918`, draft, 4 open questions. Flagged by audit
  Findings 1 (successor list incomplete — major) and 4
  (1908 start).
- [Russian Empire (to 1856)](polities/f228-1800-1856.md) —
  `F228-1800-1856`, draft, 4 open questions. Pre-Crimean War
  era: Georgia, Finland, Bessarabia, Congress Poland acquisitions.
  ~17.4M km². Predecessor gap on F228-1856-1905 now closed.
- [Russian Empire (1856–1905)](polities/f228-1856-1905.md) —
  `F228-1856-1905`, draft, 4 open questions. Alexander II/III
  reform and expansion era: Crimean War end → Portsmouth.
  The last correctly labeled F228 row before the 5-row
  "USSR" anachronism block.
- [Germany (to 1919)](polities/deu-1800-1919.md) —
  `DEU-1800-1919`, draft, 6 open questions. A 120-year row
  covering Prussia 1800 → German Empire 1871 → Versailles
  1919. The 1871 unification is acknowledged in docs/03 as a
  mid-row event but not a CSV split. Flagged by audit
  Findings 1 (docs-vs-CSV contradiction on GER polity_type),
  2 (DEU-1938-1945 broken forward graph), 3 (no Prussia
  row), 4 (1871 not a split), and 5 (notes = NA on every
  row in the chain).

### Africa
_(none yet)_

### Americas
_(none yet)_

### Asia
_(none yet)_

### Oceania
_(none yet)_

## Sources

- [cshapes-2.0](sources/cshapes-2.0.md) — Schvitz et al. 2022,
  *Mapping the International System, 1886-2019: The CShapes 2.0
  Dataset*, JCR 66(1), 144–161. DOI 10.1177/00220027211013563.
  Primary source (PDF on disk, hash verified). Cited by:
  [lux-1839-2025](polities/lux-1839-2025.md),
  [ott-1800-1886](polities/ott-1800-1886.md),
  [ott-1886-1908](polities/ott-1886-1908.md),
  [ott-1908-1912](polities/ott-1908-1912.md).
- [cow-state-system-v2024](sources/cow-state-system-v2024.md) —
  Correlates of War State System Membership List v2024. Data
  committed under `wiki/sources/data/cow-v2024/`. Cited by:
  [lux-1839-2025](polities/lux-1839-2025.md),
  [ott-1800-1886](polities/ott-1800-1886.md),
  [ott-1886-1908](polities/ott-1886-1908.md),
  [ott-1908-1912](polities/ott-1908-1912.md).
- [wikipedia-luxembourg-2026-04-11](sources/wikipedia-luxembourg-2026-04-11.md)
  — History of Luxembourg, Wikipedia snapshot 2026-04-11. Cited by:
  [lux-1839-2025](polities/lux-1839-2025.md).
- [cliopatria-v0.1.3](sources/cliopatria-v0.1.3.md) — Seshat
  Global History Databank, Cliopatria v0.1.3, CC BY 4.0, ~1,600
  polities 3400 BCE–2024 CE. Docs-derived source file (no paper
  fetched yet). Cited by:
  [ott-1800-1886](polities/ott-1800-1886.md),
  [ott-1886-1908](polities/ott-1886-1908.md).
- [wikipedia-ottoman-2026-04-11](sources/wikipedia-ottoman-2026-04-11.md)
  — Two Wikipedia snapshots (*Decline and modernization of the
  Ottoman Empire* and *Dissolution of the Ottoman Empire*)
  covering 1800–1923. Cited by:
  [ott-1800-1886](polities/ott-1800-1886.md),
  [ott-1886-1908](polities/ott-1886-1908.md),
  [ott-1908-1912](polities/ott-1908-1912.md).
- [biger-1995](sources/biger-1995.md) — Biger, Gideon (ed.),
  *The Encyclopedia of International Boundaries*, Facts on File,
  1995 (ISBN 0-8160-3233-5), in collaboration with the Durham
  International Boundaries Research Unit. Strict all-rights-reserved;
  fair-use short-quote citation only. PDF gitignored, SHA-256
  recorded. Six `§`-sections so far (luxembourg, austria,
  algeria, bosnia, libya, tunisia). Cited by:
  [lux-1839-2025](polities/lux-1839-2025.md),
  [ott-1800-1886](polities/ott-1800-1886.md),
  [ott-1886-1908](polities/ott-1886-1908.md),
  [ott-1908-1912](polities/ott-1908-1912.md),
  [auh-1800-1867](polities/auh-1800-1867.md),
  [auh-1867-1908](polities/auh-1867-1908.md),
  [auh-1908-1918](polities/auh-1908-1918.md).
- [wikipedia-austria-hungary-2026-04-11](sources/wikipedia-austria-hungary-2026-04-11.md)
  — Snapshot of the *Austria-Hungary* Wikipedia article
  covering 1804–1920. Verbatim dates for the 1804 Empire
  proclamation, 1859 Lombardy loss, 1866 Venetia loss, 1867
  Ausgleich, 1878 Bosnia occupation, 1908-10-06 Bosnia
  annexation, 1914 WWI entry, 1918-10-31 dissolution, 1919
  Saint-Germain, 1920 Trianon, plus the list of seven
  successor states. Cited by:
  [auh-1800-1867](polities/auh-1800-1867.md),
  [auh-1867-1908](polities/auh-1867-1908.md),
  [auh-1908-1918](polities/auh-1908-1918.md).
- [wikipedia-russian-empire-2026-04-11](sources/wikipedia-russian-empire-2026-04-11.md)
  — Snapshot of the *Russian Empire* Wikipedia article with
  dates for the 1856 Treaty of Paris, 1858/1860 Aigun/Peking
  Far East gains, 1861 serf emancipation, 1865–1884 Central
  Asian conquests (Tashkent, Bukhara, Khiva, Kokand, Merv),
  1867 Alaska sale, 1875 Sakhalin/Kurils exchange, 1878
  Congress of Berlin Russian side, 1897 census, 1904–1905
  Russo-Japanese War, 1905 Treaty of Portsmouth and
  Revolution. Canonical citation target for the "USSR did not
  exist until 30 December 1922" claim. Cited by:
  [f228-1856-1905](polities/f228-1856-1905.md).
- [wikipedia-italy-2026-04-12](sources/wikipedia-italy-2026-04-12.md)
  — Snapshot of *Kingdom of Italy* Wikipedia article with dates
  for 1861-03-17 unification, 1866 Venetia, 1870-09-20 Rome
  capture, 1882-05-20 Triple Alliance, 1919-09-10 Treaty of
  Saint-Germain. Cited by:
  [ita-1861-1919](polities/ita-1861-1919.md).
- [wikipedia-uk-2026-04-12](sources/wikipedia-uk-2026-04-12.md)
  — Snapshots of *History of the United Kingdom* and
  *Anglo-Irish Treaty* Wikipedia articles with dates for the
  1801 Act of Union, 1921-12-06 Anglo-Irish Treaty, 1922-12-06
  Irish Free State establishment. Cited by:
  [gbr-1800-1921](polities/gbr-1800-1921.md).
- [wikipedia-france-2026-04-12](sources/wikipedia-france-2026-04-12.md)
  — Snapshots of *France in the long nineteenth century* and
  *French colonial empire* Wikipedia articles with dates for the
  1815 Vienna settlement, 1830 Algeria invasion, 1860 Nice/Savoy
  annexation, 1871 Treaty of Frankfurt (Alsace-Lorraine loss),
  1881 Tunisia protectorate, 1919 Versailles. Cited by:
  [fra-1800-1919](polities/fra-1800-1919.md).
- [wikipedia-german-empire-2026-04-11](sources/wikipedia-german-empire-2026-04-11.md)
  — Snapshot of the *German Empire* Wikipedia article with
  dates for the 1834 Zollverein, 1864 Second Schleswig War,
  1866 Austro-Prussian War, 1867 North German Confederation,
  1870–1871 Franco-Prussian War, 1871-01-18 Empire
  proclamation at Versailles, 1871-04-16 Constitution, 1871
  Alsace-Lorraine annexation, 1884–1885 Berlin Conference,
  1914-07-28 WWI entry, 1918-11-09 abdication, 1918-11-11
  armistice, 1919-06-28 Versailles. Cited by:
  [deu-1800-1919](polities/deu-1800-1919.md).

## Aggregates and unions

_(entries that cover multiple polities, e.g. customs unions, colonial
federations — live in `wiki/polities/_aggregates/`)_

## Log and meta

- [log.md](log.md) — append-only decision trail
- [README.md](README.md) — wiki schema and link conventions
- [prompts/ingest.md](prompts/ingest.md), [prompts/query.md](prompts/query.md), [prompts/lint.md](prompts/lint.md)
- [prompts/autonomous-next.md](prompts/autonomous-next.md) —
  self-paced meta-prompt for running the wiki in autonomous mode
  via the `/loop` skill (not yet wired; documentation only).
