# Abia Malaria Intervention Scenario Explorer

## Purpose

This is a static HTML/CSS/JavaScript application for exploring the 24-month potential impact of LGA-specific malaria intervention packages in Abia State.

## Open the app

Double-click `index.html`. No installation, web server, Python environment or internet connection is required for the calculations and charts. Internet access is only needed when opening evidence-source links.

## How the app works

1. Select one of the 17 LGAs from the dropdown.
2. The LGA prevalence, burden classification, projected population and recommended intervention mix appear automatically.
3. Only interventions recommended for that LGA are displayed as sliders.
4. Move each slider from 0% to 100% to define a policy scenario.
5. Select low, base or high intervention-effectiveness and cost assumptions.
6. Review the SARIMA business-as-usual forecast, projected scenario cases, cases averted, programme cost and net cost per case averted.
7. Download the monthly scenario as a CSV or print the report.

## Critical interpretation of the sliders

Verified current intervention coverage by LGA is unavailable. The sliders are therefore interpreted as **additional effective coverage intensity above the SARIMA business-as-usual forecast**:

- 0% = no additional scale-up;
- 100% = maximum modelled additional reach for the selected intervention.

They are not estimates of measured total intervention coverage. This avoids inventing a baseline coverage value, but it means the results are prevention-potential scenarios rather than validated causal impact estimates.

## Epidemiological calculation

For group `g`, month `t`, and LGA-specific intervention package `M`, remaining risk is:

`R(g,t) = product over i in M of [1 - coverage(i,t) × effectiveness(i)]`

Scenario cases are:

`scenario cases(g,t) = SARIMA BAU cases(g,t) × R(g,t)`

The model forecasts pregnant women, children under five, and persons aged five years and above separately so that targeted interventions are applied only to eligible groups.

## Coverage scale-up

When gradual scale-up is enabled, the selected coverage is reached linearly over the first 12 forecast months and maintained during months 13–24.

## Files

- `index.html`: page structure
- `styles.css`: visual design
- `app.js`: dropdown, sliders, calculations, charts and export logic
- `data.js`: embedded LGA metadata and 24-month SARIMA forecasts
- `data/`: transparent CSV copies of the metadata, forecasts, population, effectiveness and cost assumptions
- `MODEL_NOTE.md`: methodological explanation and limitations

## Editing the app

### Change an LGA package

Edit the `metadata` object in `data.js`, or regenerate `data.js` from the supplied CSV files.

### Change effectiveness or cost assumptions

Edit the relevant values in `data.js`. The transparent source tables are also available under `data/`.

### Change the initial exchange rate

Edit `usdToNgn` under `settings` in `data.js`.

## Policy use

The app is suitable for scenario planning, stakeholder consultation and data-gap identification. It is not a substitute for verified baseline coverage, local programme costs, budget-impact analysis, causal evaluation or a calibrated malaria transmission model.
