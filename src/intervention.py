from __future__ import annotations
import numpy as np
import pandas as pd
from .config import (
    SCENARIO_COVERAGE, SCALE_UP_MONTHS, EFFECTIVENESS, TARGET_GROUPS,
)


def coverage_at_month(intervention: str, scenario: str, month_index: int, scale_up_months: int = SCALE_UP_MONTHS) -> float:
    """Linear scale-up from BAU coverage to the scenario target."""
    baseline = SCENARIO_COVERAGE["BAU"][intervention]
    target = SCENARIO_COVERAGE[scenario][intervention]
    if scenario == "BAU":
        return baseline
    if scale_up_months <= 0:
        return target
    fraction = min((month_index + 1) / scale_up_months, 1.0)
    return baseline + fraction * (target - baseline)


def residual_risk(mix: list[str], group: str, coverage: dict[str, float], effect_level: str = "base") -> float:
    risk = 1.0
    for intervention in mix:
        if group in TARGET_GROUPS[intervention]:
            efficacy = EFFECTIVENESS[intervention][effect_level]
            risk *= 1 - coverage[intervention] * efficacy
    return max(float(risk), 1e-9)


def evaluate_scenarios(group_forecast: pd.DataFrame, meta: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly_rows = []
    cumulative_rows = []

    for _, mrow in meta.iterrows():
        lga = mrow["LGA"]
        mix = mrow["mix_list"]
        lga_fc = group_forecast[group_forecast["LGA"] == lga].copy()

        for scenario in SCENARIO_COVERAGE:
            scenario_monthly = []
            for month_idx, date in enumerate(sorted(lga_fc["date"].unique())):
                cov = {i: coverage_at_month(i, scenario, month_idx) for i in mix}
                for group in sorted(lga_fc["group"].unique()):
                    row = lga_fc[(lga_fc["date"] == date) & (lga_fc["group"] == group)].iloc[0]
                    rr0_base = residual_risk(mix, group, {i: SCENARIO_COVERAGE["BAU"][i] for i in mix}, "base")
                    rr_base = residual_risk(mix, group, cov, "base")
                    rr0_low = residual_risk(mix, group, {i: SCENARIO_COVERAGE["BAU"][i] for i in mix}, "low")
                    rr_low = residual_risk(mix, group, cov, "low")
                    rr0_high = residual_risk(mix, group, {i: SCENARIO_COVERAGE["BAU"][i] for i in mix}, "high")
                    rr_high = residual_risk(mix, group, cov, "high")

                    ratio_base = min(rr_base / rr0_base, 1.0)
                    ratio_low = min(rr_low / rr0_low, 1.0)
                    ratio_high = min(rr_high / rr0_high, 1.0)

                    bau = float(row["bau_mean"])
                    bau_lo = float(row["bau_lower95"])
                    bau_hi = float(row["bau_upper95"])
                    scenario_cases = bau * ratio_base
                    scenario_cases_lo = bau_lo * ratio_high
                    scenario_cases_hi = bau_hi * ratio_low
                    averted = max(bau - scenario_cases, 0.0)
                    averted_lo = max(bau_lo - scenario_cases_lo, 0.0)
                    averted_hi = max(bau_hi - scenario_cases_hi, 0.0)

                    rec = {
                        "LGA": lga, "date": date, "month_index": month_idx + 1,
                        "group": group, "scenario": scenario,
                        "bau_cases": bau, "scenario_cases": scenario_cases,
                        "cases_averted": averted,
                        "cases_averted_low": min(averted_lo, averted),
                        "cases_averted_high": max(averted_hi, averted),
                    }
                    for i in mix:
                        rec[f"coverage_{i}"] = cov[i]
                    monthly_rows.append(rec)
                    scenario_monthly.append(rec)

            temp = pd.DataFrame(scenario_monthly)
            cumulative = {
                "LGA": lga, "prevalence": mrow["prevalence"], "burden": mrow["burden"],
                "recommended_mix": mrow["mix"], "scenario": scenario,
                "bau_cases_24m": temp["bau_cases"].sum(),
                "scenario_cases_24m": temp["scenario_cases"].sum(),
                "cases_averted_24m": temp["cases_averted"].sum(),
                "cases_averted_low_24m": temp["cases_averted_low"].sum(),
                "cases_averted_high_24m": temp["cases_averted_high"].sum(),
                "percent_averted": 100 * temp["cases_averted"].sum() / max(temp["bau_cases"].sum(), 1e-9),
            }
            for i in mix:
                cumulative[f"target_coverage_{i}"] = SCENARIO_COVERAGE[scenario][i]
            cumulative_rows.append(cumulative)

    return pd.DataFrame(monthly_rows), pd.DataFrame(cumulative_rows)
