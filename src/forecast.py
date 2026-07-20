from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.statespace.sarimax import SARIMAX
from .config import (
    VALIDATION_MONTHS, FORECAST_HORIZON, SARIMA_CANDIDATES,
    MAX_FORECAST_MULTIPLIER, REQUESTED_END, GROUP_COLUMNS,
)

warnings.filterwarnings("ignore")


def _seasonal_naive(train: pd.Series, steps: int, period: int = 12) -> np.ndarray:
    vals = train.dropna().to_numpy(dtype=float)
    if len(vals) == 0:
        return np.zeros(steps)
    if len(vals) < period:
        return np.repeat(vals[-1], steps)
    pattern = vals[-period:]
    return np.resize(pattern, steps)


def _mase(actual: np.ndarray, pred: np.ndarray, train: pd.Series, period: int = 12) -> float:
    clean = train.dropna().to_numpy(dtype=float)
    if len(clean) <= period:
        return np.nan
    denom = np.mean(np.abs(clean[period:] - clean[:-period]))
    if denom <= 0:
        return np.nan
    return float(np.mean(np.abs(actual - pred)) / denom)


def _fit_sarima(train: pd.Series, order, seasonal_order):
    z = np.log1p(train.astype(float))
    model = SARIMAX(
        z,
        order=order,
        seasonal_order=seasonal_order,
        trend="n",
        enforce_stationarity=False,
        enforce_invertibility=False,
        missing="none",
        simple_differencing=True,
    )
    return model.fit(disp=False, maxiter=50, method="lbfgs")


def select_and_forecast(series: pd.Series, lga: str, group: str):
    series = series.astype(float).dropna().copy()
    n = len(series)
    train = series.iloc[: n - VALIDATION_MONTHS]
    test = series.iloc[n - VALIDATION_MONTHS :]
    actual = test.to_numpy(dtype=float)

    naive_pred = _seasonal_naive(train, VALIDATION_MONTHS)
    naive_rmse = float(np.sqrt(mean_squared_error(actual, naive_pred)))
    naive_mae = float(mean_absolute_error(actual, naive_pred))

    candidate_rows = []
    fitted_candidates = []
    scale = max(float(np.nanmax(train.to_numpy(dtype=float))), 1.0)

    for order, seasonal_order in SARIMA_CANDIDATES:
        try:
            fit = _fit_sarima(train, order, seasonal_order)
            pred_log = fit.get_forecast(VALIDATION_MONTHS).predicted_mean
            pred = np.maximum(np.expm1(np.asarray(pred_log, dtype=float)), 0)
            if (not np.all(np.isfinite(pred))) or pred.max() > MAX_FORECAST_MULTIPLIER * scale:
                raise ValueError("implausible validation forecast")
            rmse = float(np.sqrt(mean_squared_error(actual, pred)))
            mae = float(mean_absolute_error(actual, pred))
            mase = _mase(actual, pred, train)
            candidate_rows.append({
                "LGA": lga, "group": group, "order": str(order),
                "seasonal_order": str(seasonal_order), "rmse": rmse,
                "mae": mae, "mase": mase, "aic": float(fit.aic), "status": "ok"
            })
            fitted_candidates.append((rmse, fit.aic, order, seasonal_order))
        except Exception as exc:
            candidate_rows.append({
                "LGA": lga, "group": group, "order": str(order),
                "seasonal_order": str(seasonal_order), "rmse": np.nan,
                "mae": np.nan, "mase": np.nan, "aic": np.nan,
                "status": f"failed: {type(exc).__name__}"
            })

    forecast_dates = pd.date_range(REQUESTED_END + pd.offsets.MonthBegin(1), periods=FORECAST_HORIZON, freq="MS")

    if fitted_candidates:
        _, _, best_order, best_seasonal = sorted(fitted_candidates, key=lambda x: (x[0], x[1]))[0]
        selected_validation = [r for r in candidate_rows if r["order"] == str(best_order) and r["seasonal_order"] == str(best_seasonal) and r["status"] == "ok"][0]
        sarima_beats_naive = bool(selected_validation["rmse"] < naive_rmse)

        # A seasonal-naive model is a mandatory benchmark.  If the best SARIMA
        # candidate does not improve validation RMSE, use the benchmark rather
        # than retaining an inferior model simply because it converged.
        if not sarima_beats_naive:
            mean = _seasonal_naive(series, FORECAST_HORIZON)
            lower80 = mean * 0.75
            upper80 = mean * 1.25
            lower95 = mean * 0.50
            upper95 = mean * 1.50
            method = "seasonal-naive fallback after validation"
            full_aic = np.nan
            lb_p = np.nan
            warning = "Best SARIMA validation RMSE was not better than seasonal naive"
        else:
            full_fit = _fit_sarima(series, best_order, best_seasonal)
            fc = full_fit.get_forecast(FORECAST_HORIZON)
            mean_log = np.asarray(fc.predicted_mean, dtype=float)
            ci80 = np.asarray(fc.conf_int(alpha=0.20), dtype=float)
            ci95 = np.asarray(fc.conf_int(alpha=0.05), dtype=float)
            mean = np.maximum(np.expm1(mean_log), 0)
            lower80 = np.maximum(np.expm1(ci80[:, 0]), 0)
            upper80 = np.maximum(np.expm1(ci80[:, 1]), 0)
            lower95 = np.maximum(np.expm1(ci95[:, 0]), 0)
            upper95 = np.maximum(np.expm1(ci95[:, 1]), 0)
            max_allowed = MAX_FORECAST_MULTIPLIER * max(float(np.nanmax(series)), 1.0)
            explosive = bool((not np.all(np.isfinite(mean))) or np.nanmax(mean) > max_allowed)
            if explosive:
                mean = _seasonal_naive(series, FORECAST_HORIZON)
                lower80 = mean * 0.75
                upper80 = mean * 1.25
                lower95 = mean * 0.50
                upper95 = mean * 1.50
                method = "seasonal-naive fallback after explosive SARIMA refit"
                warning = "Full-series SARIMA forecast was implausibly large"
            else:
                method = "SARIMA"
                warning = ""
            residuals = np.asarray(full_fit.resid, dtype=float)
            residuals = residuals[np.isfinite(residuals)]
            try:
                lb_p = float(acorr_ljungbox(residuals, lags=[min(12, max(1, len(residuals)//4))], return_df=True)["lb_pvalue"].iloc[0])
            except Exception:
                lb_p = np.nan
            full_aic = float(full_fit.aic)

        diagnostics = {
            "LGA": lga, "group": group, "selected_method": method,
            "selected_order": str(best_order), "selected_seasonal_order": str(best_seasonal),
            "validation_rmse": selected_validation["rmse"],
            "validation_mae": selected_validation["mae"],
            "validation_mase": selected_validation["mase"],
            "seasonal_naive_rmse": naive_rmse, "seasonal_naive_mae": naive_mae,
            "sarima_beats_naive": sarima_beats_naive,
            "aic_full_fit": full_aic, "ljung_box_pvalue": lb_p,
            "forecast_warning": warning,
        }
    else:
        mean = _seasonal_naive(series, FORECAST_HORIZON)
        lower80, upper80 = mean*0.75, mean*1.25
        lower95, upper95 = mean*0.50, mean*1.50
        diagnostics = {
            "LGA": lga, "group": group, "selected_method": "seasonal-naive fallback",
            "selected_order": "None", "selected_seasonal_order": "None",
            "validation_rmse": naive_rmse, "validation_mae": naive_mae,
            "validation_mase": np.nan, "seasonal_naive_rmse": naive_rmse,
            "seasonal_naive_mae": naive_mae, "sarima_beats_naive": False,
            "aic_full_fit": np.nan, "ljung_box_pvalue": np.nan,
            "forecast_warning": "All SARIMA candidates failed",
        }

    forecast = pd.DataFrame({
        "date": forecast_dates, "LGA": lga, "group": group,
        "bau_mean": mean, "bau_lower80": lower80, "bau_upper80": upper80,
        "bau_lower95": lower95, "bau_upper95": upper95,
    })
    return forecast, diagnostics, pd.DataFrame(candidate_rows)


def forecast_all_lgas(long_df: pd.DataFrame, meta: pd.DataFrame):
    forecasts, diagnostics, candidates = [], [], []
    for _, mrow in meta.iterrows():
        lga_df = long_df[long_df["LGA"] == mrow["LGA"]].sort_values("date").set_index("date")
        for group, col in GROUP_COLUMNS.items():
            print(f"Forecasting {mrow['LGA']} - {group}", flush=True)
            fc, diag, cand = select_and_forecast(lga_df[col], mrow["LGA"], group)
            forecasts.append(fc)
            diagnostics.append(diag)
            candidates.append(cand)
    return pd.concat(forecasts, ignore_index=True), pd.DataFrame(diagnostics), pd.concat(candidates, ignore_index=True)


def aggregate_total_forecast(group_forecast: pd.DataFrame) -> pd.DataFrame:
    cols = ["bau_mean", "bau_lower80", "bau_upper80", "bau_lower95", "bau_upper95"]
    return group_forecast.groupby(["LGA", "date"], as_index=False)[cols].sum()
