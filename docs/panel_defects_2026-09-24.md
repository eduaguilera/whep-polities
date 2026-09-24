# Source-data defects in the subnational production panel (2026-09-24)

*Written by Claude (Anthropic's model) from an audit of the panel. For the panel's producer.*

This lists defects in the **data values** of the WHEP harmonized subnational production panel
(`whep_production_subnational.parquet`, 8,929,673 rows; see `wiki/sources/juan-subnational.md`).
Routing (which polity a unit's rows go to) is out of scope here and is fixed in this repository.
Every number below was recomputed from the panel on 2026-09-24 with the snippet under it.

All snippets start from:

```python
import os, numpy as np, pandas as pd
d = pd.read_parquet(os.environ.get("WHEP_SUBNATIONAL",
                    "/tmp/claude-1001/panel/whep_production_subnational.parquet"))
K = ["admin_unit_id", "lane", "item_clean", "indicator", "unit_canonical", "year"]
```

`K` is the key that should be unique: one value per unit, lane, item, indicator, unit and year.

## Summary

| # | defect | size | countries |
|---|---|---|---|
| 1 | Cropland is zero or near zero where crops are large, because the land-use join matches names that differ | 11 units, every year | Chile, Mexico, Bolivia |
| 2 | Chile's crop series for regions later split are on the pre-split territory, and the land use is on the post-split polygon | Biobío/Ñuble, Los Lagos/Los Ríos, Tarapacá/Arica y Parinacota | Chile |
| 3 | USDA NASS `ALL CLASSES` rows sit beside the class breakdowns under the same key | 94,767 duplicated key groups (84,694 contain `ALL CLASSES`); the rows sum to a median 2.0x the total | USA |
| 4 | Chillies rows duplicated exactly | 30,959 key groups, 61,918 rows | Colombia, Mexico, Brazil, Argentina |
| 5 | `Beans, green` mapped to broad beans, beside it, with fallback zeros | 8,524 key groups; 4,632 hold a zero beside a non-zero value | Argentina, Brazil |
| 6 | `legacy_balanced` yields 10x above or below the same item's median in that country and year | 17,518 unit-years (17,429 legacy_balanced, 89 observational) | mainly Argentina, Mexico, Colombia, Brazil |
| 7 | Identical series in two different units | 343 series pairs identical in 100 or more years, 313 of them in France | France, Argentina, Italy, Colombia, Spain |
| 8 | Livestock with a constant share across departments, labelled `observational` | Rabbits and hares (100% of 89 departments), Turkeys (98.9%) | France |
| 9 | NASS rows whose unit was never converted | 21,439 rows, `value_canonical` null | USA |
| 10 | Argentina cropland jumps 75% in one year where two methods are spliced | 6.84 Mha (1908) to 11.98 Mha (1909) | Argentina |

## 1. Cropland zero where crops are large: names that differ in the land-use join

For each of these units the crop rows and the land-use rows carry **different `admin_name_clean`
forms** for the same `admin_unit_id`. Wherever the land use was allocated by name, the unit got
zero or almost zero cropland in every year, and the cropland meant for it is missing:

| unit | name on crop rows | name on land-use rows | crop area (median ha) | cropland (median ha) |
|---|---|---|---|---|
| MEX-MEX | Estado de México | México | 562,527 | 406 |
| MEX-CMX | Ciudad de México | Distrito Federal | 9,907 | 21 |
| BOL-BEN | Beni | El Beni | 51,073 | 0 in all 124 years |
| CHL-BI | Biobío | Bío-Bío | 243,119 | 0 in all 124 years |
| CHL-LI | O'Higgins | Libertador General Bernardo O'Higgins | 118,021 | 0 in all 124 years |
| CHL-RM | Metropolitana | Región Metropolitana de Santiago | 75,642 | 0 in all 124 years |

Chile also has cropland 0 in every year for CHL-AI, AN, AP, AT, LR, MA, NB and TA. Those units
have no crop rows, so the zero may be real for the desert and Patagonian ones. For Ñuble, Los Ríos
and Arica y Parinacota it is probably the split problem in section 2. The Chilean units whose two
name forms agree (Araucanía, Coquimbo, Los Lagos, Maule, Valparaíso) do get cropland.

```python
for c in ["Chile", "Mexico", "Bolivia"]:
    x = d[d.country_clean == c]
    area = (x[(x.indicator == "area") & (x.lane == "legacy_balanced") & (x.unit_canonical == "ha")]
            .groupby(["admin_unit_id", "admin_name_clean", "year"]).value_canonical.sum())
    crop = (x[(x.indicator == "landuse") & (x.item_clean == "cropland")]
            .groupby(["admin_unit_id", "admin_name_clean", "year"]).value_canonical.sum())
    m = pd.concat([area.rename("croparea"), crop.rename("cropland")], axis=1).reset_index()
    print(m.groupby(["admin_unit_id", "admin_name_clean"])
           .agg(croparea=("croparea", "median"), cropland=("cropland", "median")))
```

**Fix:** join land use to crops on `admin_unit_id`, not on the name.

## 2. Chile: crops on pre-split regions, land use on post-split polygons

Each Chilean unit's land-use total (cropland + pasture + forest + other_natural + urban) is
constant in every year from 1900 to 2023, and it is the **post-split** region: CHL-BI 23,310 km2
and CHL-NB (Ñuble, split off in 2018) 13,012 km2, reported separately from 1900. The crop series
do not follow that:

- Ñuble, Los Ríos (split off Los Lagos in 2007) and Arica y Parinacota (split off Tarapacá in 2007)
  have **no crop rows at all**.
- CHL-BI's crop area has no break at 2018 (173,111 ha in 2017, 174,995 ha in 2018). CHL-LL's
  falls 20% in 2007 (75,858 to 60,640 ha), but CHL-BI falls 24% in the same year and CHL-LL is back
  to 73,787 ha in 2008. That is a panel-wide break in 2007, the census year, not the Los Ríos split.
  Both series appear to still include the territory split off later.

So for the whole period Biobío's crops cover Biobío plus Ñuble, but its land use covers only
post-2018 Biobío, and the same holds for Los Lagos and Los Ríos. Any per-hectare ratio of the two
is too high. This is a likely reading, not proven: the producer should confirm which boundary the
Chilean crop series use.

```python
c = d[d.country_clean == "Chile"]
lu = (c[(c.indicator == "landuse") & c.item_clean.isin(
        ["cropland", "forest", "other_natural", "pasture", "urban"])]
      .groupby(["admin_unit_id", "year"]).value_canonical.sum().unstack(0) / 100)  # km2
print(lu.loc[[1900, 2017, 2018, 2023]].T)
area = (c[(c.indicator == "area") & (c.lane == "legacy_balanced") & (c.unit_canonical == "ha")]
        .groupby(["admin_unit_id", "year"]).value_canonical.sum().unstack(0))
print(area.loc[2005:2019, ["CHL-BI", "CHL-LL"]], sorted(area.columns))
```

## 3. USDA NASS: `ALL CLASSES` beside its own breakdown

NASS reports a commodity total (`class: ALL CLASSES`) and its classes (winter/spring wheat,
alfalfa/excluding alfalfa hay, ...). The panel keeps both under the same `item_clean`. Of the
94,767 NASS key groups with more than one row, 84,694 contain an `ALL CLASSES` row. Among the
55,783 area and production groups that have one, the rows sum to a median **2.0x** the
`ALL CLASSES` value: the total is counted once as itself and once as its parts. Summing or averaging
by key doubles or distorts every such state-year.

```python
n = d[d.source == "USDA NASS Subnational"]
n = n.assign(cls=n.source_detail.str.extract(r"class: ([^|]*?) \|")[0])
g = n.groupby(K).agg(cnt=("year", "size"), hasall=("cls", lambda s: (s == "ALL CLASSES").any()))
print((g.cnt > 1).sum(), ((g.cnt > 1) & g.hasall).sum())            # 94767 84694
v = n[n.indicator.isin(["area", "production"]) & n.value_canonical.notna()]
allc = v[v.cls == "ALL CLASSES"].groupby(K).value_canonical.max()
m = pd.concat([allc.rename("allc"), v.groupby(K).value_canonical.sum().rename("tot"),
               v.groupby(K).size().rename("cnt")], axis=1).dropna()
m = m[m.cnt > 1]
print(len(m), (m.tot / m.allc).median())                            # 55783 2.0
```

**Fix:** keep class rows as their own `item_clean` or series, or drop them where the total exists.

## 4. Chillies: exact duplicate rows

In the LatAm component, 30,959 key groups for `Chillies and peppers, green` have exactly two rows.
In every group they are identical: same value, same `item_original`, same `source_detail`
(61,918 rows, all `legacy_balanced`; Colombia 18,966, Mexico 18,048, Brazil 13,392,
Argentina 11,512). Sums over them count chillies twice.

```python
ch = d[d.item_clean.str.startswith("Chillies", na=False) & (d.source == "LatAm Subnational")]
g = ch.groupby(K).agg(n=("year", "size"), nv=("value_canonical", "nunique"))
print((g.n > 1).sum(), ((g.n > 1) & (g.nv == 1)).sum())             # 30959 30959
```

## 5. Broad beans: `Beans, green` merged into them, with fallback zeros

In Argentina and Brazil, `item_original = "Beans, green"` (a different FAO item) is mapped to
`item_clean = "Broad beans and horse beans, green"` and sits beside the real broad-bean rows:
8,524 duplicated key groups. In 4,632 of them one row is zero and the other is not. The zeros come
from `fallback` / `fallback_interpolated` rows. All 8,524 duplicated rows with the broad-bean
`item_original` are zero fallbacks. Of the green-bean rows, 3,348 are zero fallbacks and 544 are
zero `scaled` rows. So a mean over the key halves the value, and a max or first row
depends on row order.

```python
bb = d[(d.item_clean == "Broad beans and horse beans, green") & (d.source == "LatAm Subnational")]
g = bb.groupby(K).agg(n=("year", "size"), mn=("value_canonical", "min"), mx=("value_canonical", "max"))
print((g.n > 1).sum(), ((g.n > 1) & (g.mn == 0) & (g.mx > 0)).sum())   # 8524 4632
dd = bb[bb.duplicated(K, keep=False)]
print(dd.groupby(["item_original", "method", dd.value_canonical.eq(0)]).size())
```

## 6. Yield outliers in `legacy_balanced`

Production divided by area, compared with the median over the same item in the same country, lane
and year, where at least five units report it. 17,518 unit-years are more than 10x above or below
that median. 17,429 of them are `legacy_balanced`, and Argentina alone has 7,053. The worst are
persistent, not single years. For example, **ARG-RESID soya beans** is an outlier in 74 years
(1945-2018), with a median ratio of 0.018 to its siblings. Its production/area over its 79
soya years has a median of 0.036 t/ha, against a sibling median of about 1.5 t/ha. That looks like
the residual's area kept while its production was allocated away. The per-series list the audit
produced (1,029 series) can be regenerated with the snippet below.

```python
x = d[d.value_canonical.notna() & d.indicator.isin(["production", "area"])
      & d.unit_canonical.isin(["tonnes", "ha"])].copy()
x["series"] = np.where(x.source == "USDA NASS Subnational",
                       x.source_detail.str.extract(r"data_item: ([^|]*?) \|")[0].fillna(""), "")
k = ["country_clean", "admin_unit_id", "lane", "item_clean", "series", "year"]
w = x.groupby(k + ["indicator"]).value_canonical.mean().unstack("indicator").dropna()
w = w[(w.area > 0) & (w.production > 0)].reset_index()
w["y"] = w.production / w.area
grp = ["country_clean", "lane", "item_clean", "series", "year"]
w["r"] = w.y / w.groupby(grp).y.transform("median")
o = w[(w.groupby(grp).y.transform("size") >= 5) & ((w.r > 10) | (w.r < 0.1))]
print(len(o), o.lane.value_counts())                                 # 17518
```

## 7. Identical series in two units

Positive values rounded to 1e-6 that are identical in two units for the same country, lane, item,
indicator and year, counting only values that are not multiples of 10 (so round numbers do not match
by chance). 343 series pairs are identical in 100 or more such years: France 313, Argentina 22,
Italy 4, Colombia 3, Spain 1. In France the pairs include departments in different regions: pears area,
FRA-FRJ24 = FRA-FRJ25 for 143 years; apricots production, FRA-FRI31 (Charente) = FRA-FRJ26
(Hautes-Pyrénées) for 143 years. One department's series was copied to another instead of being allocated. Loosening the
threshold to 6 identical years gives 2,910 pairs, 1,864 of them French.

```python
x = d[d.value_canonical.notna() & (d.value_canonical > 0) & (d.indicator != "yield")].copy()
x["series"] = x.source_detail.where(x.source == "USDA NASS Subnational", "") \
               .str.extract(r"data_item: ([^|]*?) \|")[0].fillna("")
x["v"] = x.value_canonical.round(6)
k = ["country_clean", "lane", "item_clean", "indicator", "series", "year", "v"]
g = x.groupby(k).admin_unit_id.agg(lambda s: "|".join(sorted(set(s)))).reset_index()
g = g[g.admin_unit_id.str.contains("|", regex=False) & (g.v % 10 != 0)]
s = g.groupby(["country_clean", "lane", "item_clean", "indicator", "series", "admin_unit_id"]).size()
print((s >= 100).sum(), s[s >= 100].groupby(level=0).size())         # 343
```

## 8. France: constant-share livestock labelled observational

For French rabbits and hares, every department's share of the national stock is constant
(coefficient of variation below 1e-3) across all 141 years. For turkeys the same holds in 88 of
89 departments. Those are a national total allocated with fixed weights, but the rows are
`lane = observational`, `observation_type = annual` with an empty `method`. A consumer filtering
on the lane treats them as department observations.

```python
fr = d[(d.country_clean == "France") & (d.indicator == "livestock_stock")
       & d.item_clean.isin(["Rabbits and hares", "Turkeys"])]
for item, x in fr.groupby("item_clean"):
    p = x.pivot_table(index="year", columns="admin_unit_id", values="value_canonical").dropna()
    sh = p.div(p.sum(axis=1), axis=0)
    print(item, ((sh.std() / sh.mean()) < 1e-3).mean(), x.lane.unique(), x.method.unique())
```

## 9. NASS rows with unconverted units

21,439 NASS rows carry `conversion_method = "unmapped"` and a null `value_canonical`, although
`value_original` is present in all of them. By `unit_canonical`: `tonnes_lint` 11,557, `BOXES`
4,290, `PCT BY GRADE` 1,950, `BOXES / ACRE` 1,056, `bushels` 528, `BALES / ACRE` 432,
`RUNNING BALES` 380, `GALLONS / TAP` 250. The cotton lint and the citrus boxes are real production
lost to every canonical-unit consumer. Percent-by-grade is not a quantity and could be dropped.

```python
u = d[(d.source == "USDA NASS Subnational") & (d.conversion_method == "unmapped")]
print(len(u), u.value_canonical.notna().sum(), u.value_original.notna().sum())  # 21439 0 21439
print(u.unit_canonical.value_counts())
```

## 10. Argentina: cropland jumps at the 1908/1909 splice

Argentina's summed cropland rises from 6.84 Mha in 1908 to 11.98 Mha in 1909 (+75%). Before
that it climbs linearly by about 0.42 Mha a year, and after it by about 0.3 Mha a year. All 24
provinces change method in that same year: `luh2_calibrated_to_fao1961` up to 1908, `iia_benchmark`
from 1909. The step is the splice, not agricultural history. Anything divided by cropland (yield per
cropland hectare, cropland shares) breaks at 1909.

```python
a = d[(d.country_clean == "Argentina") & (d.indicator == "landuse") & (d.item_clean == "cropland")]
print((a.groupby("year").value_canonical.sum().loc[1905:1912] / 1e6).round(2))
print(a[a.year.isin([1908, 1909])].groupby(["year", "method"]).size())
```

**Fix:** scale the pre-1909 LUH2 path to the 1909 IIA benchmark, or blend over a transition window.
