from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .config import SCENARIO_COVERAGE, OUTPUT_DIR

SCENARIO_ORDER = ["BAU", "Scenario 1", "Scenario 2", "Target", "High", "Maximum"]


def safe_name(text: str) -> str:
    return "_".join(text.replace("/", "-").split())


def compact_ngn(value: float) -> str:
    if pd.isna(value):
        return "–"
    if abs(value) >= 1e9:
        return f"NGN {value/1e9:.1f}bn"
    if abs(value) >= 1e6:
        return f"NGN {value/1e6:.1f}m"
    if abs(value) >= 1e3:
        return f"NGN {value/1e3:.1f}k"
    return f"NGN {value:,.0f}"


def plot_lga_report(
    lga: str,
    long_df: pd.DataFrame,
    total_forecast: pd.DataFrame,
    results: pd.DataFrame,
    meta: pd.DataFrame,
    output_dir: Path | None = None,
) -> Path:
    output_dir = output_dir or (OUTPUT_DIR / "lga_reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    mrow = meta[meta["LGA"] == lga].iloc[0]
    history = long_df[long_df["LGA"] == lga].sort_values("date")
    forecast = total_forecast[total_forecast["LGA"] == lga].sort_values("date")
    block = results[results["LGA"] == lga].set_index("scenario").loc[SCENARIO_ORDER].reset_index()
    mix = mrow["mix_list"]

    fig = plt.figure(figsize=(16, 13))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1.0], hspace=0.32, wspace=0.24)

    # Panel A: observed history and SARIMA forecast
    ax = fig.add_subplot(gs[0, 0])
    ax.plot(history["date"], history["Total_incidence_cases"], marker="o", markersize=2.5, linewidth=1.2, label="Observed cases")
    ax.plot(forecast["date"], forecast["bau_mean"], linewidth=2, label="SARIMA BAU forecast")
    ax.fill_between(forecast["date"], forecast["bau_lower80"], forecast["bau_upper80"], alpha=0.2, label="80% forecast interval")
    ax.axvline(history.loc[history["Total_incidence_cases"].notna(), "date"].max(), linestyle="--", linewidth=1)
    ax.set_title("A. Monthly malaria cases: observed and 24-month BAU forecast")
    ax.set_ylabel("Cases (log scale)")
    ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8)

    # Panel B: cases averted
    ax = fig.add_subplot(gs[0, 1])
    non_bau = block[block["scenario"] != "BAU"]
    y = non_bau["cases_averted_24m"].to_numpy()
    lo = y - non_bau["cases_averted_low_24m"].to_numpy()
    hi = non_bau["cases_averted_high_24m"].to_numpy() - y
    bars = ax.bar(non_bau["scenario"], y, alpha=0.8)
    ax.set_title("B. Cumulative cases averted over 24 months")
    ax.set_ylabel("Cases averted")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    for b, val in zip(bars, y):
        ax.text(b.get_x()+b.get_width()/2, b.get_height(), f"{val:,.0f}", ha="center", va="bottom", fontsize=8)

    # Panel C: cost-effectiveness
    ax = fig.add_subplot(gs[1, 0])
    cer = non_bau["net_cost_per_case_averted_ngn"].to_numpy()
    bars = ax.bar(non_bau["scenario"], cer, alpha=0.8)
    ax.set_title("C. Net cost per case averted")
    ax.set_ylabel("NGN per case averted")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    for b, val in zip(bars, cer):
        ax.text(b.get_x()+b.get_width()/2, b.get_height(), compact_ngn(val), ha="center", va="bottom", fontsize=8)

    # Panel D: coverage table
    ax = fig.add_subplot(gs[1, 1])
    ax.axis("off")
    table_rows = []
    for scenario in SCENARIO_ORDER:
        table_rows.append([scenario] + [f"{SCENARIO_COVERAGE[scenario][i]*100:.0f}%" for i in mix])
    tbl = ax.table(
        cellText=table_rows,
        colLabels=["Scenario"] + mix,
        cellLoc="center",
        colLoc="center",
        loc="upper center",
        bbox=[0, 0.10, 1, 0.82],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.25)
    ax.set_title("D. Effective intervention coverage assumptions", pad=12)

    policy_row = block[block["scenario"] == ("High" if mrow["prevalence"] >= 15 else "Target" if mrow["prevalence"] >= 10 else "Scenario 2" if mrow["prevalence"] >= 5 else "Scenario 1")].iloc[0]
    policy_text = (
        f"Planning implication: use {policy_row['scenario']} as the minimum working scenario under the current burden rule. "
        f"Estimated 24-month impact: {policy_row['cases_averted_24m']:,.0f} cases averted; "
        f"programme cost {compact_ngn(policy_row['programme_cost_ngn'])}; net cost per case averted "
        f"{compact_ngn(policy_row['net_cost_per_case_averted_ngn'])}."
    )

    fig.suptitle(
        f"{lga}: SARIMA Forecast, Recommended Intervention Mix and Cost-Effectiveness\n"
        f"Prevalence {mrow['prevalence']:.2f}% ({mrow['burden']}) | Mix: {mrow['mix']} | Projected 2026 population: {mrow['population_2026']:,}",
        fontsize=15, fontweight="bold", y=0.98,
    )
    fig.subplots_adjust(bottom=0.12, top=0.90)
    fig.text(0.5, 0.060, policy_text, ha="center", va="center", fontsize=9, wrap=True)
    fig.text(
        0.5, 0.025,
        "Population: NPC 2006 final LGA census projected to 2026 using the official Abia 2006–2016 state growth rate. "
        "Costs: published malaria costing studies converted to 2024 USD. Forecast/effect uncertainty is retained in the output tables; all parameters are editable.",
        ha="center", va="center", fontsize=7.5, wrap=True,
    )

    path = output_dir / f"{safe_name(lga)}_SARIMA_intervention_report.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_all_lgas(long_df, total_forecast, results, meta):
    return [plot_lga_report(lga, long_df, total_forecast, results, meta) for lga in meta["LGA"]]
