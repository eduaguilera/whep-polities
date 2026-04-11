# Wiki Index

Auto-maintained catalog. Every page in `wiki/polities/` must appear here;
lint fails if the index is stale.

## Coverage

| Metric | Value |
|---|---|
| Polities in CSV | 1386 (as of 2026-04-11 lint) |
| Polity pages | 4 |
| Sources ingested | 6 |
| Pages with `status: reviewed` | 1 |
| Pages with `status: contested` | 0 |
| Open questions across wiki | 11 (1 fully resolved, 3 partially resolved by Biger Ottoman batch ingest) |

## Polities by continent

### Europe

- [Luxembourg](polities/lux-1839-2025.md) — `LUX-1839-2025`,
  **reviewed**, 3 open questions.
- [Ottoman Empire (to 1886)](polities/ott-1800-1886.md) —
  `OTT-1800-1886`, draft, 4 open questions. Cliopatria polygon.
- [Ottoman Empire (1886–1908)](polities/ott-1886-1908.md) —
  `OTT-1886-1908`, draft, 2 open questions.
- [Ottoman Empire (1908–1912)](polities/ott-1908-1912.md) —
  `OTT-1908-1912`, draft, 3 open questions.

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
  recorded. Five `§`-sections so far (luxembourg, algeria,
  bosnia, libya, tunisia). Cited by:
  [lux-1839-2025](polities/lux-1839-2025.md),
  [ott-1800-1886](polities/ott-1800-1886.md),
  [ott-1886-1908](polities/ott-1886-1908.md),
  [ott-1908-1912](polities/ott-1908-1912.md).

## Aggregates and unions

_(entries that cover multiple polities, e.g. customs unions, colonial
federations — live in `wiki/polities/_aggregates/`)_

## Log and meta

- [log.md](log.md) — append-only decision trail
- [README.md](README.md) — wiki schema and link conventions
- [prompts/ingest.md](prompts/ingest.md), [prompts/query.md](prompts/query.md), [prompts/lint.md](prompts/lint.md)
