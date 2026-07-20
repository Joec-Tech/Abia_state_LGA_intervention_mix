# Model methods

## 1. Forecast counterfactual

For each LGA `l` and case stratum `g` (pregnant women, under five, age five plus), the observed monthly series is transformed as:

`z(l,g,t) = log(1 + y(l,g,t))`.

A constrained candidate set of `SARIMA(p,d,q)(P,D,Q)[12]` models is assessed using the last 12 observed months as a validation set. Candidate selection prioritises validation RMSE and then AIC. A seasonal-naive forecast is retained as a benchmark. The selected model is refitted to all observations and produces a 24-month point forecast for May 2026–April 2028 with 80% and 95% intervals.

The three stratum forecasts are summed to obtain the total LGA business-as-usual forecast.

## 2. Intervention scenarios

For intervention `i`, scenario `s`, month `t`, and stratum `g`, effective coverage ramps linearly from BAU coverage to the scenario target over 12 months.

Residual risk is:

`R(l,g,s,t) = product_i [1 - C(i,s,t) E(i)]`,

using only interventions in the LGA's recommended package and only those applicable to stratum `g`.

Scenario cases are:

`Y_s = Y_BAU × R_s / R_BAU`.

Cases averted are:

`A_s = Y_BAU - Y_s`.

Low/high impact bounds combine SARIMA forecast bounds with low/high intervention-effect assumptions. These are scenario envelopes rather than formal posterior credible intervals.

## 3. Population

The model uses final 2006 census LGA counts and projects them to 2026 using the compound annual growth rate implied by the official NPC/NBS Abia State estimates for 2006 and 2016:

`g = (3,727,347 / 2,845,380)^(1/10) - 1 = 2.7368%`.

`N_l,2026 = N_l,2006 × (1 + g)^20`.

This is a transparent planning projection, not a new census estimate. The project includes the source count and the projected value for each LGA.

## 4. Costs

Published cost estimates are converted to 2024 USD using US CPI-U where source years are available. The model then converts 2024 USD to NGN using an editable planning exchange rate.

Cost denominators are intervention-specific:

- CM: additionally reached forecast malaria cases;
- IPTp: estimated monthly pregnancies/birth cohorts;
- PMC: under-two population proxy;
- vaccine: monthly birth cohort receiving a four-dose R21 course;
- pyrethroid and Dual-AI nets: additional person-years protected;
- LSM: additional person-years protected within the targetable ecological share.

Treatment-cost savings equal cases averted multiplied by the referenced diagnosis-plus-uncomplicated-treatment cost.

`Net cost = programme cost - treatment-cost savings`.

`Net cost per case averted = net cost / cases averted`.

## 5. Policy scenario rule

The report highlights a transparent minimum planning scenario:

- prevalence 15% or more: High;
- prevalence 10–14.99%: Target;
- prevalence 5–9.99%: Scenario 2;
- prevalence below 5%: Scenario 1.

This is an editable decision rule, not a WHO threshold or an empirically estimated optimum. Government can run any coverage scenario in `src/config.py`.

## 6. Main limitations

- All 64 observations map directly to the complete January 2021–April 2026 monthly calendar.
- Only 64 observations are available per LGA; long-horizon SARIMA uncertainty can be wide.
- The case data are not adjusted for reporting completeness, testing intensity or structural breaks.
- Intervention effects are literature-informed planning parameters rather than Abia-specific causal estimates.
- The residual-risk layer does not capture herd effects, transmission feedback, immunity or mosquito dynamics.
- Current LGA populations are projections from the 2006 census, not direct 2026 enumerations.
- Cost transferability across countries and implementation platforms is uncertain.
