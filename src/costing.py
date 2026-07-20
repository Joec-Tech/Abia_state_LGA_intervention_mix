from __future__ import annotations
import numpy as np
import pandas as pd
from .config import (
    COST_LIBRARY, USD_TO_NGN, SCENARIO_COVERAGE, TREATMENT_COST_SAVED_USD_2024,
    WTP_PER_CASE_AVERTED_NGN, LSM_TARGETABLE_POPULATION_SHARE,
)


def monthly_cost(intervention: str, delta_coverage: float, row: pd.Series, bau_cases_month: float) -> float:
    """Incremental financial/economic proxy in 2024 USD for one forecast month."""
    if delta_coverage <= 0:
        return 0.0
    unit = COST_LIBRARY[intervention]["base_usd_2024"]
    population = float(row["population_2026"])

    if intervention == "CM":
        denominator = bau_cases_month
        return delta_coverage * denominator * unit
    if intervention == "IPTp":
        monthly_pregnancies = float(row["annual_births_2026"]) / 12
        return delta_coverage * monthly_pregnancies * unit
    if intervention == "PMC":
        under2 = float(row["under2_population_2026"])
        return delta_coverage * under2 * unit / 12
    if intervention == "Vac":
        monthly_birth_cohort = float(row["annual_births_2026"]) / 12
        return delta_coverage * monthly_birth_cohort * unit
    if intervention in {"Pyr", "Dual AI"}:
        return delta_coverage * population * unit / 12
    if intervention == "LSM":
        return delta_coverage * population * LSM_TARGETABLE_POPULATION_SHARE * unit / 12
    raise KeyError(intervention)


def add_cost_effectiveness(
    monthly_scenarios: pd.DataFrame,
    cumulative_scenarios: pd.DataFrame,
    meta: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = monthly_scenarios.copy()
    costs = []
    meta_index = meta.set_index("LGA")

    for (lga, scenario, date), block in monthly.groupby(["LGA", "scenario", "date"]):
        mrow = meta_index.loc[lga]
        mix = mrow["mix_list"]
        month_idx = int(block["month_index"].iloc[0])
        bau_cases = float(block["bau_cases"].sum())
        programme_cost = 0.0
        breakdown = {}
        for intervention in mix:
            cov_col = f"coverage_{intervention}"
            current_cov = SCENARIO_COVERAGE["BAU"][intervention]
            scenario_cov = float(block[cov_col].iloc[0])
            delta = max(scenario_cov - current_cov, 0.0)
            value = monthly_cost(intervention, delta, mrow, bau_cases)
            breakdown[intervention] = value
            programme_cost += value
        cases_averted = float(block["cases_averted"].sum())
        treatment_savings = cases_averted * TREATMENT_COST_SAVED_USD_2024
        costs.append({
            "LGA": lga, "scenario": scenario, "date": date,
            "programme_cost_usd_2024": programme_cost,
            "treatment_savings_usd_2024": treatment_savings,
            "net_cost_usd_2024": programme_cost - treatment_savings,
            **{f"cost_{i}_usd_2024": v for i, v in breakdown.items()},
        })

    monthly_cost_df = pd.DataFrame(costs)
    cumulative_cost = monthly_cost_df.groupby(["LGA", "scenario"], as_index=False)[
        ["programme_cost_usd_2024", "treatment_savings_usd_2024", "net_cost_usd_2024"]
    ].sum()

    results = cumulative_scenarios.merge(cumulative_cost, on=["LGA", "scenario"], how="left")
    results["programme_cost_ngn"] = results["programme_cost_usd_2024"] * USD_TO_NGN
    results["treatment_savings_ngn"] = results["treatment_savings_usd_2024"] * USD_TO_NGN
    results["net_cost_ngn"] = results["net_cost_usd_2024"] * USD_TO_NGN
    results["net_cost_per_case_averted_ngn"] = np.where(
        results["cases_averted_24m"] > 0,
        results["net_cost_ngn"] / results["cases_averted_24m"],
        np.nan,
    )
    results["net_monetary_benefit_ngn"] = (
        results["cases_averted_24m"] * WTP_PER_CASE_AVERTED_NGN - results["net_cost_ngn"]
    )
    return monthly_cost_df, results


def incremental_cea(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    scenario_order = ["BAU", "Scenario 1", "Scenario 2", "Target", "High", "Maximum"]
    for lga, block in results.groupby("LGA"):
        block = block.set_index("scenario").loc[scenario_order].reset_index()
        prev_cost = prev_effect = 0.0
        for _, r in block.iterrows():
            inc_cost = r["net_cost_ngn"] - prev_cost
            inc_effect = r["cases_averted_24m"] - prev_effect
            icer = inc_cost / inc_effect if inc_effect > 0 else np.nan
            rows.append({
                "LGA": lga, "scenario": r["scenario"],
                "incremental_net_cost_ngn": inc_cost,
                "incremental_cases_averted": inc_effect,
                "incremental_cost_per_case_averted_ngn": icer,
            })
            prev_cost = r["net_cost_ngn"]
            prev_effect = r["cases_averted_24m"]
    return pd.DataFrame(rows)


def recommended_scenario(prevalence: float) -> str:
    # Transparent burden rule; not a universal national policy threshold.
    if prevalence >= 15:
        return "High"
    if prevalence >= 10:
        return "Target"
    if prevalence >= 5:
        return "Scenario 2"
    return "Scenario 1"


def build_government_recommendations(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lga, block in results.groupby("LGA"):
        prevalence = float(block["prevalence"].iloc[0])
        preferred = recommended_scenario(prevalence)
        r = block[block["scenario"] == preferred].iloc[0]
        rows.append({
            "LGA": lga,
            "prevalence": prevalence,
            "recommended_mix": r["recommended_mix"],
            "planning_scenario": preferred,
            "forecast_bau_cases_24m": r["bau_cases_24m"],
            "projected_cases_with_mix_24m": r["scenario_cases_24m"],
            "cases_averted_24m": r["cases_averted_24m"],
            "percent_averted": r["percent_averted"],
            "programme_cost_ngn": r["programme_cost_ngn"],
            "net_cost_per_case_averted_ngn": r["net_cost_per_case_averted_ngn"],
            "recommendation_basis": "Prevalence-based minimum planning scenario; coverage and cost assumptions are editable.",
        })
    return pd.DataFrame(rows).sort_values(["prevalence", "cases_averted_24m"], ascending=False)
