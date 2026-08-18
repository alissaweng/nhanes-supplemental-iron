"""
Supplemental iron intake by age and gender, NHANES 2021-2023.

Python version of an analysis originally written in R for PH 142, with three
changes:
  1. Survey weights are applied to the descriptive statistics. The R version
     treated NHANES as a simple random sample, which biases every estimate.
  2. log(0) is handled explicitly instead of silently producing -inf.
  3. Regression lines come from the fitted models instead of coefficients
     typed in by hand.

Files needed in the same folder, from https://wwwn.cdc.gov/nchs/nhanes/
  DEMO_L.xpt     demographics, weights, and design variables
  DSQTOT_L.xpt   total dietary supplements, 30-day average nutrient intake
"""

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.stats import mannwhitneyu

sns.set_theme(style="whitegrid")


# Load the two files
demo = pd.read_sas("DEMO_L.xpt", format="xport")
supp = pd.read_sas("DSQTOT_L.xpt", format="xport")

# WTINT2YR is the interview weight: how many people in the US population this
# respondent stands for. NHANES oversamples some groups on purpose, so
# unweighted numbers describe the sample and not the country.
# SDMVSTRA and SDMVPSU describe the clustered sampling. They matter for
# standard errors rather than for the estimates themselves.
demo_keep = demo[["SEQN", "RIDAGEYR", "RIAGENDR", "WTINT2YR", "SDMVSTRA", "SDMVPSU"]]
iron_keep = supp[["SEQN", "DSQTIRON"]]

# SEQN is the respondent ID shared by both files
df = iron_keep.merge(demo_keep, on="SEQN", how="left")

print("Rows, columns:", df.shape)
print(df.head())


# Clean and transform
df["Gender"] = df["RIAGENDR"].map({1: "Male", 2: "Female"})

# log(0) is negative infinity, not an error. The R version let those through,
# which is why points trailed off the bottom of the first scatter plot.
# Only take the log of positive values, and report how many were dropped.
n_zero = (df["DSQTIRON"] == 0).sum()
n_missing = df["DSQTIRON"].isna().sum()
print("Zero-intake records excluded from the log transform:", n_zero)
print("Missing intake records:", n_missing)

df["iron_log"] = np.where(df["DSQTIRON"] > 0, np.log(df["DSQTIRON"]), np.nan)

df["Age_Group"] = np.where(df["RIDAGEYR"] >= 50, "Older", "Younger")
df["Age_Decade"] = df["RIDAGEYR"] // 10 * 10


# Weighted statistics
def weighted_mean(values, weights):
    """Population mean. Each person counts as many times as their weight."""
    ok = values.notna() & weights.notna()
    if ok.sum() == 0:
        return np.nan
    return (values[ok] * weights[ok]).sum() / weights[ok].sum()


def weighted_median(values, weights):
    """Population median. Sort by value, add up the weights as you go, and
    return the value where the running total passes half the total weight."""
    ok = values.notna() & weights.notna()
    if ok.sum() == 0:
        return np.nan
    table = pd.DataFrame({"value": values[ok], "weight": weights[ok]})
    table = table.sort_values("value")
    running = table["weight"].cumsum()
    halfway = table["weight"].sum() / 2
    return table.loc[running >= halfway, "value"].iloc[0]


# Summary table, one row per gender and age group
rows = []
clean = df.dropna(subset=["DSQTIRON", "Gender"])

for gender in ["Female", "Male"]:
    for age_group in ["Younger", "Older"]:
        group = clean[(clean["Gender"] == gender) & (clean["Age_Group"] == age_group)]
        rows.append({
            "Gender": gender,
            "Age group": age_group,
            "n": len(group),
            "Unweighted median": round(group["DSQTIRON"].median(), 1),
            "Weighted median": round(
                weighted_median(group["DSQTIRON"], group["WTINT2YR"]), 1),
            "Weighted mean": round(
                weighted_mean(group["DSQTIRON"], group["WTINT2YR"]), 1),
        })

summary = pd.DataFrame(rows)
print()
print("Weighted vs unweighted summary")
print(summary.to_string(index=False))


# Fit a line of log intake against age, separately for each gender.
# The R version fitted these and then typed the coefficients into
# geom_abline by hand, so the plot would go stale if the data changed.
# Here the plot reads the coefficients off the fitted models.
male_data = df[df["Gender"] == "Male"].dropna(subset=["iron_log", "RIDAGEYR"])
female_data = df[df["Gender"] == "Female"].dropna(subset=["iron_log", "RIDAGEYR"])

# add_constant adds the column of 1s that represents the intercept.
# R's lm() does this automatically, statsmodels does not.
male_model = sm.WLS(
    male_data["iron_log"],
    sm.add_constant(male_data["RIDAGEYR"]),
    weights=male_data["WTINT2YR"],
).fit()

female_model = sm.WLS(
    female_data["iron_log"],
    sm.add_constant(female_data["RIDAGEYR"]),
    weights=female_data["WTINT2YR"],
).fit()

print()
print("Male   intercept", round(male_model.params.iloc[0], 4),
      " slope", round(male_model.params.iloc[1], 6),
      " R2", round(male_model.rsquared, 5))
print("Female intercept", round(female_model.params.iloc[0], 4),
      " slope", round(female_model.params.iloc[1], 6),
      " R2", round(female_model.rsquared, 5))


# Plot 1: log intake against age, with the fitted lines
plot_data = df.dropna(subset=["iron_log", "Gender"])
ages = np.linspace(plot_data["RIDAGEYR"].min(), plot_data["RIDAGEYR"].max(), 100)

plt.figure(figsize=(9, 5.5))
sns.scatterplot(data=plot_data, x="RIDAGEYR", y="iron_log", hue="Gender",
                alpha=0.35, s=14)

male_intercept, male_slope = male_model.params
plt.plot(ages, male_intercept + male_slope * ages,
         color="blue", linewidth=2, label="Male (weighted fit)")

female_intercept, female_slope = female_model.params
plt.plot(ages, female_intercept + female_slope * ages,
         color="red", linewidth=2, label="Female (weighted fit)")

plt.xlabel("Age (years)")
plt.ylabel("Log supplemental iron intake")
plt.title("Daily supplemental iron intake by age and gender, log scale")
plt.legend()
plt.tight_layout()
plt.savefig("fig1_scatter_by_age.png", dpi=150)
plt.close()


# Plot 2: weighted mean intake by decade
bar_rows = []
for gender in ["Female", "Male"]:
    for decade in sorted(plot_data["Age_Decade"].unique()):
        group = plot_data[(plot_data["Gender"] == gender)
                          & (plot_data["Age_Decade"] == decade)]
        bar_rows.append({
            "Gender": gender,
            "Age_Decade": decade,
            "mean_iron_log": weighted_mean(group["iron_log"], group["WTINT2YR"]),
        })

binned = pd.DataFrame(bar_rows)

plt.figure(figsize=(9, 5))
sns.barplot(data=binned, x="Age_Decade", y="mean_iron_log", hue="Gender")
plt.xlabel("Age group")
plt.ylabel("Weighted mean iron intake (log)")
plt.title("Weighted average supplemental iron intake by age group and gender")
plt.tight_layout()
plt.savefig("fig2_bar_by_age_group.png", dpi=150)
plt.close()


# Hypothesis test
# H0: the distribution of supplemental iron intake is the same for older
#     (50+) and younger (<50) adults, tested separately within each gender.
#
# The outcome is right-skewed with many zeros, so a rank-based test is more
# appropriate than a two-sample t-test. scipy calls this Mann-Whitney U and R
# calls the same test wilcox.test.
#
# LIMITATION: this test is unweighted. There is no standard survey-weighted
# rank test in Python, so these p-values describe the NHANES sample rather
# than the US population, and they ignore the clustered sampling design.
# R's survey package handles this properly.
print()
print("Mann-Whitney U, unweighted (see limitation in the comments)")
for gender in ["Female", "Male"]:
    subset = clean[clean["Gender"] == gender]
    older = subset[subset["Age_Group"] == "Older"]["DSQTIRON"]
    younger = subset[subset["Age_Group"] == "Younger"]["DSQTIRON"]
    stat, p = mannwhitneyu(older, younger, alternative="two-sided")
    print(gender, " U =", round(stat), " p =", round(p, 4),
          " n =", len(older), "older /", len(younger), "younger")


# Plot 3: distribution by age group and gender
chart = sns.catplot(data=clean, x="Age_Group", y="DSQTIRON", hue="Gender",
                    col="Gender", kind="violin", cut=0,
                    height=5, aspect=0.8, legend=False)
chart.set_axis_labels("Age group", "Daily supplemental iron intake (mg)")
chart.savefig("fig3_violin.png", dpi=150)
plt.close()

print()
print("Done. Three figures written.")
