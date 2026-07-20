from pathlib import Path
import pandas as pd
from src.config import OUTPUT_DIR, PROCESSED_DATA_DIR, COST_LIBRARY, EFFECTIVENESS, SCENARIO_COVERAGE
from src.data import load_all_lgas, population_reference_table
from src.forecast import forecast_all_lgas, aggregate_total_forecast
from src.intervention import evaluate_scenarios
from src.costing import add_cost_effectiveness, incremental_cea, build_government_recommendations
from src.plotting import plot_all_lgas


def parameter_tables():
    cost_rows = []
    for intervention, d in COST_LIBRARY.items():
        cost_rows.append({"intervention": intervention, **d})
    effect_rows = []
    for intervention, d in EFFECTIVENESS.items():
        effect_rows.append({"intervention": intervention, **d})
    coverage_rows = []
    for scenario, cov in SCENARIO_COVERAGE.items():
        for intervention, value in cov.items():
            coverage_rows.append({"scenario": scenario, "intervention": intervention, "coverage": value})
    return pd.DataFrame(cost_rows), pd.DataFrame(effect_rows), pd.DataFrame(coverage_rows)


def main():
    for p in [PROCESSED_DATA_DIR, OUTPUT_DIR / "tables", OUTPUT_DIR / "forecasts", OUTPUT_DIR / "lga_reports", OUTPUT_DIR / "diagnostics"]:
        p.mkdir(parents=True, exist_ok=True)

    long_df, meta, validation = load_all_lgas()
    long_df.to_csv(PROCESSED_DATA_DIR / "Abia_monthly_cases_dated.csv", index=False)
    meta.drop(columns="mix_list").to_csv(PROCESSED_DATA_DIR / "Abia_LGA_metadata_population.csv", index=False)
    validation.to_csv(OUTPUT_DIR / "tables" / "data_validation.csv", index=False)
    population_reference_table(meta).to_csv(OUTPUT_DIR / "tables" / "population_reference_table.csv", index=False)

    print("STAGE forecast", flush=True)
    group_fc, diagnostics, candidates = forecast_all_lgas(long_df, meta)
    print("STAGE forecast done", flush=True)
    total_fc = aggregate_total_forecast(group_fc)
    group_fc.to_csv(OUTPUT_DIR / "forecasts" / "group_SARIMA_forecasts_24m.csv", index=False)
    total_fc.to_csv(OUTPUT_DIR / "forecasts" / "LGA_total_SARIMA_forecasts_24m.csv", index=False)
    diagnostics.to_csv(OUTPUT_DIR / "diagnostics" / "selected_SARIMA_models.csv", index=False)
    candidates.to_csv(OUTPUT_DIR / "diagnostics" / "SARIMA_candidate_models.csv", index=False)

    print("STAGE scenarios", flush=True)
    monthly_scenarios, cumulative = evaluate_scenarios(group_fc, meta)
    print("STAGE scenarios done", flush=True)
    print("STAGE costing", flush=True)
    monthly_costs, results = add_cost_effectiveness(monthly_scenarios, cumulative, meta)
    print("STAGE costing done", flush=True)
    incremental = incremental_cea(results)
    recommendations = build_government_recommendations(results)

    monthly_scenarios.to_csv(OUTPUT_DIR / "tables" / "monthly_intervention_scenarios.csv", index=False)
    monthly_costs.to_csv(OUTPUT_DIR / "tables" / "monthly_costs.csv", index=False)
    results.to_csv(OUTPUT_DIR / "tables" / "LGA_scenario_cost_effectiveness.csv", index=False)
    incremental.to_csv(OUTPUT_DIR / "tables" / "incremental_cost_effectiveness.csv", index=False)
    recommendations.to_csv(OUTPUT_DIR / "tables" / "government_recommendations.csv", index=False)

    costs, effects, coverages = parameter_tables()
    costs.to_csv(OUTPUT_DIR / "tables" / "cost_assumptions_with_sources.csv", index=False)
    effects.to_csv(OUTPUT_DIR / "tables" / "effectiveness_assumptions.csv", index=False)
    coverages.to_csv(OUTPUT_DIR / "tables" / "coverage_scenarios.csv", index=False)

    print("STAGE plots", flush=True)
    paths = plot_all_lgas(long_df, total_fc, results, meta)
    print("STAGE plots done", flush=True)
    print(f"Completed: {len(paths)} LGA reports")
    print(f"Forecast models: {len(diagnostics)} (17 LGAs x 3 strata)")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
