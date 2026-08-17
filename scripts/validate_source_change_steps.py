#!/usr/bin/env python3
"""Does a jump in a family's area coincide with a change of polygon SOURCE?

When two consecutive periods of one family draw their polygons from different datasets, any
difference between those datasets' conventions is published as a territorial change at the
boundary year. Nothing else in this repo asks that question:

  * `validate_family_areas` compares each period against its family MEDIAN, so a step between
    two halves of a family can leave both halves inside tolerance.
  * `validate_polygon_period_fit` asks whether a VINTAGE sits inside a SPAN — a per-row
    question that says nothing about the neighbour.
  * `validate_polygons`' area check is opt-in via `polygon_area_km2`, and most of the rows
    involved here declare null (issue 59).

A large ratio ALONE is not a signal: the largest steps in this database are the Treaty of
Trianon and Guadalupe Hidalgo. A source change alone is not a signal either: 22 of the 39
source-changing steps move the area by under 30%. The two TOGETHER are the signal, and the
baseline below is the instrument — every qualifying step must carry an entry naming what
produced it. An entry saying "Trianon" is documentation; the absence of one is a flag.

WHAT IT FOUND when first run (issue 159):

  TUN-1800-1881 -> TUN-1881-2025   3.55x, the largest step in the database, and NOT history.
      The earlier row was bound to Paine et al. (2024) feature `Tunis` at 43,752 km2, its
      successor to CShapes 616@1886 at 155,471. Issue 159 read the 111,741 km2 difference as
      claimed-versus-effective territory with the Sahara between them. Re-measuring rejected
      that: only 61,369 km2 of it lies south of 33.44N and 42,728 km2 is north-WESTERN
      Tunisia — Beja, Jendouba, Le Kef, Kasserine and Gafsa all outside the Paine polygon
      while Kairouan, Siliana and Sfax are inside it. The Medjerda valley is the Beylik's
      grain belt; no account of Husainid control excludes it and keeps Kairouan. The row was
      rebound to CShapes 616@1886, which its own page had described all along, and the step
      now measures 1.00x — so it is absent from the baseline rather than listed in it.

  OTT-1800-1886 -> OTT-1886-1908   1.34x, and THE SIGN IS THE PROOF. The Ottoman Empire
      contracted across the nineteenth century, yet the data publishes a 34% EXPANSION at
      1886. Decomposed: +881,968 km2 in Ottoman Libya and +81,552 km2 in Yemen/Asir, both
      held in 1800 and both simply absent from Cliopatria's polygon; -171,358 km2 in the
      Balkans, which is the real 1878 Berlin settlement. A convention difference of 963,520
      km2 — nine times TUN's — outweighing a real loss and reversing its sign. Baselined as
      an artefact rather than fixed, because fixing it needs a constructed 1800 polygon and
      neither source offers one.

  TUR-1800-1913 -> TUR-1913-1914   2.29x, which is neither an event nor a convention
      difference but a change in what the family DENOTES: an Anatolia-only proxy for what
      Mitchell and FAOSTAT report as "Turkey", followed by the whole Ottoman Empire at 1913.
      Both pages document their own choice, and nothing compared them.

Usage:
  python3 scripts/validate_source_change_steps.py [--ratio 1.3]
"""
import argparse
import csv
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES_CSV = os.path.join(REPO, "data/final/polities_database.csv")
POLITIES_GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
FAOSTAT_MAP = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")

DEAD_STATUS = ("retired", "superseded")

CODE_RE = re.compile(r"^(.*)-(\d{4})-(\d{4})$")

# Every entry must open with one of these, so the verdict is machine-readable and a reader
# does not have to parse prose to learn whether the published step is history:
#
#   EVENT     a real territorial change at the boundary year. The source change rides along.
#   ARTEFACT  the step is a difference between the two datasets' conventions, not history.
#             A consumer's per-km2 series shows a discontinuity that never happened.
#   SCOPE     the two rows deliberately denote different territorial extents, so the step is
#             neither an event nor a convention difference but a change of subject.
VERDICTS = ("EVENT", "ARTEFACT", "SCOPE")

# The prose after the tag has to say something. "EVENT: yes" would otherwise satisfy this
# gate, and a baseline that accepts a content-free entry is a baseline that accepts anything
# — the lesson audit_family_shadowing paid for, where an entry whose prose described a defect
# still counted as accepting it.
MIN_REASON_CHARS = 20

# Judged source-changing steps, keyed "EARLIER -> LATER". Bidirectional: a new qualifying
# step fails, and so does an entry whose step no longer qualifies.
BASELINE = {
    # ---------- ARTEFACT: published as history, and it is not ----------
    "OTT-1800-1886 -> OTT-1886-1908": (
        "ARTEFACT: 2,106,441 -> 2,823,367 km2, a 34% EXPANSION of an empire that spent the "
        "nineteenth century contracting, which is how the artefact is provable rather than "
        "arguable. Measured by difference and point-in-polygon: Cliopatria's 1800 polygon "
        "omits Ottoman Libya (+881,968 km2 in CShapes 1886) and Yemen/Asir (+81,552), both "
        "held in 1800; against that the Balkans lose 171,358 km2, which is the real 1878 "
        "Berlin settlement. So 963,520 km2 of convention difference outweighs a genuine loss "
        "and flips its sign. NOT FIXED: CShapes has no pre-1886 step, and back-projecting "
        "616/640@1886 would restore Libya while wrongly re-annexing Greece, Serbia, Romania "
        "and Bulgaria, which WERE Ottoman in 1800. It needs a constructed 1800 polygon "
        "(Cliopatria union Ottoman Libya union the Yemeni Tihama) and a source for its edges. "
        "Separately and in both rows: Istanbul falls OUTSIDE the polygon, so the empire's "
        "capital is not in it — same in both, so it does not drive this step."
    ),
    # ---------- SCOPE: the family changes what it denotes ----------
    "TUR-1800-1913 -> TUR-1913-1914": (
        "SCOPE: 780,180 -> 1,784,775 km2. Not an event and not a convention difference. "
        "TUR-1800-1913 is deliberately CShapes 640@1923 as an ANATOLIA-ONLY proxy, because "
        "Mitchell and FAOSTAT report 'Turkey' for present-day borders retroactively (Pamuk); "
        "TUR-1913-1914 is the whole Ottoman Empire at 1913. Both pages document their own "
        "choice and nothing compared the two. OPEN: a per-km2 series crossing 1913 in this "
        "family divides Anatolian output by an empire-wide denominator on one side of the "
        "boundary and an Anatolian one on the other. Resolving it is a periodisation "
        "question — whether the empire belongs to OTT/TUR-1913 or the family should be "
        "Anatolian throughout — not a polygon question, so it is not decided here."
    ),
    # ---------- EVENT: real history at the boundary year ----------
    # Key renamed 2026-08-17 (issue 252): HUN-1918-1919 -> HUN-1918-1920, when the row's
    # exclusive end_year moved 1919 -> 1920 to give 1919 back its coverage. Re-measured after
    # the rename: still 325,419 -> 93,004 km2, still 3.50x, still a source change. Only the
    # identifier moved.
    "HUN-1918-1920 -> HUN-1920-1938": (
        "EVENT: Treaty of Trianon, 4 June 1920. 325,419 -> 93,004 km2 (3.50x); Hungary "
        "genuinely lost about two thirds of its territory. The earlier row is HistoGIS' 1860 "
        "Habsburg Hungary, the later CShapes', so the source changes at the same boundary — "
        "which is exactly why a large ratio alone cannot be the signal."
    ),
    "COL-1800-1830 -> COL-1830-1903": (
        "EVENT: dissolution of Gran Colombia, 1830-31. 2,846,354 km2 is Gran Colombia — "
        "Venezuela, Ecuador and Panama included — against 1,167,440 for New Granada. The "
        "TERRITORY is right for the period; what is wrong is that the row is called "
        "'Colombia', which is a naming question tracked in issue 159 rather than a polygon "
        "one, and no area check can see it."
    ),
    "GRC-1881-1913 -> GRC-1913-1919": (
        "EVENT: the Balkan Wars. 63,612 -> 121,615 km2; the treaties of London and Bucharest "
        "(1913) added Macedonia, Epirus and Crete, and Greece nearly doubled."
    ),
    "SER-1878-1913 -> SER-1913-1918": (
        "EVENT: the Balkan Wars. 52,539 -> 90,538 km2; Serbia gained Kosovo and Vardar "
        "Macedonia under the 1913 Treaty of Bucharest."
    ),
    "MNE-1878-1913 -> MNE-1913-1918": (
        "EVENT: the Balkan Wars. 9,944 -> 15,922 km2; Montenegro gained the Sandzak of Plav "
        "and Gusinje and part of Metohija, roughly doubling."
    ),
    "GRC-1830-1881 -> GRC-1881-1913": (
        "EVENT: the 1881 Convention of Constantinople ceded "
        "Thessaly and the Arta district, about 13,000 km2. Measured 45,004 -> 63,612 km2 "
        "(1.41x) is larger than the cession alone, so part of this step is Cliopatria's 1830 "
        "Greece (45,004) sitting below the 1832 borders' accepted ~47,500 km2. The event "
        "dominates; the residual is a convention difference of roughly 5,000 km2."
    ),
    "JPN-1800-1895 -> JPN-1895-1945": (
        "EVENT: 371,147 -> 626,507 km2. The Treaty of Shimonoseki (1895) transferred Taiwan, "
        "and the annexation of Korea (1910) falls inside the later row; the two together "
        "account for the step."
    ),
    "JPN-1895-1945 -> JPN-1945-1952": (
        "EVENT: 626,507 -> 371,147 km2, the loss of the empire in 1945 — the same step in "
        "reverse, back to the home islands."
    ),
    "POL-1918-1919 -> POL-1919-1920": (
        "EVENT: the Treaty of Saint-Germain, 10 September 1919, which incorporated Galicia. "
        "130,180 -> 256,627 km2 (1.97x). The step is real history and most of it is Galicia "
        "(78,813 km2) plus the Versailles settlement of the western border and the Polish "
        "Corridor (130,205 -> 177,762 in CShapes' own steps for gwcode 290). The source "
        "changes at this boundary only because the later row cannot express its CShapes step "
        "as a polygon_feature_year and now binds constructed/POL-1919-1920, which IS that "
        "CShapes step named by its year bounds — so nothing about the step is a convention "
        "difference. Appeared when the row stopped publishing the polygon its own page "
        "rejects: it had been carrying the 177,762 km2 post-Versailles step, and 130,180 -> "
        "177,754 was 1.37x with no source change, hence unflagged. Issue 100."
    ),
    "HUN-1938-1940 -> HUN-1940-1944": (
        "EVENT: the Second Vienna Award, 30 August 1940, returned Northern Transylvania — "
        "43,492 km2. 108,814 + 43,492 = 152,306 against 152,441 measured, a 0.09% match, "
        "which is about as close as a polygon check gets to naming a treaty."
    ),
    "HUN-1940-1944 -> HUN-1944-1947": (
        "EVENT: reversal of the Vienna Awards, 1944-47. 152,441 -> 93,004 km2, back to the "
        "Trianon borders confirmed by the 1947 Treaty of Paris."
    ),
    "ROU-1920-1940 -> ROU-1940-1947": (
        "EVENT: the 1940 cessions. 296,126 -> 193,832 km2 — Bessarabia and northern Bukovina "
        "to the USSR (June), Northern Transylvania to Hungary (August), Southern Dobruja to "
        "Bulgaria (September)."
    ),
    "MEX-1800-1848 -> MEX-1848-2025": (
        "EVENT: the Treaty of Guadalupe Hidalgo, 2 February 1848. 3,187,750 -> 1,956,564 "
        "km2; the Mexican Cession is roughly the difference."
    ),
    "DEU-1938-1945 -> DEU-1945-1949": (
        "EVENT: 1945. 496,629 -> 356,835 km2 — the territory east of the Oder-Neisse line, "
        "plus the reversal of the Anschluss and of the Sudetenland annexation that the "
        "earlier row's 1938 vintage includes."
    ),
    "AUT-1800-1918 -> AUT-1918-1919": (
        "EVENT: the dissolution of Austria-Hungary, October-November 1918. 300,304 km2 is "
        "Cisleithania, whose accepted area is ~300,005 km2; 212,011 is the Republic of "
        "German-Austria's CLAIMED extent before Saint-Germain, which is why it contains "
        "Bolzano, Ljubljana and Trieste but not Prague or Brno. Correct for a row ending in "
        "1919. Both rows declare polygon_area_km2 = null, so nothing but this gate and the "
        "family-median check examines either figure (issue 59)."
    ),
    "EGY-1820-1885 -> EGY-1885-1899": (
        "EVENT: the Mahdist revolt ended Egyptian rule in Sudan by "
        "1885. 1,834,435 -> 1,167,984 km2, and point-in-polygon confirms the direction: "
        "Khartoum and Wadi Halfa are inside the earlier polygon and outside the later one. "
        "The residual runs the other way — Siwa and the western desert are inside CShapes' "
        "1885 Egypt and outside Cliopatria's Khedivate — so the step understates the Sudan "
        "loss and overstates the total change. The event dominates."
    ),
}


def faostat_reach() -> dict:
    """Which FAOSTAT area codes reach each polity. A baselined step a consumer cannot see is
    latent; one it can see is live, and the numbers do not distinguish them."""
    reach = defaultdict(set)
    if not os.path.exists(FAOSTAT_MAP):
        return reach
    with open(FAOSTAT_MAP, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            code = (r.get("polity_code") or "").strip()
            if code:
                reach[code].add((r.get("area_code") or "").strip())
    return reach


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratio", type=float, default=1.3)
    args = ap.parse_args()

    try:
        import geopandas as gpd
        from shapely.validation import make_valid
    except ImportError as exc:
        print(f"FAIL: geopandas/shapely unavailable ({exc})")
        return 2
    if not os.path.exists(POLITIES_GPKG):
        print(f"FAIL: {POLITIES_GPKG} missing; run scripts/build_database.py first")
        return 2

    # polygon_source is read from the CSV rather than the GeoPackage, because the CSV is the
    # published record of the BINDING while the GeoPackage carries the geometry the binding
    # produced. The two must agree, and validate_polygons is what checks that; here the
    # question is which dataset a row declares.
    with open(POLITIES_CSV, encoding="utf-8") as fh:
        rows = {r["polity_code"]: r for r in csv.DictReader(fh)}
    dead = {
        code for code, r in rows.items()
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS
    }

    frame = gpd.read_file(POLITIES_GPKG)
    frame = frame[~frame.geometry.isna() & ~frame.geometry.is_empty].copy()
    frame["geometry"] = frame.geometry.map(make_valid)
    measured = dict(
        zip(frame["polity_code"], frame.to_crs("ESRI:54034").geometry.area / 1e6)
    )

    families = defaultdict(list)
    for code, km2 in measured.items():
        if code in dead:
            continue
        m = CODE_RE.match(code)
        if m:
            families[m.group(1)].append((int(m.group(2)), int(m.group(3)), code, km2))

    steps = []
    for periods in families.values():
        periods.sort()
        for (_, _, ca, ka), (_, _, cb, kb) in zip(periods, periods[1:]):
            sa = (rows.get(ca, {}).get("polygon_source") or "").strip()
            sb = (rows.get(cb, {}).get("polygon_source") or "").strip()
            if sa == sb:
                continue
            ratio = max(ka, kb) / max(min(ka, kb), 1e-9)
            steps.append((ratio, ca, sa, ka, cb, sb, kb))
    steps.sort(reverse=True)

    reach = faostat_reach()
    qualifying = {}
    print(f"source-changing steps: {len(steps)} across "
          f"{len({s[1].rsplit('-', 2)[0] for s in steps})} families")
    for ratio, ca, sa, ka, cb, sb, kb in steps:
        key = f"{ca} -> {cb}"
        mark = " "
        if ratio >= args.ratio:
            qualifying[key] = (ratio, ka, kb)
            mark = "*"
        note = ""
        if mark == "*":
            tag = (BASELINE.get(key) or "unbaselined:").split(":", 1)[0].strip()
            n = len(sorted(reach.get(ca, ())) + sorted(reach.get(cb, ())))
            # Reachability separates a live artefact from a latent one, and the numbers do
            # not: an unreachable step misleads nobody until an alias points at it.
            seen = f"FAOSTAT-mapped via {n} area code(s)" if n else "not FAOSTAT-mapped"
            note = f"   [{tag}; {seen}]"
        print(
            f"  {mark}{ratio:>6.2f}x  {ca:<18}{sa:<24}{ka:>12,.0f} -> "
            f"{cb:<18}{sb:<24}{kb:>12,.0f}{note}"
        )
    print(f"\nat or above {args.ratio}x with a source change: {len(qualifying)} "
          f"(marked *) — each needs a baseline entry naming what produced it")

    problems = []
    for key in sorted(qualifying):
        ratio, ka, kb = qualifying[key]
        entry = BASELINE.get(key)
        left, right = key.split(" -> ")
        seen = sorted(reach.get(left, ())) + sorted(reach.get(right, ()))
        how = (
            f"FAOSTAT-mapped via {len(seen)} area code(s)" if seen
            else "not FAOSTAT-mapped"
        )
        if entry is None:
            problems.append(
                f"UNDOCUMENTED source-changing step: {key} moves the area {ratio:.2f}x "
                f"({ka:,.0f} -> {kb:,.0f} km2) at a boundary where polygon_source also "
                f"changes, so a consumer's per-km2 series steps there. {how}. Add a "
                f"BASELINE entry tagged EVENT (name the treaty or war), ARTEFACT (say "
                f"which convention differs, and by how much) or SCOPE (say what the two "
                f"rows denote) — or fix the binding"
            )
            continue
        tag = entry.split(":", 1)[0].strip()
        if tag not in VERDICTS:
            problems.append(
                f"{key}: baseline entry opens with {tag!r}, which is not one of "
                f"{list(VERDICTS)} — the verdict has to be readable without parsing prose"
            )
        reason = entry.split(":", 1)[1].strip() if ":" in entry else ""
        if len(reason) < MIN_REASON_CHARS:
            problems.append(
                f"{key}: baseline entry says only {reason!r}. An entry has to NAME what "
                f"produced the step; describing a step is not the same as accounting for it"
            )

    for key in sorted(set(BASELINE) - set(qualifying)):
        tag = BASELINE[key].split(":", 1)[0].strip()
        current = "no longer a source-changing step at all"
        for ratio, ca, sa, ka, cb, sb, kb in steps:
            if f"{ca} -> {cb}" == key:
                current = f"now measures {ratio:.2f}x, below the {args.ratio}x threshold"
                break
        problems.append(
            f"{key} is baselined as {tag} but {current} — remove the entry and replace it "
            f"with a comment saying what was measured and why it is gone (baselines here "
            f"are bidirectional)"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    counts = defaultdict(int)
    for key in qualifying:
        counts[BASELINE[key].split(":", 1)[0].strip()] += 1
    print("\nPASS: every source-changing step above the threshold is accounted for "
          + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
