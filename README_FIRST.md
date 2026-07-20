# Abia Malaria Intervention — Complete VS Code Project

This single folder contains both parts of the project:

1. **Python/SARIMA modelling project** — raw data, processed data, Jupyter notebooks, reusable `src` modules, model outputs, cost-effectiveness tables, and 17 LGA reports.
2. **HTML/CSS/JavaScript web app** — LGA dropdown, automatic recommended intervention mix, 0–100% additional-coverage sliders, projected cases averted, and indicative costs.

## Folder structure

```text
Abia_Malaria_Intervention_Complete_VSCode_Project/
├── data/
│   ├── raw/Abia/                 # 17 original LGA files
│   └── processed/                # dated and population-linked data
├── notebooks/                    # five Jupyter notebooks
├── src/                          # Python modelling source code
│   ├── config.py
│   ├── data.py
│   ├── forecast.py
│   ├── intervention.py
│   ├── costing.py
│   └── plotting.py
├── outputs/
│   ├── forecasts/
│   ├── diagnostics/
│   ├── tables/
│   └── lga_reports/
├── web_app/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── data.js
│   └── data/
├── run_pipeline.py               # rebuild Python model outputs
├── sync_web_app_data.py          # copy outputs into web app and rebuild data.js
├── run_full_refresh.py           # run both steps
├── requirements.txt
└── 01–04 Windows helper files
```

## First run in VS Code on Windows

1. Extract the ZIP.
2. Open `Abia_Malaria_Intervention.code-workspace` in VS Code, or use **File → Open Folder**.
3. Double-click `01_setup_environment.bat` to create `.venv` and install packages.
4. Run the complete Python model and update the app with `02_run_model_and_update_app.bat`.
5. Start the web app with `03_run_web_app.bat`.
6. Your browser should open at `http://127.0.0.1:8000`.

## Run from the VS Code terminal

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_full_refresh.py
python web_app\serve_app.py
```

## Run the notebooks

Open the notebooks in this order:

1. `notebooks/01_data_dates_population.ipynb`
2. `notebooks/02_sarima_forecasting.ipynb`
3. `notebooks/03_intervention_scenarios.ipynb`
4. `notebooks/04_cost_effectiveness_17_reports.ipynb`

Or use `notebooks/00_run_all.ipynb` to run the complete pipeline.

## How the Python model and web app are connected

`python run_pipeline.py` regenerates the SARIMA forecasts and model outputs.

`python sync_web_app_data.py` then copies the updated forecasts and assumptions into `web_app/data/` and rebuilds `web_app/data.js`, which the browser app uses.

`python run_full_refresh.py` performs both operations.

## Historical and forecast periods

- Historical data: January 2021–April 2026
- Forecast period: May 2026–April 2028
- Forecast horizon: 24 months

## Slider interpretation

Because verified current LGA intervention coverage is unavailable, 0–100% is interpreted as **additional effective coverage above the SARIMA business-as-usual forecast**. Zero means no additional scale-up; 100% means the maximum modelled additional reach.
