# Supplemental Iron Intake by Age and Gender

An analysis of daily iron intake from dietary supplements using NHANES
2021-2023, asking whether older adults report lower intake than younger adults
and whether that pattern differs by gender.

**[Read the full analysis](analysis.md)**

## Approach

Two NHANES files were merged on respondent ID to link supplement intake with
age and gender. The outcome is right-skewed with a large mass of zero values, so
it was log-transformed for visualization and compared across age groups using a
Wilcoxon rank-sum test rather than a two-sample t-test.

Iron intake differed significantly by age group among men (p = 0.016) but not
among women (p = 0.263).

## Data

Publicly available from the [CDC NHANES portal](https://wwwn.cdc.gov/nchs/nhanes/),
August 2021 to August 2023 cycle.

| File | Contents |
|---|---|
| `DEMO_L.xpt` | Demographics: age, gender |
| `DSQTOT_L.xpt` | Total dietary supplements: 30-day average nutrient intake |

The sampling frame is the U.S. civilian non-institutionalized population, so
results do not generalize to people in hospitals, nursing homes, or prisons.
Supplement intake is self-reported.

## Files

| File | Contents |
|---|---|
| `analysis.Rmd` | Source. R Markdown with code and interpretation |
| `analysis.md` | Rendered output, viewable on GitHub |
| `analysis_files/` | Generated figures |

## Running it

Requires R with `foreign`, `dplyr`, `ggplot2`, and `broom`. Place both `.xpt`
files in the project folder and knit `analysis.Rmd`.

## About

Originally completed as a four-person group project for PH 142 (Introduction to
Probability and Statistics in Biology and Public Health) at UC Berkeley, Spring
2026. My contributions were the data import, both visualizations, the
distribution and probability work, the hypotheses, and the Wilcoxon rank-sum
tests. Contributor details are in the analysis.
