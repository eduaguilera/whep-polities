#!/usr/bin/env python3
"""Keep the Saudi/Yemen source footprints on the same side of the 2000 border change.

CShapes 2.0 GW 670 and 678 both change on 2000-06-12. UNTS 2389,
I-43167 records legal entry into force on 2000-07-04. These tests enforce
an explicit annual-2000 representation, not daily statistical precision.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


def reporting_period(iso3, year):
    matches = []
    for path in (ROOT / "wiki" / "polities").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        row = yaml.safe_load(text.split("---", 2)[1])
        if (
            row.get("iso3") == iso3
            and row.get("status") not in {"retired", "superseded"}
            and row.get("start_year", 9999) <= year < row.get("end_year", 0)
        ):
            matches.append(row)
    return matches


class SaudiYemenPeriods(unittest.TestCase):
    def test_source_features_follow_the_territorial_transition(self):
        # The independently inspected original source has coherent pre/post
        # pairs with zero overlap. Mixing Saudi1935 with Yemen2000 instead
        # duplicates about 2.994 million hectares before simplification.
        for year in (1990, 1999, 2000, 2001, 2015):
            for iso3, before, gwcode in (("SAU", 1935, 670), ("YEM", 1990, 678)):
                with self.subTest(iso3=iso3, year=year):
                    rows = reporting_period(iso3, year)
                    self.assertEqual(len(rows), 1)
                    row = rows[0]
                    self.assertEqual(row["polygon_source"], "cshapes-2.0")
                    self.assertEqual(row["polygon_feature_id"], gwcode)
                    self.assertEqual(
                        row["polygon_feature_year"], before if year < 2000 else 2000
                    )


if __name__ == "__main__":
    unittest.main()
