#!/usr/bin/env python3
"""Compare each polygon against the area the SOURCE stated for that reporting unit.

Every other area check in this repo compares our polygon to another GIS product, or to a
family median. Both can be consistently wrong in the same direction, because GIS products share
conventions. This one compares against `data/final/source_stated_areas.csv` -- 2,002 statements
from six IIA yearbook editions (1909-1938) in which each reporting unit is given its own area in
km2 by the statistical authority that published the data.

WHY THAT IS A DIFFERENT QUESTION. Polities exist to carry data rows, so the territorial basis
that matters is the one the source used. Issue 159 asks whether polygons should follow CLAIMED
territory (CShapes) or EFFECTIVE CONTROL (Cliopatria, paine-2024) -- a question with no answer
in the abstract, and 29 families where the two conventions meet and publish the difference as a
territorial event. The source's own figure decides it, per row, with evidence.

Tunisia is the case that made this worth building, AND THE CASE THAT SHOWS WHY ONE SOURCE IS NOT
ENOUGH. On IIA alone the reading was "both polygons are wrong":

    IIA stated                    125,130 km2      six editions 1911-1937, unchanged
    TUN-1800-1881  paine-2024      43,752 km2      0.35x of IIA
    TUN-1881-2025  cshapes-2.0    155,482 km2      1.24x of IIA

Adding FAO reversed half of that conclusion. FAO states 155,830 km2, which matches CShapes to
0.2%, and across every polity where both sources speak they agree closely -- Chile 741,770 vs
741,767, Libya 1,759,500 vs 1,759,540, Yugoslavia 1.03x, French Togoland 1.06x. Tunisia is the
ONLY 20%+ disagreement between them.

So TUN-1881-2025 is right and IIA is the outlier; only paine-2024's 43,752 is wrong. The 3.55x
step at 1881 is still an artifact, but of ONE bad polygon rather than of two conventions meeting.
Two sources agreeing to four digits while a third differs by a quarter is how you tell an outlier
from a convention -- and with IIA alone I drew the wrong conclusion and wrote it into a merged PR.

BUT AGREEMENT BETWEEN THESE TWO SOURCES IS NOT ALWAYS INDEPENDENT, and Libya is the case that
shows it (issue 196). FAO 1952's 1,759,500 and IIA 1938's 1,759,540 agree to 0.002% because they
are the same Italian colonial figure, first published in the IIA 1938 edition for a Libya whose
southern boundary was the never-ratified 1935 Laval-Mussolini (Aouzou) line. The IIA 1932 and 1933
editions give 1,638,000 for the same country. Three modern boundary products agree with the 1932
figure and disagree with the 1938 one by 8.2%, so here the two "agreeing" sources are both the
outlier. Cross-source agreement bounds transcription error, not scope error; only a source with a
different provenance bounds that.

WHAT THIS CHECK IS NOT FOR. The yearbooks are not more accurate than modern GIS about
coastlines, and they carry their own errors: IIA gives Monaco as 21 km2 in five editions and 149
in two, against an actual ~2 km2. What a stated area IS authoritative about is SCOPE -- whether
the Sahara was in Tunisia, whether Patagonia was in Chile -- which is exactly what a per-km2
denominator has to match. So the threshold is deliberately loose (25%): this is a scope
detector, not a precision check. `validate_polygons` owns precision.

On the first run, of 228 (polity, year) pairs that resolve to a stated area:

    within 10%                                 177
    within 25%                                 210
    polygon more than 25% LARGER than stated     0
    polygon more than 25% SMALLER than stated   18

Zero overstatements is itself worth recording: whatever else is wrong with these polygons, they
are not systematically bigger than the territories the sources were describing.

Comparison is against the RANGE of everything the source ever stated for a polity, not a single
figure, because the source revises itself: 61 of 159 repeated (label, year) pairs disagree across
editions, up to 5.45x. See the comment in main().

Bidirectional: a new divergence fails, and a baselined one that comes back inside the range must
be removed.
"""
from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATED_PATH = os.path.join(REPO, "data/final/source_stated_areas.csv")
GPKG_PATH = os.path.join(REPO, "data/final/polities_database.gpkg")
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
LEXICON_PATH = os.path.join(REPO, "data/final/source_label_lexicon.csv")

TOLERANCE = 0.25  # scope detector, not a precision check

# (polity_code, source) -> why the polygon and the stated area disagree by more than 25%.
# Being here means the divergence is understood, NOT that it is acceptable.
BASELINE = {
    # MCO-1800-2025 was baselined here and the gate REMOVED IT, which is the design working.
    # IIA states Monaco as 21 km2 in seven editions and 149 in two, for a territory that has
    # never exceeded ~2 -- and FAO states the correct 2. Once each source got ONE VOTE instead of
    # one per edition, FAO's value survived, the accepted band became 2-21, and our 2 km2 polygon
    # stopped diverging. Keep the reasoning: Monaco is the control case for this whole check.
    # A stated area can be a transcription or unit error, so a divergence is a question, not a
    # verdict -- and a majority of editions agreeing proves nothing, because yearbooks reprint
    # each other's area tables.
    ("PRY-1870-1932", "iia"):
        "IIA states 450,000 km2 for 1913 against our 293,549 (0.65x). Modern Paraguay is "
        "406,752, so OUR POLYGON IS 28% BELOW even the present-day country, which makes this "
        "ours rather than the source's. Pre-Chaco-War Paraguay also claimed territory it did "
        "not hold, so part of the gap is the claimed-versus-controlled question of issue 159. "
        "Tracked with the long-single-vintage rows in issue 22, which names Paraguay.",
    # --- FAO additions, 2026-08-05. Each says WHICH SIDE is wrong, because the answer differs.
    # --- surfaced 2026-08-05 when the French lexicon took coverage from 41 polities to 203.
    # Each says which side is wrong. THIRTEEN of these are scope or vintage differences where our
    # polygon is defensible; TWO are apparent polygon defects and are filed rather than accepted.
    # BSS-1884-1960/iia and ITS-1908-1960/iia were baselined here and BOTH WERE REMOVED on
    # 2026-08-18, when iia's `somalia` label was rerouted from BSS-1884-1960 to ITS-1908-1960.
    # This gate is what corroborated that reroute, and it also corrects the reasoning the BSS entry
    # used to carry. That entry read IIA's ~497,500 km2 as "roughly Italian + British Somaliland
    # together"; it is not. IIA states BRITISH Somaliland separately and consistently as
    # `SOMALIE BRITANNIQUE` at 176,117 / 176,000 km2 in every edition from 1909 to 1938, while its
    # unqualified `SOMALIE` / `SOMALIE ITALIENNE` rises 357,000 (1909) -> 400,000 -> 490,000 ->
    # 495,000 -> 500,000 (1933) as Jubaland transfers in. So the stated area under the label that
    # actually carried the data is ITALIAN Somaliland alone: 500,000 against ITS's polygon of
    # 464,286 is 7.7% out and passes, where against BSS's 171,633 it was 2.9x. Combined Somaliland
    # would be ~678,000, which the source never states. The old entry's CONCLUSION (ours is right,
    # the label reaches the wrong extent) was correct; its premise was not, and the premise is the
    # part a reader would have reused.
    ("CHN-1921-1932", "iia"):
        "SCOPE. IIA states 11,080,000 km2 for China against our 7,496,467. China's own claimed "
        "area including Outer Mongolia and Tibet was routinely given as ~11m in this period; the "
        "1938 edition drops to 9,870,000 once Mongolia is excluded. Our polygon is effective "
        "Republican control, which is the right basis for production data.",
    ("CHN-1932-1945", "iia"): "same as CHN-1921-1932, against the 1932 edition's 11,084,000.",
    ("DZA-1902-1919", "iia"):
        "SCOPE, and the more interesting direction. IIA states 575,511 km2 -- NORTHERN Algeria, "
        "the three civil departments -- while our polygon is 2,442,844 including the Southern "
        "Territories. Both are 'Algeria'; only one is the basis French agricultural statistics "
        "were collected on. A per-km2 denominator using our polygon understates by 4.2x for any "
        "series the yearbook drew from the civil departments.",
    ("ETH-1907-1936", "iia"):
        "OURS IS RIGHT. Ethiopia is ~1,104,300 km2 and our polygon is 1,127,533. IIA's 900,000 "
        "is a pre-survey estimate from before the interior was mapped.",
    ("GBR-1800-1921", "iia"):
        "THE LABEL IS NARROWER THAN THE POLITY. IIA's `royaume uni` states 230,616 km2, which is "
        "GREAT BRITAIN without Ireland. Our 313,550 includes all of Ireland, which is correct for "
        "the United Kingdom of 1800-1921. Ours is right; the label needs a separate GB row if any "
        "data actually arrives under it.",
    ("GKM-1884-1912", "iia"):
        "VINTAGE. IIA states 790,000 km2, which is German Kamerun AFTER the 1911 Neukamerun "
        "cession from French Equatorial Africa; our 510,422 is the pre-1911 colony. The row spans "
        "1884-1912, so both are inside it and the polygon represents most of the span.",
    ("GRC-1881-1913", "iia"):
        "PERIOD MISMATCH IN THE SOURCE, not in us. IIA's 1925 edition states 119,050 km2 under "
        "the data year 1913 -- post-Balkan-Wars Greece -- while this row ends in 1913 and covers "
        "the 63,211 km2 kingdom. Our 63,612 is right for the row. The yearbook is labelling a "
        "1913 column with the territory Greece held after the treaties of that year.",
    ("IRQ-1921-1932", "iia"):
        "OURS IS RIGHT. Iraq is 438,317 km2 and our polygon is 436,200. IIA's 336,379 predates "
        "the 1926 settlement of the Mosul vilayet boundary with Turkey.",
    ("MAN-1932-1945", "iia"):
        "SCOPE. IIA states 1,303,143 km2 for Manchukuo, which includes Jehol and the Inner "
        "Mongolian leagues; our 791,708 is the three north-eastern provinces. build_man_1932_1945() "
        "documents that choice, and this is the first external evidence of what it costs.",
    # GRL-1800-2025 was baselined here and the gate removed it: the digit screen drops IIA's
    # Greenland statements before they reach the comparison. Keep the reasoning, because it is the
    # counter-example to the screen's own premise. IIA states 88,100 km2 in the early editions and
    # 313,000 / 341,700 later, for an island of 2,166,000. Those are ICE-FREE area estimates,
    # growing as the coast was surveyed -- a DIFFERENT QUANTITY, not a lost digit. A ~10x outlier
    # can be either, and the screen cannot tell them apart; it only stops the outlier widening the
    # accepted band, which is right in both cases but for different reasons.
    ("F249-1918-1990", "fao"):
        "SCOPE MISMATCH, not an error. FAO's `Yemen` for 1947 is 195,000 km2 -- NORTH Yemen "
        "alone -- while F249-1918-1990 is the combined YAR + PDR reporting unit at 423,668. The "
        "routing question (should a pre-1990 `Yemen` label reach the combined row or a "
        "North-Yemen one?) is the pre-1990 Yemen gap already known from the production/trade "
        "review; it is not answerable by area.",
    ("RYU-1945-1972", "fao"):
        "SCOPE MISMATCH, explained. FAO states 3,410 km2 against our 2,270. The US-administered "
        "Ryukyus included Amami Oshima (~1,200 km2) until it returned to Japan in 1953, and "
        "2,270 + 1,200 = 3,470, within 2% of the stated figure. Our polygon is Okinawa "
        "Prefecture, so the gap is Amami and the divergence is real rather than wrong.",
    ("SAU-1924-2025", "fao"):
        "GENUINE HISTORICAL UNCERTAINTY. FAO states 1,546,000 km2 against our 1,954,454 and a "
        "modern 2,149,690. Saudi Arabia's southern and eastern desert boundaries were not "
        "settled until the 1990s, so contemporary figures varied by hundreds of thousands of "
        "km2. Neither side is wrong; the territory was not agreed.",
    ("QAT-1800-2025", "fao"):
        "GENUINE HISTORICAL UNCERTAINTY, same shape. FAO states 22,000 km2 against our 11,062 "
        "and a modern 11,586. Pre-settlement figures for Qatar commonly included disputed zones.",
    ("VNM-1887-1954", "fao"):
        "OUR POLYGON IS CORROBORATED BY THE OTHER SOURCE, so FAO is the narrow one here. FAO "
        "states 225,000 km2 for `Indochina Viet Nam` in 1951 against our 324,094. But IIA lists "
        "the three constituent protectorates separately -- Tonkin 115,700 + Annam 147,600 + "
        "Cochinchine 64,700 = 328,000 -- which is within 1.2% of our polygon. 1951 sits in the "
        "middle of the First Indochina War, with the State of Vietnam administering part of the "
        "territory and the Viet Minh the rest, so a survey covering 225,000 km2 is plausible as "
        "the area actually enumerated. Cross-checking two sources is what makes this readable as "
        "a coverage difference rather than a polygon error.",
    ("EGY-1899-1925", "iia"):
        "SCOPE, verified by containment rather than assumed. Our polygon is 1,517,144 km2 against "
        "IIA's 1,027,996 and a modern Egypt of 1,001,450 -- but Cairo, Aswan and Sinai are inside "
        "it while Wadi Halfa, Khartoum and Port Sudan are OUTSIDE, so it is not silently carrying "
        "Sudan. The extra ~500,000 km2 is the Libyan Desert: Egypt's western boundary with "
        "Cyrenaica was undefined until 1925 and CShapes encodes the maximal claim. IIA states the "
        "administered territory, which is the basis its agricultural figures were collected on.",
    ("SMO-1912-1956", "iia"):
        "SCOPE, and OUR POLYGON IS ARGUABLY THE MORE COMPLETE. 52,792 km2 in TWO parts, bounds "
        "27.67-35.92N: the northern zone (Tetouan and Nador inside) plus the Tarfaya strip in the "
        "far southwest. Spanish Morocco did include that Southern Protectorate, so the union is "
        "right. IIA's 21,800 is the northern zone alone, matching the ~20,948 km2 usually quoted "
        "for it. Anyone using Spanish Morocco as a denominator needs to know which of the two the "
        "numerator came from.",
    ("SLV-1821-2025", "fao"):
        "EXTRACTION DAMAGE, visible in the label itself: the row is `EI Salvador`, an OCR misread "
        "of `El`. The stated 34,130 km2 is 62% above El Salvador's 21,041, so the number is as "
        "suspect as the name. Belongs to the digitisation review, not to this repo.",
    # JAM-1800-2025 / fao was baselined here as "THE LABEL IS NOT THE POLITY ... IIA's equivalent
    # sub-label states 231-271 km2 -- BOTH sources give a small figure, so this is a sub-unit
    # inside a BWI section rather than the island. The alias routing it to JAM-1800-2025 is what
    # needs revisiting, not the polygon." THAT WAS WRONG, and issue 111 is why it was re-measured.
    #
    # The 231-271 km2 belongs to `INDES OCCIDENTALES BRITANNIQUES: JAMAIQUE: CAIMANS` -- the
    # CAYMAN ISLANDS, whose own polity is CYM-1800-2025 at 281 km2 and whose FAO 1952 sibling row
    # states 240. It is a different reporting unit that happens to be indented under Jamaica.
    # IIA's actual `JAMAIQUE` line states 10,880 / 10,896 / 11,525 / 11,526 km2 across its six
    # editions, i.e. the ISLAND, within 0.2-4.9% of our 11,001 polygon and of the modern 10,991.
    # The lexicon now maps that label (and the Bahamas one), so IIA votes here and the second
    # source is no longer invisible; the accepted band widens to 1,420-11,525 and our polygon sits
    # inside it, which is why this entry is gone rather than reworded.
    #
    # So FAO 1952's 1,420 is a TRANSCRIPTION ERROR, not a narrower scope, and it is not the x10
    # kind: 14,200 would be 1.29x of Jamaica while 11,420 -- a DROPPED LEADING 1 -- is 1.039x.
    # Its BWI neighbours in the same table are right (Barbados 450 vs our 435, 1.03x; Cayman
    # Islands 240 vs our 281, 0.86x), which is what makes it a slip in one cell rather than a
    # different territorial basis for the block. Logged as a source error, with the sibling
    # `British West Indies Bahamas` 1,400-for-13,880 (a clean x10), in
    # pipelines/polity-autoimprove/state/data_errors.csv; the figure is NOT corrected here,
    # because this repo records what the yearbook printed.
    ("NFK-1914-2025", "fao"):
        "A UNIT ERROR IN THE SOURCE. FAO states 350 km2 for Norfolk Island, which is 35 km2 -- "
        "exactly 10x, i.e. a figure in km2 recorded under the `1000 hectares` heading. Our 37 is "
        "right.",
    # ("SMR-1800-2025", "fao") REMOVED 2026-08-20. The divergence was real and its reason was
    # right -- FAO's 1,000-hectare grid can only record San Marino's 61 km2 as 100 -- but it is no
    # longer the polity's stated figure. Retargeting the `saint marin` lexicon entry brought IIA's
    # nine statements in, and IIA states 61 km2 against our 61 (1.003x), so the polity-level figure
    # now agrees and this entry baselines a divergence that no longer exists. The FAO row itself is
    # unchanged and still reads 0.612x with its note; what changed is that a finer source outvotes it.
    ("JPN-1895-1945", "iia"):
        "SCOPE, AND IT CORROBORATES A CONVENTION FROM A NEW DIRECTION. IIA states 382,415 km2, "
        "which is METROPOLITAN Japan (Japan proper is about 382,000 km2). Our polygon is 626,507 "
        "km2, the Japanese Empire including Korea and Formosa. The convention at (\"iia\", "
        "\"japan\", \"*\") already records that this source's `japan` label reports metropolitan "
        "Japan exclusive of Korea and Formosa, established from PRODUCTION arithmetic -- japan falls "
        "below south korea in 151 of 264 shared cells, which inclusion cannot produce. This is the "
        "same conclusion reached independently from the AREA side, and the two agree to within a "
        "percent on what the metropolitan figure should be. Neither number is an error: the polygon "
        "is right for the polity and the stated area is right for the reporting unit, which is "
        "exactly the basis mismatch this file exists to publish. Surfaced 2026-08-20 by adding the "
        "`japon` lexicon entry (issue 195); note that `japan` itself does not resolve by name at all "
        "and is routed by alias, so the stated-area side had no entry until now.",
    ("NFL-1907-1949", "iia"):
        "A REAL SCOPE DIFFERENCE, AND THE MOST CONSEQUENTIAL ONE THIS FILE CARRIES AFTER ALGERIA. "
        "IIA states 110,679 km2, which is the ISLAND of Newfoundland (about 111,000 km2). Our "
        "polygon is 398,115 km2, which is the island PLUS LABRADOR (together about 405,000 km2). "
        "Both are correct for what they describe -- the Dominion did administer Labrador -- so "
        "neither figure is an error and the polygon is not being changed. But a per-km2 intensity "
        "computed from a yearbook numerator over this polygon understates by 3.6x, with nothing "
        "else in the repo to warn of it. Surfaced on 2026-08-20 when the `terre neuve` lexicon "
        "entry was retargeted from `Newfoundland`, which matches no polity_name, to `Dominion of "
        "Newfoundland` (issue 195).",
    ("MAC-1800-2025", "iia"):
        "THE TERRITORY GREW, AND BOTH FIGURES ARE RIGHT FOR THEIR DATE. IIA states 14 km2 for "
        "Macao; our polygon is 34 km2. Macao has roughly doubled by land reclamation across the "
        "20th century, so a 1911-1937 statement of 14 km2 and a modern outline of 34 km2 are both "
        "accurate and the ratio is a vintage difference rather than a scope one. This is the "
        "issue 22 shape -- one long row against a territory that moved -- at a magnitude where it "
        "cannot be checked any other way, since anything under a few hundred km2 sits below this "
        "source's resolution. Surfaced on 2026-08-20 by the `macao` lexicon retarget (issue 195).",
    ("PRY-1932-1938", "iia"):
        "same polygon as PRY-1870-1932 (293,549) against a stated 457,872 for 1932/1933/1937. "
        "The Chaco War is fought across this row's span, so the stated figure is a claim under "
        "active dispute -- but the polygon does not move at all, which is the issue 22 problem.",
    ("JAM-1800-2025", "fao"):
        "A TRANSCRIPTION ERROR IN THIS SOURCE, and NOT a x10 one. FAO 1952's `British West "
        "Indies Jamaica` states 142 thousand ha = 1,420 km2 for an island of 10,991. A decimal "
        "shift gives 14,200 (1.29x, too large); restoring a dropped leading digit gives 11,420 "
        "(1.039x). IIA's own `JAMAIQUE` line states 10,880-11,526 across six editions and our "
        "polygon is 11,001, so the polygon and the alias are right and this one figure is wrong. "
        "Its BWI neighbours in the same FAO table are right (Barbados 450 vs 435; Cayman Islands "
        "240 vs 281), which is what makes it one bad cell rather than a narrower basis for the "
        "block. DO NOT use 1,420 km2 as a denominator for Jamaican FAO 1952 rows. Logged with "
        "the sibling Bahamas error in pipelines/polity-autoimprove/state/data_errors.csv; the "
        "figure is not corrected, because this repo carries what the yearbook printed.",
}

# (polity_code, source) -> why ONE SOURCE's figure is wrong for a polity the gate does NOT fail on.
#
# BASELINE cannot hold these, because it is bidirectional: an entry there for a polity now inside
# the accepted band is itself a failure ("remove its entry"). But a polity can be accepted on one
# source's figure while the OTHER source's is badly wrong, and that is exactly the case a per-km2
# consumer has to be warned about -- it divides by the figure IT holds, not by the accepted band.
# `write_stated_area_basis.py` publishes these into the `note` column so the warning survives
# outside this file. Nothing here affects pass/fail.
SOURCE_NOTES = {
    # The JAM-1800-2025/fao note that lived here moved to BASELINE on 2026-08-17: divergence is
    # computed PER (polity, source), so IIA voting 10,880-11,526 does not bring JAM inside the band
    # FAO states, and only BASELINE suppresses a failure. write_stated_area_basis.py reads BOTH
    # dicts, so the published warning survives the move.
    #
    # The five entries below were added on 2026-08-20. None suppresses a failure -- the gate is
    # already green on all of them -- but each was flagged `review` in
    # source_stated_area_basis.csv with NO published reason, so a reader met a 10x ratio and an
    # empty note. That is the shape this file warns about elsewhere: an unexplained flag reads as
    # either an error or an oversight, and there is no way to tell which.
    # SIX SINGLE-EDITION AREA OUTLIERS, added 2026-08-20. Each was surfaced by
    # 34_area_revision_boundaries.py as a >=50% revision that ONE POLITY SPANS -- i.e. a candidate
    # missing period boundary. Each is instead a bad figure in one edition, and the test is the one
    # this file's own failure message prescribes: check which side is wrong first. In every case the
    # polygon sits within 0-11% of one stated figure and 36-628% from the other, and the remaining
    # editions agree with the figure the polygon backs. Recording them here removes them from that
    # screen, which is the point of its exclusion: a diagnosed source defect leaves by being diagnosed.
    ("EST-1918-1940", "iia"):
        "A SINGLE-EDITION OUTLIER. The 1909 edition states 6,775 km2 for `ESTHONIE`; the 1925 edition "
        "states 47,549, and our polygon is 49,303 -- 4% from the later figure and 628% from the "
        "earlier. 47,549 km2 is interwar Estonia including Petserimaa and Narva-taguse, so the 1925 "
        "figure is right and the 1909 one is wrong by a factor of seven. Not a periodisation gap.",
    ("FRS-1884-1977", "iia"):
        "A SINGLE-EDITION OUTLIER. `CÔTE DES SOMALIS` reads 120,000 km2 in the 1909 edition (applied to "
        "1911 and 1921) and 21,963 in 1937; our polygon is 21,481, i.e. 2% from the later figure and "
        "82% from the earlier. French Somaliland was about 23,000 km2, so 120,000 is the error.",
    ("LTU-1918-1940", "iia"):
        "A SINGLE-EDITION OUTLIER, and the later editions are unanimous. `LITHUANIE` reads 150,000 km2 "
        "in the 1909 edition and then 55,658 / 55,670 / 55,670 / 55,670 across 1925-1937; our polygon "
        "is 55,904, within 0% of those. Interwar Lithuania was about 55,700 km2 without Vilnius, so "
        "150,000 is the error and four editions agree against it.",
    ("BSS-1884-1960", "iia"):
        "A SINGLE-EDITION OUTLIER, in the other direction. `SOMALIE BRITANNIQUE` reads 176,000 km2 in "
        "1913 and 86,000 in 1925; our polygon is 171,627, which is 2% from the EARLIER figure and 100% "
        "from the later. British Somaliland was about 176,000 km2, so here it is the 1925 edition that "
        "is wrong -- which is why this class cannot be handled by preferring later editions.",
    ("ALB-1913-2025", "iia"):
        "TWO EDITIONS CARRY A FIGURE 60% TOO LARGE, and they are not consecutive. `ALBANIE` reads "
        "45,000 km2 at 1913, 28,500 at 1921, 45,000 again at 1925, then 27,538 for 1932/1933/1937; our "
        "polygon is 28,624. Albania is about 28,750 km2, so the ~28,000 figures are right and 45,000 is "
        "wrong -- appearing, disappearing and reappearing, which is the product-switch shape "
        "(21_item_product_switches.py) applied to an area column rather than a single bad edition.",
    ("ECU-1800-1942", "iia"):
        "A CLAIM, NOT A DEFECT AND NOT A BOUNDARY CHANGE. `EQUATEUR` reads 307,243 km2 in four "
        "editions, 451,180 in 1932, 306,644 in 1933 and 714,860 in 1937; our polygon is 341,715, "
        "closest to the 307,243 cluster. 714,860 km2 is Ecuador's CLAIMED Amazon territory before the "
        "1942 Rio Protocol, and 451,180 is an intermediate claim -- so the source is tracking what "
        "Ecuador asserted rather than what it administered. Neither figure is an error in the source "
        "and neither implies a missing period boundary; the polity's own span ends at 1942, which is "
        "the year the claim was settled.",
    ("MCO-1800-2025", "iia"):
        "A LOST DECIMAL SEPARATOR, TWICE, AT TWO DIFFERENT MAGNITUDES. IIA states 21 km2 for "
        "Monaco in 1911-1932 and 149 km2 in 1933/1937; Monaco is about 2.0 km2 today and was "
        "about 1.5 km2 before its land reclamation. So 21 is 2.1 and 149 is 1.49, each with the "
        "separator dropped -- and the pair is self-corroborating, because two independent "
        "misreadings of one small number would not both land on Monaco's actual size in different "
        "eras. Our 2 km2 is right. Nothing under a few hundred km2 can be checked against this "
        "source without this hazard.",
    ("GIB-1800-2025", "fao"):
        "THE SAME UNIT ERROR AS NFK-1914-2025, WHICH IS ALREADY BASELINED. FAO states 60 km2 for "
        "Gibraltar, which is 6.8 km2 -- a figure recorded under the `1000 hectares` heading and "
        "read as km2, i.e. 6.8 thousand hectares instead of 0.68. Norfolk Island is the identical "
        "shape (350 stated, 35 actual), so this is a systematic hazard of that table at small "
        "magnitudes rather than a one-off slip. Our 7 is right.",
    ("SLV-1821-2025", "iia"):
        "A STALE SOURCE FIGURE, NOT A TRANSCRIPTION ERROR, AND THE STABILITY IS THE EVIDENCE. IIA "
        "states 34,126 km2 for `SAN SALVADOR` in EVERY edition -- 1913, 1925, 1929, 1932, 1933 and "
        "1937, byte-identical -- against El Salvador's 21,041 km2. A digit slip would not reproduce "
        "across six editions; a figure the yearbook believed and never revised would. 34,126 is a "
        "pre-boundary-survey estimate of the kind older gazetteers carried, so this is a vintage "
        "disagreement about the same territory rather than a different scope. Our 20,558 is right. "
        "Recorded because a 1.62x ratio with no note reads as a possible routing error, and it is "
        "not one.",
    ("GRL-1800-2025", "iia"):
        "PROBABLY A SCOPE STATEMENT, AND DELIBERATELY HEDGED. IIA states 88,100 km2 for Greenland "
        "in 1911-1925, then 313,000 in 1932/1933 and 341,700 in 1937, against a total area of "
        "2,166,000 km2. No unit or digit error explains three different values, and the later two "
        "sit near Greenland's ICE-FREE area (roughly 410,000 km2), which is the quantity an "
        "agricultural yearbook would care about. So the likeliest reading is that the source states "
        "usable rather than total land and revised its estimate twice. I have NOT confirmed that "
        "against the volumes, so it is not baselined as understood -- the 1909-edition 88,100 is "
        "additionally dropped by this gate's own digit-error screen as ~10x from the polity median.",
    ("SMR-1800-2025", "fao"):
        "ROUNDING AT LOW MAGNITUDE. FAO's smallest unit is 1,000 hectares = 10 km2, so San "
        "Marino's 61 km2 can only be recorded as 6 or 10 -- it is recorded as 10, giving 100. Our "
        "61 is right. This lived in BASELINE until 2026-08-20, when retargeting the `saint marin` "
        "lexicon entry brought IIA's nine statements in; IIA states 61 against our 61, so the "
        "polity is no longer outside every stated area and the baseline became stale. The FAO row "
        "still reads 0.612x and still needs explaining, which is what this dict is for.",
}

_both = sorted(set(BASELINE) & set(SOURCE_NOTES))
if _both:
    raise SystemExit(
        f"BASELINE and SOURCE_NOTES both explain {_both}; a divergence is either baselined or "
        f"a one-source note, not both, or the published note is ambiguous"
    )



# The IIA tables are in FRENCH, and 708 of 785 labels resolved to nothing, so the check reached
# only 41 polities on its first run. `data/final/source_label_lexicon.csv` maps a normalised
# French (or OCR-damaged) form to an English label that `matchlib` can resolve.
#
# DELIBERATELY NOT ALIASES. These labels never appear in production data -- layer B's IIA rows
# arrive already translated -- so putting 180 French rules into applied_aliases.csv would inflate
# the published label_alias_map.csv with routes nothing uses. The lexicon serves this reference
# table only.
#
# The normaliser also strips a trailing nationality qualifier (`TUNISIE french`,
# `AUSTRALIE british`) and repairs OCR hyphenation across a line break, which is why several
# variants collapse onto one form.
_NATIONALITY = re.compile(
    r"\b(british|french|portuguese|german|spanish|italian|belgian|dutch|japanese|american"
    r"|fr|br|it|sp|port|angl)\b"
)


def normalise_label(raw: str) -> str:
    text = unicodedata.normalize("NFKD", str(raw)).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"-\s+", "", text)          # OCR hyphenation across a line break
    text = _NATIONALITY.sub("", text)
    text = re.sub(r"[^a-z0-9: ]", " ", text)
    return re.sub(r"\s+", " ", text).strip(" :")


def load_lexicon() -> dict:
    if not os.path.exists(LEXICON_PATH):
        return {}
    with open(LEXICON_PATH, encoding="utf-8") as fh:
        return {
            r["normalised_form"]: r["english_label"]
            for r in csv.DictReader(fh)
            if r.get("normalised_form") and r.get("english_label")
        }


def analyse():
    """Resolve every stated area to a polity and compare it to that polity's polygon.

    Returns a dict, or a string explaining why the analysis cannot run (a SKIP reason).

    SPLIT OUT OF main() FOR ISSUE 166. The comparison used to exist only inside this gate, so
    the one thing a CONSUMER needs from it -- which territorial basis the source's numbers were
    collected on, per (polity, source) -- was reachable only by reading a Python dict of prose.
    `scripts/write_stated_area_basis.py` publishes it as a table by calling this function, which
    keeps exactly one implementation of the digit screen and the consensus band. If the two ever
    disagreed, the published table would contradict the gate that guards it.
    """
    for path in (STATED_PATH, CSV_PATH, GPKG_PATH):
        if not os.path.exists(path):
            return f"SKIP: {os.path.relpath(path, REPO)} missing"
    try:
        import geopandas as gpd
    except ImportError:
        return "SKIP: geopandas unavailable"
    sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))
    try:
        import matchlib
    except ImportError:
        return "SKIP: matchlib unavailable"

    import warnings
    warnings.filterwarnings("ignore")

    frame = gpd.read_file(GPKG_PATH)
    frame = frame[frame.geometry.notna() & ~frame.geometry.is_empty].to_crs("ESRI:54034")
    ours = {r["polity_code"]: r.geometry.area / 1e6 for _, r in frame.iterrows()}
    with open(CSV_PATH, encoding="utf-8") as fh:
        names = {r["polity_code"]: r["polity_name"] for r in csv.DictReader(fh)}

    matcher = matchlib.Matcher(
        CSV_PATH,
        os.path.join(REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv"),
        verbose=False,
    )

    lexicon = load_lexicon()
    with open(STATED_PATH, encoding="utf-8") as fh:
        statements = list(csv.DictReader(fh))

    # COMPARE AGAINST THE RANGE OF STATED AREAS, NOT A SINGLE FIGURE.
    #
    # The first version of this gate took the most divergent single statement per polity and
    # failed on it. That was wrong, and measuring showed why: THE SOURCE DISAGREES WITH ITSELF.
    # Of 159 (label, data_year) pairs stated in more than one IIA edition, 61 -- 38% -- give
    # different areas for the SAME data year, 11 of them by over 25%:
    #
    #     cote des somalis  1913     22,000 -> 120,000   5.45x
    #     inde britannique  1911  2,012,967 -> 4,659,226 2.31x
    #     equateur          1913    307,243 ->   451,180 1.47x
    #     mozambique        1913    760,014 -> 1,105,475 1.45x
    #     bolivie           1913  1,332,808 -> 1,834,225 1.38x
    #
    # These are not territorial changes -- Mozambique's borders were settled in 1891 and the
    # 1929 edition simply revised a bad earlier survey downward by 335,000 km2. So "what the
    # source thought the territory was" depends on WHICH EDITION you read, not only on which
    # year it describes. A gate that picks one statement picks an edition, arbitrarily.
    #
    # So a polygon is only flagged when it falls outside the FULL RANGE of what any edition
    # ever stated for that polity, by more than the tolerance. That is the claim worth making:
    # not "our polygon disagrees with the source" but "our polygon disagrees with EVERY figure
    # the source ever published". Mozambique passes on this logic and should -- 786,369 sits
    # inside 760,014-1,108,875, agreeing with the four later editions and not the two earlier.
    # CONSENSUS, NOT RANGE -- because the NUMBERS have OCR errors too, not just the labels.
    #
    # The first version accepted anything inside the full span of what the source ever stated.
    # That is unsafe, and Cote des Somalis shows why:
    #
    #     iia ed1909, ed1925        120,000 km2      wrong
    #     iia ed1929, 32, 33, 38     22,000 / 21,963  correct
    #     fao ed1952                 23,000          independent confirmation
    #     French Somaliland actual   ~23,200
    #
    # That is not the source revising its scope. It is a BAD NUMBER, corrected in 1929, and it
    # looks like a spurious leading digit on 20,000. Accepting the full range would let a 5x
    # wrong polygon pass for Djibouti. Monaco is the same shape (21 in five editions, 149 in two,
    # against FAO's correct 2) and so is Norfolk Island (FAO 350 against an actual 35 -- exactly
    # 10x, a figure in km2 filed under a `1000 hectares` heading).
    #
    # So: take the MEDIAN of everything stated for a polity, drop statements that sit at roughly
    # 10x or 1/10 of it -- the signature of a lost or gained digit -- and compare the polygon
    # against what survives. The dropped statements are reported separately, because a list of
    # probable digit errors is useful feedback for the digitisation pipeline rather than noise.
    #
    # Tunisia deliberately does NOT get dropped by this rule: IIA states 125,130 and FAO 155,830,
    # a 0.76x ratio that is nothing like a digit error, and IIA repeats it identically across six
    # editions, which OCR would not. That one is a definitional difference -- most likely whether
    # the southern military territories were counted -- and it should stay visible.
    import statistics

    pairs, allstated = {}, {}
    for row in statements:
        try:
            year = int(row["data_year"])
            stated = float(row["stated_area_km2"])
        except (KeyError, TypeError, ValueError):
            continue
        code = None
        for candidate in (row["label"], lexicon.get(normalise_label(row["label"]))):
            if not candidate:
                continue
            try:
                code = matcher.assign(candidate, None, row["source"], year)[0]
            except Exception:
                code = None
            if code:
                break
        if not code or code not in ours or stated <= 0:
            continue
        pairs[(code, row["source"], year)] = ours[code] / stated
        allstated.setdefault(code, []).append((stated, row["source"], row["edition"], row["label"]))

    # ONE VOTE PER SOURCE, NOT PER EDITION -- because editions are not independent.
    #
    # A count-based median is fooled whenever the majority is wrong, and Monaco proves it: IIA
    # states 21 km2 in seven editions and 149 in two, FAO states the correct 2. Median by count
    # is 21, so the first version of this screen discarded FAO'S CORRECT VALUE as the outlier.
    # Yearbooks reprint each other's area tables, so seven IIA editions are close to one
    # observation repeated, not seven observations agreeing.
    #
    # So: collapse each source to its own median first, then take the consensus across sources.
    # Monaco becomes IIA 21 vs FAO 2, and neither is discarded -- the band is simply wide, which
    # is the honest description of two sources disagreeing tenfold about a 2 km2 country.
    DIGIT_LO, DIGIT_HI = 7.0, 13.0  # a lost or gained decimal digit, with room for rounding
    suspect, worst, per_source = [], {}, {}
    for code, obs in allstated.items():
        by_source = {}
        for stated, src, edition, label in obs:
            by_source.setdefault(src, []).append((stated, edition, label))
        source_value = {
            src: statistics.median(v for v, *_ in vals) for src, vals in by_source.items()
        }
        consensus = statistics.median(source_value.values())
        kept = {}
        for src, val in source_value.items():
            r = val / consensus if val > consensus else consensus / val
            # only drop a source whose whole median looks like a digit error AND where another
            # source survives to compare against -- never leave the polity with no evidence
            dropped = DIGIT_LO <= r <= DIGIT_HI and len(source_value) > 1
            if dropped:
                worst_ed = max(by_source[src], key=lambda t: abs(t[0] - consensus))
                suspect.append((code, val, consensus, src, worst_ed[1], worst_ed[2]))
            else:
                kept[src] = val
            per_source[(code, src)] = {
                "stated": val,
                "statements": len(by_source[src]),
                "editions": sorted({str(e) for _, e, _ in by_source[src]}),
                "labels": sorted({lab for *_, lab in by_source[src]}),
                "digit_error_suspect": dropped,
            }
        if not kept:
            continue
        lo, hi = min(kept.values()), max(kept.values())
        mine = ours[code]
        key = (code, "/".join(sorted(kept)))
        if mine < lo * (1 - TOLERANCE):
            worst[key] = (mine / lo, lo, hi, mine, list(kept.items()))
        elif mine > hi * (1 + TOLERANCE):
            worst[key] = (mine / hi, lo, hi, mine, list(kept.items()))

    return {
        "ours": ours,
        "names": names,
        "statements": statements,
        "lexicon": lexicon,
        "pairs": pairs,
        "allstated": allstated,
        "per_source": per_source,
        "suspect": suspect,
        "diverged": worst,
    }


def main() -> int:
    result = analyse()
    if isinstance(result, str):
        print(result)
        return 0
    ours = result["ours"]
    statements, lexicon, pairs = result["statements"], result["lexicon"], result["pairs"]
    allstated, suspect, diverged = result["allstated"], result["suspect"], result["diverged"]

    problems = []
    baselined = {k[0] for k in BASELINE}
    for key in sorted(diverged):
        if key[0] in baselined:
            continue
        ratio, lo, hi, mine, ev = diverged[key]
        rng = f"{lo:,.0f}" if lo == hi else f"{lo:,.0f}-{hi:,.0f}"
        problems.append(
            f"{key[0]} polygon {mine:,.0f} km2 is outside every area {key[1]} states for it "
            f"({rng} km2 across {len(ev)} statement(s), {ratio:.2f}x the nearest)"
        )
    seen = {k[0] for k in diverged}
    for key in sorted(BASELINE):
        if key[0] in ours and key[0] not in seen:
            problems.append(
                f"{key[0]} / {key[1]} is baselined as diverging but is now within "
                f"{TOLERANCE:.0%} -- remove its entry"
            )

    within10 = sum(1 for r in pairs.values() if abs(r - 1) <= 0.10)
    print(f"stated-area statements: {len(statements):,}   lexicon entries: {len(lexicon)}")
    print(f"(polity, source, year) pairs resolved: {len(pairs)}   polities: {len({k[0] for k in pairs})}")
    print(f"  within 10%: {within10}   within {TOLERANCE:.0%}: "
          f"{sum(1 for r in pairs.values() if abs(r - 1) <= TOLERANCE)}")
    print(f"  polygon >{TOLERANCE:.0%} LARGER than stated:  {sum(1 for r in pairs.values() if r > 1 + TOLERANCE)}")
    print(f"  polygon >{TOLERANCE:.0%} SMALLER than stated: {sum(1 for r in pairs.values() if r < 1 - TOLERANCE)}")
    revised = sum(
        1 for obs in allstated.values() if len({round(v) for v, *_ in obs}) > 1
    )
    print(f"  polities whose stated area is REVISED between editions for one data year: {revised}")
    print(f"  polities outside every stated figure: {len(diverged)} ({len(BASELINE)} baselined)")
    if suspect:
        print(f"\n  statements dropped as probable DIGIT ERRORS (~10x the median for that polity): {len(suspect)}")
        for code, stated, med, src, edition, label in sorted(suspect)[:10]:
            print(f"    {code:18s} {src} ed{edition} states {stated:>11,.0f} vs median {med:>11,.0f}  [{label[:26]}]")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print(
            "\n  A stated area is evidence about SCOPE -- what the publisher counted as inside\n"
            "  the territory -- which is what a per-km2 denominator must match. Check which side\n"
            "  is wrong before changing anything: IIA states Monaco as 21 km2, so the source can\n"
            "  be the error. If the divergence is real and understood, baseline it with the\n"
            "  reason; if the polygon is wrong, fix the polygon."
        )
        return 1

    print("\nPASS: every polygon agrees with its source's stated area, or diverges for a recorded reason")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
