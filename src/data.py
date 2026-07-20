from __future__ import annotations
import numpy as np
import pandas as pd
from .config import (
    LGA_INFO, RAW_DATA_DIR, REQUESTED_START, REQUESTED_END,
    POPULATION_GROWTH_RATE, POPULATION_PROJECTION_YEAR, ABIA_POP_2006,
    ABIA_POP_2016, UNDER5_SHARE, UNDER2_SHARE, CRUDE_BIRTH_RATE,
)

REQUIRED_COLUMNS = ["periodname", "PW", "Under_5yrs", "Above_5yrs", "Total_incidence_cases"]


def build_calendar() -> pd.DatetimeIndex:
    return pd.date_range(REQUESTED_START, REQUESTED_END, freq="MS")


def load_lga_metadata() -> pd.DataFrame:
    meta = pd.DataFrame(LGA_INFO)
    meta["mix_list"] = meta["mix"].str.split(r"\s*\+\s*", regex=True)
    years = POPULATION_PROJECTION_YEAR - 2006
    factor = (1 + POPULATION_GROWTH_RATE) ** years
    meta["population_2026"] = (meta["population_2006"] * factor).round().astype(int)
    meta["under5_population_2026"] = (meta["population_2026"] * UNDER5_SHARE).round().astype(int)
    meta["under2_population_2026"] = (meta["population_2026"] * UNDER2_SHARE).round().astype(int)
    meta["annual_births_2026"] = (meta["population_2026"] * CRUDE_BIRTH_RATE).round().astype(int)
    meta["population_source"] = (
        "NPC 2006 final LGA census; projected to 2026 using the Abia 2006-2016 "
        "annual growth rate implied by NPC/NBS state estimates"
    )
    return meta


def load_one_lga(row: pd.Series) -> pd.DataFrame:
    path = RAW_DATA_DIR / row["filename"]
    df = pd.read_csv(path, sep="\t")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{row['LGA']}: missing columns {missing}")

    calendar = build_calendar()
    if len(df) != len(calendar):
        raise ValueError(
            f"{row['LGA']}: expected {len(calendar)} monthly observations for "
            f"{REQUESTED_START:%b %Y}--{REQUESTED_END:%b %Y}, but found {len(df)}."
        )

    df = df.copy()
    df["date"] = calendar
    df["LGA"] = row["LGA"]
    df["date_alignment"] = "Direct monthly mapping: Jan 2021--Apr 2026"

    calculated = df["PW"] + df["Under_5yrs"] + df["Above_5yrs"]
    df["total_check"] = calculated == df["Total_incidence_cases"]
    if not df["total_check"].all():
        bad = int((~df["total_check"]).sum())
        raise ValueError(f"{row['LGA']}: {bad} rows fail the total-case check")

    # Preserve the complete monthly calendar in chronological order.
    df = df.set_index("date").reindex(calendar)
    df.index.name = "date"
    df["LGA"] = row["LGA"]
    df["date_alignment"] = "Direct monthly mapping: Jan 2021--Apr 2026"
    return df.reset_index()


def load_all_lgas() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    meta = load_lga_metadata()
    frames = []
    validation = []
    for _, row in meta.iterrows():
        df = load_one_lga(row)
        frames.append(df)
        validation.append({
            "LGA": row["LGA"],
            "rows_in_calendar": len(df),
            "observed_rows": int(df["Total_incidence_cases"].notna().sum()),
            "missing_month": "None",
            "totals_valid": bool(df.loc[df["Total_incidence_cases"].notna(), "total_check"].all()),
            "first_observed": str(df.loc[df["Total_incidence_cases"].notna(), "date"].min().date()),
            "last_observed": str(df.loc[df["Total_incidence_cases"].notna(), "date"].max().date()),
        })
    long_df = pd.concat(frames, ignore_index=True)
    validation_df = pd.DataFrame(validation)
    return long_df, meta, validation_df


def population_reference_table(meta: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "LGA", "population_2006", "population_2026", "under5_population_2026",
        "under2_population_2026", "annual_births_2026", "population_source"
    ]
    out = meta[cols].copy()
    out["projection_growth_rate_percent"] = POPULATION_GROWTH_RATE * 100
    out["abia_state_population_2006"] = ABIA_POP_2006
    out["abia_state_population_2016"] = ABIA_POP_2016
    return out
