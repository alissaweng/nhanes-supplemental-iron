# Supplemental Iron Intake by Age and Gender

An analysis of daily iron intake from dietary supplements using NHANES
2021-2023, asking whether older adults report lower intake than younger adults
and whether that pattern differs by gender.

The same analysis exists in two versions. The R version is the original
coursework. The Python version reimplements it and fixes three methodological
problems in the original.

**[Read the R analysis](analysis.md)** | **[Python version](analysis_python.py)**

## Approach

Two NHANES files were merged on respondent ID to link supplement intake with
age and gender. The outcome is right-skewed with a large mass of zero values,
so it was log-transformed for visualization and compared across age groups
using a Wilcoxon rank-sum test rather than a two-sample t-test.

Iron intake differed significantly by age group among men but not among women.

## What changed in the Python version

**Sampling weights.** The original treated NHANES as a simple random sample.
NHANES oversamples some groups by design, so unweighted statistics describe the
sample rather than the US population. The Python version applies `WTINT2YR` to
the medians, means, and regression fits.

Weights are applied to point estimates only. Full design-based variance
estimation, using the `SDMVSTRA` and `SDMVPSU` design variables, requires R's
`survey` package and is not implemented here. The Mann-Whitney test in the
Python version is therefore unweighted, and its p-value describes the sample
rather than the population.

**Log of zero.** `log(0)` returns negative infinity rather than an error, and
the original passed those values through to the plot, which is why points trail
off the bottom of the first scatter. The Python version restricts the transform
to positive values and reports how many records were excluded.

**Fitted lines.** The original computed linear models and then typed the
resulting intercepts and slopes into `geom_abline` by hand, so the plot would go
stale if the data changed. The Python version reads the coefficients off the
fitted model objects.

## Data

Publicly available from the [CDC NHANES portal](https://wwwn.cdc.gov/nchs/nhanes/),
August 2021 to August 2023 cycle.

| File | Contents |
|---|---|
| `DEMO_L.xpt` | Demographics, sampling weights, design variables |
| `DSQTOT_L.xpt` | Total dietary supplements, 30-day average nutrient intake |

The sampling frame is the U.S. civilian non-institutionalized population, so
results do not generalize to people in hospitals, nursing homes, or prisons.
Supplement intake is self-reported.

## Files

| File | Contents |
|---|---|
| `analysis.Rmd` | R source, R Markdown with code and interpretation |
| `analysis.md` | Rendered R analysis, viewable on GitHub |
| `analysis_files/` | Figures from the R version |
| `analysis_python.py` | Python version with sampling weights |

## Running it

**R.** Requires `foreign`, `dplyr`, `ggplot2`, and `broom`. Place both `.xpt`
files in the project folder and knit `analysis.Rmd`.

**Python.** Requires `pandas`, `numpy`, `seaborn`, `matplotlib`, `scipy`, and
`statsmodels`. Place both `.xpt` files in the project folder and run
`analysis_python.py`. Three figures are written to the same folder.

## About

Originally completed as a four person group project for PH 142 (Introduction to
Probability and Statistics in Biology and Public Health) at UC Berkeley, Spring
2026. My contributions were the data import, both visualizations, the
distribution and probability work, the hypotheses, and the Wilcoxon rank-sum
tests. Contributor details are in the analysis. The Python version and the
weighting are my own later work.
