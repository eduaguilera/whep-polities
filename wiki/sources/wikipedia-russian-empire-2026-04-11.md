---
source_slug: wikipedia-russian-empire-2026-04-11
title: "Russian Empire (Wikipedia snapshot)"
author: Wikipedia contributors
year: 2026
access_date: 2026-04-11
type: gazetteer
coverage: Russian Empire territorial events, 1800–1917
source_articles:
  - url: https://en.wikipedia.org/wiki/Russian_Empire
    slug: russian-empire-main
    covers: 1721–1917
---

# Russian Empire (Wikipedia snapshot, 2026-04-11)

## Why it was ingested

To back polity pages for the F228 chain representing the Russian
Empire / RSFSR / USSR / Russia entity. The current CSV has five
rows mislabeled "USSR" despite predating 1922 — this source file
provides the dates needed to relabel them correctly and to file
[log proposal-f228-ussr-anachronism]. Also provides the Russian
Empire territorial event dates needed for polity pages covering
1800–1917.

## What it adds

Claims are tagged with the event year. Each is verifiable on the
2026-04-11 Wikipedia *Russian Empire* article.

#### 1856
*Treaty of Paris ends the Crimean War.*

"The treaty mandated 'demilitarization of the Black Sea' and forced Russia to cede southern Bessarabia to Moldova." The Treaty of Paris (30 March 1856) is the real territorial event that marks the start of the Alexander II period. Southern Bessarabia (~10,200 km2) was ceded; the Black Sea demilitarization was lifted in 1871. **The CSV's F228-1800-1856 / F228-1856-1905 split at 1856 is defensible on territorial grounds** (small but real Bessarabian loss).

#### 1858
*Treaty of Aigun.*

"Russia acquired the Amur region from China through this treaty." Major territorial gain in the Far East — establishes Russian control over the left bank of the Amur River.

#### 1860
*Treaty of Peking.*

"China ceded the Ussuri region to Russia, establishing Russian presence on the Pacific coast." Extends the 1858 Aigun gains to the Pacific. Together the 1858 + 1860 treaties added roughly 1 million km2 to the Russian Empire.

#### 1861
*Emancipation of the serfs.*

Alexander II freed "approximately 23 million serfs through imperial decree." Not a territorial event but the defining domestic policy of the early 1856-1905 period.

#### 1865
*Conquest of Tashkent.*

"Russian forces captured the Central Asian city of Tashkent, marking the beginning of systematic conquest of the khanates." Start of the ~20-year Central Asian conquest campaign.

#### 1867
*Alaska sale.*

"Russia sold Alaska to the United States for $7.2 million, relinquishing North American colonial holdings." ~1.5 million km2 transferred. Major territorial event, but it *reduced* the Russian Empire from a transpacific to a Eurasian-only state.

#### 1868
*Conquest of Bukhara.*

"Russian military forces subjugated the Khanate of Bukhara." Bukhara became a Russian protectorate (not directly annexed); the territorial status is complicated.

#### 1873
*Conquest of Khiva.*

"Russian armies conquered the Khanate of Khiva." Khiva became a protectorate.

#### 1875
*Treaty of Saint Petersburg (Sakhalin/Kurils exchange).*

"Russia exchanged the Kuril Islands for control of Sakhalin Island in negotiations with Japan." Russia gained sole control of Sakhalin by giving up the Kuril chain.

#### 1876
*Conquest of Kokand.*

"The Khanate of Kokand fell to Russian forces, completing major Central Asian acquisitions." Annexed directly (unlike Bukhara and Khiva).

#### 1878
*Congress of Berlin.*

"Following Russo-Turkish War victory, the Congress realigned Balkan territories; Russia gained southern Bessarabia recovery but faced constraints on further expansion." The territorial recovery of southern Bessarabia (lost in 1856) is the key Russian gain; Russia lost most of the San Stefano gains it had extracted from the Ottomans in the March 1878 Treaty of San Stefano when the European powers intervened at Berlin.

#### 1884
*Conquest of Merv.*

"Russian forces captured the oasis city of Merv in Turkmenistan, completing Central Asian dominance." End of the Central Asian conquest campaign.

#### 1897
*Imperial Census.*

"Russia conducted its only official census, recording a population of 125,640,021 across the vast empire." Useful for trade-data denominators.

#### 1904-1905
*Russo-Japanese War.*

"Military conflict resulted in Russian defeat and territorial losses in the Far East region." The war ran 8 February 1904 - 5 September 1905.

#### 1905
*Treaty of Portsmouth.*

"Russia ceded southern Sakhalin Island and the Kwantung leased territory to Japan, acknowledging 'recognition of Japanese Korea' as within Japan's sphere." The treaty was signed 5 September 1905 at Portsmouth, New Hampshire. South Sakhalin (~36,000 km2) + Kwantung leased territory (~3,500 km2) transferred to Japan. **This is the territorial event that justifies the WHEP CSV's 1905 split point for the F228 chain.**

#### 1905-revolution
*1905 Revolution.*

"Mass unrest culminated in the February Revolution framework, leading Tsar Nicholas II to authorize creation of the 'State Duma', though maintaining substantial autocratic authority." Not a territorial event but the defining political moment of 1905. The October Manifesto (30 October 1905) established the State Duma. The Russian Empire continued as a state until February 1917, but internally it became a constitutional monarchy after 1905.

#### ussr-founded
*USSR NOT YET EXISTING in any year covered by this article.*

The USSR was not created until **30 December 1922**, when the Treaty on the Creation of the USSR was signed by the RSFSR, the Ukrainian SSR, the Byelorussian SSR, and the Transcaucasian SFSR. The entity sequence from 1917 to 1922 is:

- February 1917 - October 1917: **Russian Republic** (Provisional Government)
- October 1917 - 30 December 1922: **Russian SFSR** (RSFSR), as the dominant but not sole Soviet republic during the Civil War period
- 30 December 1922 onward: **USSR**

**This is the canonical citation target for [log proposal-f228-ussr-anachronism].** Any WHEP row labeled "USSR" with a start or end year before 1922 is anachronistic relative to this date.

## Known limitations

1. **Wikipedia is a tertiary source.** For archival-grade dating
   of 19th-century treaties a diplomatic history would be
   stronger. The dates here are from the Wikipedia *Russian
   Empire* main article (one article, one access) and should be
   cross-checked against Biger's RUSSIA entry in a later
   ingest — see [oq-biger-russia] on the f228-1856-1905 polity
   page.
2. **Territorial gains from Central Asian conquests are not
   quantified here.** The article gives years for Tashkent,
   Bukhara, Khiva, Kokand, and Merv but not square-kilometer
   totals. The overall Russian Empire area grew from roughly
   17.4 million km² in 1800 (per the CSV notes field on
   F228-1800-1856) to roughly 22 million km² by 1900 (per the
   CSV notes field on F228-1856-1905), so approximately 4–5
   million km² was added during this period, most of it in
   Central Asia and the Far East, minus the 1.5 million km²
   Alaska sale. Exact apportionment would need a second source.
3. **The article's treatment of Bukhara and Khiva as
   "conquered" conflates annexation with protectorate
   status.** Both became Russian protectorates with nominal
   local rulers rather than directly annexed provinces — the
   practical trade regime was Russian but the legal status was
   ambiguous until the 1920s when the Bolsheviks abolished the
   khanates.
4. **1867 Alaska sale is sometimes treated as a "voluntary
   transfer"** in Russian historiography rather than a loss,
   since Russia initiated the sale. Under WHEP's
   territorial-economic definition it is a polity-territory
   reduction either way.

<!-- Reference-style link definitions. Sorted. -->

[log proposal-f228-ussr-anachronism]: ../log.md#proposal-f228-ussr-anachronism
[oq-biger-russia]: ../polities/f228-1856-1905.md#oq-biger-russia
