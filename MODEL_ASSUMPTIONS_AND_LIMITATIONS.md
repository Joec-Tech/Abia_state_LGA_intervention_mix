# Model assumptions and limitations

## A. Surveillance data

1. The 64 rows in each file are in chronological order.
2. The declared period is January 2021–April 2026, which contains exactly 64 monthly observations.
3. The 64 supplied observations are mapped directly and sequentially to January 2021–April 2026; no missing month is assumed.
4. `PW`, `Under_5yrs` and `Above_5yrs` are mutually exclusive and sum to `Total_incidence_cases`.
5. Counts are used as reported; no adjustment is made for reporting completeness, testing intensity, facility attendance or case-definition changes.
6. The first observation is assigned to January 2021 and the final observation to April 2026. The forecast period is May 2026–April 2028.

## B. Forecast model

1. Monthly seasonality has period 12.
2. A log1p transform is used to stabilize variance and prevent negative forecasts after back-transformation.
3. The last 12 observed months form the validation set.
4. The candidate set is deliberately small because each series is short.
5. Validation RMSE is the main selection criterion; AIC and Ljung–Box p-values are diagnostic, not sole selection rules.
6. Seasonal naïve is a mandatory benchmark and may replace an underperforming SARIMA candidate.
7. Forecast prediction intervals represent time-series uncertainty only; they do not include intervention-parameter or cost uncertainty.
8. No rainfall, temperature, stock-out, campaign or reporting covariates are included. With reliable covariates, SARIMAX would be preferable.

## C. Population

1. LGA census counts are based on the 2006 final-results table.
2. LGA counts are proportionally reconciled to the official Abia total because the transcribed LGA sum differs slightly.
3. A common state-level growth rate is applied to every LGA through 2026.
4. Equal LGA growth is a strong assumption; migration and urban growth may make it inaccurate, especially for Aba and Umuahia.
5. Under-five and under-two shares use the NPC/NBS 2016 national population projection as an age-structure proxy and are applied uniformly to LGAs.
6. Expected live births are used as a proxy for expected pregnancies and vaccine/PMC birth cohorts.

## D. Coverage

1. Coverage is interpreted as effective coverage: reached, used and sufficiently adhered to.
2. BAU coverage is assumed because LGA-specific programme coverage data were not supplied.
3. BAU vaccine, PMC and LSM coverage are set to zero pending evidence of implementation in Abia.
4. Scale-up is linear for 12 months and then constant.
5. The same scenario targets are used across LGAs, but only interventions in the LGA's recommended package are activated.
6. Coverage correlations and implementation bottlenecks are not modelled.

## E. Intervention effects

1. Effects are relative reductions in reported clinical case risk among effectively covered, eligible persons.
2. Effects are constant across time and LGAs in the base case.
3. Effects are combined multiplicatively.
4. No synergy, antagonism, resistance evolution, intervention waning or transmission feedback is represented.
5. CM is represented by a conservative relative-reduction proxy for reported clinical case burden, reflecting faster diagnosis/treatment and reduced infectious duration; it is also costed as diagnosis and uncomplicated treatment. This is a simplification, not a directly estimated Abia effect.
6. PMC and vaccination affect the under-five forecast in proportion to the under-two share because infant-specific case data are unavailable.
7. `Dual AI` is operationalized as a pyrethroid–chlorfenapyr net such as Interceptor G2. Change the assumptions if another dual-active-ingredient product is intended.
8. LSM effects are only credible where larval habitats are few, fixed, findable and treatable; the model does not contain a habitat-suitability layer.

## F. Costs

1. Costs are literature-derived priors from several settings and source years.
2. The base analysis does not claim that the inputs are 2026 Abia procurement prices.
3. USD is the primary cost currency; NGN conversion uses an editable planning rate.
4. CM cost includes RDT diagnosis and uncomplicated treatment.
5. Net costs use a procurement proxy plus a Nigeria campaign distribution-cost midpoint.
6. Vaccine cost uses an R21 commodity-price midpoint and an RTS,S delivery-cost proxy.
7. LSM cost is based on urban Tanzania and may not transfer to rural or peri-urban Abia.
8. Costing excludes many context-specific items unless embedded in the source value: freight, wastage, taxes, warehousing, cold-chain expansion, supervision, training, social mobilization and central overhead.
9. The cost-effectiveness ratio is baseline-referenced net cost per case averted, not a full incremental league table with dominance analysis.
10. The willingness-to-pay value is illustrative and should not be used as an official Nigerian threshold.

## G. Appropriate use

Use the outputs for scenario exploration, coverage target discussions, prioritization and identifying the data needed for a formal investment case. Do not present them as calibrated transmission-model forecasts or finalized programme budgets without replacing the local coverage, population, effectiveness and cost inputs.
