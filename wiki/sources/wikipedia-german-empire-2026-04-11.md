---
source_slug: wikipedia-german-empire-2026-04-11
title: "German Empire (Wikipedia snapshot)"
author: Wikipedia contributors
year: 2026
access_date: 2026-04-11
type: gazetteer
coverage: Prussia and the German Empire, 1800–1919
source_articles:
  - url: https://en.wikipedia.org/wiki/German_Empire
    slug: german-empire-main
    covers: 1871–1918 (plus Prussian predecessor content)
---

# German Empire (Wikipedia snapshot, 2026-04-11)

## Why it was ingested

To back the German chain polity pages (DEU-*, GER-*, potentially
PRU-* if added) under the autonomous European-empires research
pass. The WHEP CSV has a 120-year single row DEU-1800-1919 with no
mid-row events — this source supplies the dated territorial and
political events needed for the critical-stance audit and for the
polity page narrative.

## What it adds

#### 1834
*Zollverein customs union established.*

The Prussian-led customs union that preceded the German Empire. Foundational to the "Germany/Zollverein" CSV framing (see [log proposal-deu-ger-chain-audit](../log.md#proposal-deu-ger-chain-audit)).

#### 1864
*Second Schleswig War.*

"The Second Schleswig War against Denmark in 1864." Prussia + Austria defeated Denmark, resulting in the joint administration of Schleswig (Prussia) and Holstein (Austria) per the Gastein Convention of 1865.

#### 1866
*Austro-Prussian War and German Confederation dissolution.*

"The Austro-Prussian War in 1866." The war ended with the Peace of Prague (23 August 1866) — the German Confederation was dissolved and the northern German states were reorganized under Prussian leadership. Real territorial event: Prussia annexed Hanover, Hesse-Kassel, Nassau, Frankfurt, and Schleswig-Holstein. Counterparted in [biger-1995 §austria](biger-1995.md#austria) (p.50), which treats 1866 as "the real territorial-political turning point".

#### 1867
*North German Confederation founded.*

"North German Confederation, comprising the 22 states north of the Main." Prussian-led political union that replaced the dissolved German Confederation for northern Germany. The southern German states (Bavaria, Wurttemberg, Baden, Hesse-Darmstadt) remained outside this confederation until the 1871 unification.

#### 1870-1871
*Franco-Prussian War.*

"The Franco-Prussian War of 1870 overwhelmed the remaining opposition to unified Germany." The war started 19 July 1870 and ended with the Treaty of Frankfurt on 10 May 1871. France ceded Alsace and most of Lorraine to the new German Empire.

#### 1871-01-18
*German Empire proclaimed at Versailles.*

"William was proclaimed Emperor in the Hall of Mirrors at the Palace of Versailles." The German Empire was proclaimed on 18 January 1871 in the Hall of Mirrors at Versailles, during the final stage of the Franco-Prussian War. The empire combined the North German Confederation + the four southern German states (Bavaria, Wurttemberg, Baden, Hesse-Darmstadt) + the soon-to-be-annexed Alsace-Lorraine. **This is the single biggest territorial-economic consolidation in 19th-century Europe and a candidate mid-row split point for the WHEP CSV's DEU-1800-1919 row.**

#### 1871-04-16
*Imperial Constitution.*

"The second German Constitution...was substantially based upon Bismarck's North German Constitution." Formalized the Empire's political structure.

#### 1871-alsace-lorraine
*Annexation of Alsace-Lorraine.*

The Treaty of Frankfurt (10 May 1871) transferred Alsace and most of Lorraine from France to the new German Empire. The territory was organized as the "Imperial Territory of Alsace-Lorraine" under direct imperial administration rather than as a constituent state. ~14,500 km2 transferred. Load-bearing for WHEP: the French side ([fra-1800-1919](../polities/fra-1800-1919.md), not yet a polity page) should record the matching territorial loss.

#### 1884-1885
*Berlin Conference and colonial acquisitions.*

The "Berlin Conference" authorized the European partition of Africa and was held in Berlin 15 November 1884 - 26 February 1885. Germany acquired several African and Pacific colonies in this period: German Southwest Africa, German East Africa, Cameroon, Togoland, German New Guinea. These are tracked separately as WHEP colonial rows (e.g. GSW, GEA) and are not counted as part of the metropolitan DEU row's territorial extent.

#### 1914-07-28
*Entry into World War I.*

"World War I began on 28 July 1914." Germany mobilized 1 August 1914 and declared war on Russia the same day. Not a territorial event itself but the trigger for the war that ended the Empire.

#### 1918-11-09
*Abdication and republic proclaimed.*

"Abdication of Wilhelm II and republic proclaimed: 9 November 1918." The German Empire formally ceased to exist with the abdication of Kaiser Wilhelm II. The Weimar Republic was proclaimed in Berlin on the same day.

#### 1918-11-11
*Armistice of Compiegne.*

Not directly quoted from the Wikipedia article excerpt. The armistice ending WWI was signed at 05:00 on 11 November 1918 and took effect at 11:00. Germany's military collapse made the armistice and the subsequent peace treaty possible.

#### 1919-06-28
*Treaty of Versailles.*

The Treaty of Versailles was signed on 28 June 1919 and took effect on 10 January 1920. Germany lost Alsace-Lorraine (back to France), Eupen-Malmedy (to Belgium), Northern Schleswig (to Denmark), West Prussia and Posen (to Poland, creating the "Polish Corridor"), Upper Silesia (partially, to Poland), Memel Territory (to Lithuania eventually), Saar Basin (under League of Nations administration for 15 years), and its entire colonial empire (to the Allies as League mandates). Total metropolitan loss: ~65,000 km2. The WHEP CSV uses **1919** as the end of the DEU-1800-1919 row, corresponding to this treaty rather than to the 1918-11-09 abdication.

## Known limitations

1. **Wikipedia is a tertiary source.** A diplomatic history of
   Bismarckian Germany would be stronger. The article's treatment
   of 1871 unification is solid but its treatment of the 1866
   Prussian annexations (Hanover, Hesse-Kassel, Nassau, Frankfurt)
   is cursory.
2. **Article date boundaries are imperfect.** The article's date
   range is "1871–1918" but the Wikipedia snapshot excerpt I read
   implies it covers some pre-1871 Prussian background without
   being explicit. The §1834 Zollverein date should be
   cross-checked against a dedicated Zollverein or Prussian
   history source.
3. **Biger was not yet read** for the Germany entry. A future
   iteration should add a `§germany` section to
   `wiki/sources/biger-1995.md` covering the GERMANY main entry
   and the GERMANY–* boundary subsections, especially
   GERMANY–FRANCE (for Alsace-Lorraine), GERMANY–POLAND (for the
   1919 Polish Corridor), and GERMANY–DENMARK (for Schleswig).
4. **No specific km² figures** for the Prussian territorial gains
   in 1866 (annexation of Hanover etc.) or the 1919 losses
   (Alsace-Lorraine etc.). Flagged on the polity page as open
   questions.