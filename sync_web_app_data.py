"""Regenerate the browser application's data files from the Python model outputs.

Run this after ``python run_pipeline.py`` whenever the SARIMA forecasts,
metadata, population estimates, effectiveness assumptions, or costs change.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

from src.config import (
    COST_LIBRARY,
    EFFECTIVENESS,
    FORECAST_HORIZON,
    LSM_TARGETABLE_POPULATION_SHARE,
    TARGET_GROUPS,
    TREATMENT_COST_SAVED_USD_2024,
    USD_TO_NGN,
)

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web_app"
WEB_DATA_DIR = WEB_DIR / "data"
PROCESSED_DIR = ROOT / "data" / "processed"
FORECAST_DIR = ROOT / "outputs" / "forecasts"
TABLE_DIR = ROOT / "outputs" / "tables"


def _records_by_lga(group_fc: pd.DataFrame) -> dict[str, list[dict]]:
    required = {
        "date", "LGA", "group", "bau_mean", "bau_lower95", "bau_upper95"
    }
    missing = required.difference(group_fc.columns)
    if missing:
        raise ValueError(f"Forecast file is missing columns: {sorted(missing)}")

    group_fc = group_fc.copy()
    group_fc["date"] = pd.to_datetime(group_fc["date"])
    result: dict[str, list[dict]] = {}

    for lga, lga_df in group_fc.groupby("LGA", sort=True):
        rows: list[dict] = []
        for date, date_df in lga_df.groupby("date", sort=True):
            by_group = date_df.set_index("group")
            row: dict[str, object] = {"date": date.strftime("%Y-%m-%d")}
            total = 0.0
            lower95 = 0.0
            upper95 = 0.0
            for group in ("PW", "U5", "A5"):
                if group not in by_group.index:
                    raise ValueError(f"Missing group {group!r} for {lga} on {date.date()}")
                rec = by_group.loc[group]
                mean = float(rec["bau_mean"])
                lo = max(float(rec["bau_lower95"]), 0.0)
                hi = max(float(rec["bau_upper95"]), 0.0)
                row[group] = mean
                row[f"{group}Lower95"] = lo
                row[f"{group}Upper95"] = hi
                total += mean
                lower95 += lo
                upper95 += hi
            row["total"] = total
            row["lower95"] = lower95
            row["upper95"] = upper95
            rows.append(row)
        result[str(lga)] = rows
    return result


def _metadata(meta_df: pd.DataFrame) -> dict[str, dict]:
    output: dict[str, dict] = {}
    for row in meta_df.itertuples(index=False):
        mix_text = str(row.mix)
        output[str(row.LGA)] = {
            "prevalence": float(row.prevalence),
            "burden": str(row.burden),
            "mix": [item.strip() for item in mix_text.split("+")],
            "mixText": mix_text,
            "population2006": int(row.population_2006),
            "population2026": int(row.population_2026),
            "under5Population2026": int(row.under5_population_2026),
            "under2Population2026": int(row.under2_population_2026),
            "annualBirths2026": int(row.annual_births_2026),
            "populationSource": str(row.population_source),
        }
    return output


def _effectiveness() -> dict[str, dict]:
    output: dict[str, dict] = {}
    for intervention, values in EFFECTIVENESS.items():
        output[intervention] = {
            "low": float(values["low"]),
            "base": float(values["base"]),
            "high": float(values["high"]),
            "note": str(values["note"]),
            "source": str(values["source"]),
            "url": str(values["url"]),
            "targets": list(TARGET_GROUPS[intervention]),
        }
    return output


def _costs() -> dict[str, dict]:
    output: dict[str, dict] = {}
    for intervention, values in COST_LIBRARY.items():
        output[intervention] = {
            "low": float(values["low_usd_2024"]),
            "base": float(values["base_usd_2024"]),
            "high": float(values["high_usd_2024"]),
            "unit": str(values["unit"]),
            "source": str(values["source"]),
            "url": str(values["url"]),
        }
    return output


def main() -> None:
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

    meta_path = PROCESSED_DIR / "Abia_LGA_metadata_population.csv"
    forecast_path = FORECAST_DIR / "group_SARIMA_forecasts_24m.csv"
    if not meta_path.exists() or not forecast_path.exists():
        raise FileNotFoundError(
            "Required model outputs are missing. Run `python run_pipeline.py` first."
        )

    meta_df = pd.read_csv(meta_path)
    group_fc = pd.read_csv(forecast_path)
    group_fc["date"] = pd.to_datetime(group_fc["date"])

    forecast_start = group_fc["date"].min().strftime("%Y-%m-%d")
    forecast_end = group_fc["date"].max().strftime("%Y-%m-%d")

    payload = {
        "metadata": _metadata(meta_df),
        "forecasts": _records_by_lga(group_fc),
        "effectiveness": _effectiveness(),
        "costs": _costs(),
        "settings": {
            "forecastStart": forecast_start,
            "forecastEnd": forecast_end,
            "horizonMonths": int(FORECAST_HORIZON),
            "usdToNgn": float(USD_TO_NGN),
            "lsmTargetableShare": float(LSM_TARGETABLE_POPULATION_SHARE),
            "treatmentCostSavedUsd2024": float(TREATMENT_COST_SAVED_USD_2024),
            "coverageInterpretation": (
                "additional effective coverage above the SARIMA business-as-usual forecast"
            ),
            "populationReference": (
                "NPC 2006 final LGA census; projected to 2026 using the Abia "
                "2006–2016 annual growth rate implied by NPC/NBS state estimates."
            ),
        },
    }

    (WEB_DIR / "data.js").write_text(
        "window.ABIA_APP_DATA = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )

    # Keep transparent CSV copies beside the browser app.
    copy_map = {
        meta_path: WEB_DATA_DIR / "lga_metadata_population.csv",
        forecast_path: WEB_DATA_DIR / "group_SARIMA_forecasts_24m.csv",
        TABLE_DIR / "effectiveness_assumptions.csv": WEB_DATA_DIR / "effectiveness_assumptions.csv",
        TABLE_DIR / "cost_assumptions_with_sources.csv": WEB_DATA_DIR / "cost_assumptions_with_sources.csv",
        TABLE_DIR / "population_reference_table.csv": WEB_DATA_DIR / "population_reference_table.csv",
    }
    for source, destination in copy_map.items():
        if not source.exists():
            raise FileNotFoundError(f"Expected output not found: {source}")
        shutil.copy2(source, destination)

    print(f"Updated: {WEB_DIR / 'data.js'}")
    print(f"Updated CSV folder: {WEB_DATA_DIR}")
    print(f"LGAs embedded: {len(payload['metadata'])}")
    print(f"Forecast period: {forecast_start} to {forecast_end}")


if __name__ == "__main__":
    main()
