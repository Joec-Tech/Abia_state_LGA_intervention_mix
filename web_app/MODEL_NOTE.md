# Model note: intervention coverage without a measured BAU coverage

## Why the slider starts at zero

The SARIMA component provides a business-as-usual forecast of reported malaria cases from May 2026 to April 2028. However, reliable LGA-specific baseline coverage for case management, IPTp, nets, PMC, vaccination and LSM is not available.

Inventing baseline coverage would make the intervention results appear more precise than the evidence supports. The application therefore defines each slider as *additional effective coverage intensity above BAU*.

## Interpretation

- Slider = 0%: the SARIMA BAU forecast is unchanged.
- Slider = 50%: half of the maximum modelled intervention effect is applied to eligible forecast cases.
- Slider = 100%: the full selected effectiveness parameter is applied to eligible forecast cases.

For example, under the base-effectiveness setting, vaccination has a modelled effect of 50% among eligible children. A 60% slider therefore produces an effective proportional reduction of `0.60 × 0.50 = 0.30` before combination with other interventions.

## Combined effects

Effects are combined multiplicatively:

`R = product(1 - coverage × effectiveness)`

This prevents the combined reduction from exceeding 100%, but assumes independent proportional effects and no explicit synergy or antagonism.

## Important limitation

The historical case series already reflects whatever interventions were operating during 2021–2026. Therefore, the application does not estimate a true no-intervention counterfactual. Its output should be described as **potential additional cases averted under the selected modelling assumptions**, not as a guaranteed or causally identified programme effect.

## What would improve the model

Replace the additional-intensity interpretation with measured baseline and target coverage once LGA-level coverage data become available. The impact equation can then compare residual risk under target coverage with residual risk under measured BAU coverage.
