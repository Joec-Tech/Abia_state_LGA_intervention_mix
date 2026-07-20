from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "Abia"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# -----------------------------------------------------------------------------
# Time axis
# -----------------------------------------------------------------------------
REQUESTED_START = pd.Timestamp("2021-01-01")
REQUESTED_END = pd.Timestamp("2026-04-01")
FORECAST_HORIZON = 24
SEASONAL_PERIOD = 12
VALIDATION_MONTHS = 12

# The supplied files contain 64 monthly observations, exactly matching
# January 2021 through April 2026. Rows are mapped directly and sequentially
# to this complete monthly calendar; no missing month is assumed.

# -----------------------------------------------------------------------------
# LGA metadata and official 2006 census populations
# -----------------------------------------------------------------------------
LGA_INFO = [
    {"LGA":"Aba North","prevalence":11.54,"burden":"Moderate","mix":"CM + IPTp + Dual AI + PMC + Vac","filename":"01_Aba North.txt","population_2006":106844},
    {"LGA":"Aba South","prevalence":11.72,"burden":"Moderate","mix":"CM + IPTp + Dual AI + PMC + Vac + LSM","filename":"02_Aba South.txt","population_2006":427421},
    {"LGA":"Arochukwu","prevalence":13.02,"burden":"Moderate","mix":"CM + IPTp + Dual AI + PMC + Vac","filename":"03_Arochukwu.txt","population_2006":169339},
    {"LGA":"Bende","prevalence":8.10,"burden":"Low","mix":"CM + IPTp + Dual AI + PMC","filename":"04_Bende.txt","population_2006":192621},
    {"LGA":"Ikwuano","prevalence":7.99,"burden":"Low","mix":"CM + IPTp + Dual AI + PMC","filename":"05_Ikwuano.txt","population_2006":137897},
    {"LGA":"Isiala Ngwa North","prevalence":11.47,"burden":"Moderate","mix":"CM + IPTp + Dual AI + PMC + Vac","filename":"06_Isiala-Ngwa North.txt","population_2006":154083},
    {"LGA":"Isiala Ngwa South","prevalence":8.29,"burden":"Low","mix":"CM + IPTp + Dual AI + PMC","filename":"07_Isiala-Ngwa South.txt","population_2006":136650},
    {"LGA":"Isuikwato","prevalence":6.07,"burden":"Low","mix":"CM + IPTp + Dual AI + PMC + LSM","filename":"08_Isuikwuato.txt","population_2006":115794},
    {"LGA":"Obi Nwa","prevalence":12.87,"burden":"Moderate","mix":"CM + IPTp + Dual AI + PMC + Vac","filename":"09_Obi Nwga.txt","population_2006":181894},
    {"LGA":"Ohafia","prevalence":8.98,"burden":"Low","mix":"CM + IPTp + Dual AI + PMC","filename":"10_Ohafia.txt","population_2006":245987},
    {"LGA":"Osisioma Ngwa","prevalence":10.48,"burden":"Moderate","mix":"CM + IPTp + Pyr + PMC + Vac","filename":"11_Osisioma Ngwa.txt","population_2006":220662},
    {"LGA":"Ugwunagbo","prevalence":17.63,"burden":"Moderate","mix":"CM + IPTp + Dual AI + PMC + Vac","filename":"12_Ugwunagbo.txt","population_2006":85371},
    {"LGA":"Ukwa East","prevalence":21.11,"burden":"Moderate","mix":"CM + IPTp + Dual AI + PMC + Vac","filename":"13_Ukwa East.txt","population_2006":58139},
    {"LGA":"Ukwa West","prevalence":17.23,"burden":"Moderate","mix":"CM + IPTp + Dual AI + PMC + Vac","filename":"14_Ukwa West.txt","population_2006":87367},
    {"LGA":"Umuahia North","prevalence":3.66,"burden":"Low","mix":"CM + IPTp + Dual AI + PMC","filename":"15_Umuahia North.txt","population_2006":223134},
    {"LGA":"Umuahia South","prevalence":4.06,"burden":"Low","mix":"CM + IPTp + Dual AI + PMC","filename":"16_Umuahia South.txt","population_2006":139058},
    {"LGA":"Umu Neochi","prevalence":7.83,"burden":"Low","mix":"CM + IPTp + Dual AI + PMC","filename":"17_Umunneochi.txt","population_2006":163119},
]

ABIA_POP_2006 = 2_845_380
ABIA_POP_2016 = 3_727_347
POPULATION_GROWTH_RATE = (ABIA_POP_2016 / ABIA_POP_2006) ** (1 / 10) - 1
POPULATION_PROJECTION_YEAR = 2026

# National demographic proxies used only when LGA-specific age structure is absent.
UNDER5_SHARE = 31_116_156 / 193_392_517  # NBS/NPC 2016 national projection
UNDER2_SHARE = UNDER5_SHARE * (2 / 5)
CRUDE_BIRTH_RATE = 0.033  # births per person-year; editable proxy
LSM_TARGETABLE_POPULATION_SHARE = 0.30

# -----------------------------------------------------------------------------
# Intervention target groups
# -----------------------------------------------------------------------------
GROUP_COLUMNS = {
    "PW": "PW",
    "U5": "Under_5yrs",
    "A5": "Above_5yrs",
}
TARGET_GROUPS = {
    "CM": ["PW", "U5", "A5"],
    "IPTp": ["PW"],
    "Dual AI": ["PW", "U5", "A5"],
    "Pyr": ["PW", "U5", "A5"],
    "PMC": ["U5"],
    "Vac": ["U5"],
    "LSM": ["PW", "U5", "A5"],
}

# Relative reduction in clinical case risk among effectively covered people.
# Base values are literature-informed planning parameters, not estimates fitted
# to the Abia surveillance data. Low/high values support scenario uncertainty.
EFFECTIVENESS = {
    "CM":      {"low":0.05, "base":0.10, "high":0.20, "note":"Incidence proxy for more effective testing and treatment.", "source":"Camponovo et al. 2024 modelling study", "url":"https://pmc.ncbi.nlm.nih.gov/articles/PMC11549775/"},
    "IPTp":    {"low":0.15, "base":0.25, "high":0.35, "note":"Planning proxy; effectiveness is SP-resistance and outcome dependent.", "source":"Kayentao et al. systematic review and later IPTp evidence", "url":"https://pmc.ncbi.nlm.nih.gov/articles/PMC4669677/"},
    "Dual AI": {"low":0.20, "base":0.30, "high":0.40, "note":"Proxy informed by next-generation/PBO net trials.", "source":"Mosha et al. dual-AI LLIN trial; Nigeria PBO-net economic evaluation used only as a cost-premium proxy", "url":"https://pmc.ncbi.nlm.nih.gov/articles/PMC8971961/"},
    "Pyr":     {"low":0.10, "base":0.20, "high":0.30, "note":"Conservative pyrethroid-net planning effect.", "source":"Spectrum-Malaria evidence synthesis / ITN trials", "url":"https://pmc.ncbi.nlm.nih.gov/articles/PMC5301449/"},
    "PMC":     {"low":0.22, "base":0.30, "high":0.35, "note":"Pooled trial evidence for reduction in clinical malaria.", "source":"PMC evidence synthesis reporting about 30% case reduction", "url":"https://pmc.ncbi.nlm.nih.gov/articles/PMC10875741/"},
    "Vac":     {"low":0.36, "base":0.50, "high":0.66, "note":"R21 four-dose programme; time-averaged planning effect.", "source":"WHO R21 recommendation and efficacy summary", "url":"https://www.who.int/news/item/02-10-2023-who-recommends-r21-matrix-m-vaccine-for-malaria-prevention-in-updated-advice-on-immunization"},
    "LSM":     {"low":0.20, "base":0.40, "high":0.60, "note":"Highly setting-dependent; requires findable and treatable habitats.", "source":"Cochrane LSM review; contextual planning range", "url":"https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.CD008923.pub3/"},
}

# Coverage is effective coverage: reached, used/adherent, and protected.
SCENARIO_COVERAGE = {
    "BAU":       {"CM":0.55,"IPTp":0.45,"Dual AI":0.40,"Pyr":0.40,"PMC":0.35,"Vac":0.25,"LSM":0.10},
    "Scenario 1":{"CM":0.65,"IPTp":0.55,"Dual AI":0.50,"Pyr":0.50,"PMC":0.45,"Vac":0.35,"LSM":0.25},
    "Scenario 2":{"CM":0.75,"IPTp":0.65,"Dual AI":0.60,"Pyr":0.60,"PMC":0.60,"Vac":0.50,"LSM":0.40},
    "Target":    {"CM":0.85,"IPTp":0.75,"Dual AI":0.75,"Pyr":0.75,"PMC":0.75,"Vac":0.65,"LSM":0.55},
    "High":      {"CM":0.90,"IPTp":0.85,"Dual AI":0.85,"Pyr":0.85,"PMC":0.85,"Vac":0.75,"LSM":0.70},
    "Maximum":   {"CM":0.95,"IPTp":0.90,"Dual AI":0.90,"Pyr":0.90,"PMC":0.90,"Vac":0.85,"LSM":0.80},
}
SCALE_UP_MONTHS = 12

# -----------------------------------------------------------------------------
# Cost library
# -----------------------------------------------------------------------------
USD_TO_NGN = 1_500.0  # editable planning exchange rate, not a claimed market rate
COST_BASE_YEAR = 2024
CPI_US = {2011:224.939, 2014:236.736, 2017:245.120, 2020:258.811, 2021:270.970, 2022:292.655, 2024:313.689}

def inflate_usd(value, source_year, target_year=2024):
    return value * CPI_US[target_year] / CPI_US[source_year]

# Base costs are converted to 2024 USD where the source price year is available.
# Units differ by intervention and are explicitly handled by costing.py.
COST_LIBRARY = {
    "CM": {
        "base_usd_2024": inflate_usd(4.32 + 5.84, 2011),
        "low_usd_2024": inflate_usd(0.34 + 2.36, 2011),
        "high_usd_2024": inflate_usd(9.34 + 23.65, 2011),
        "unit": "additional malaria case diagnosed and treated",
        "source": "White et al. 2011 systematic review",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3229472/",
    },
    "IPTp": {
        "base_usd_2024": inflate_usd(2.06, 2011),
        "low_usd_2024": inflate_usd(0.47, 2011),
        "high_usd_2024": inflate_usd(3.36, 2011),
        "unit": "pregnant woman protected per year",
        "source": "White et al. 2011 systematic review",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3229472/",
    },
    "PMC": {
        "base_usd_2024": inflate_usd(0.60, 2011),
        "low_usd_2024": inflate_usd(0.48, 2011),
        "high_usd_2024": inflate_usd(1.08, 2011),
        "unit": "eligible child protected per year",
        "source": "White et al. 2011 systematic review (IPTi/PMC proxy)",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3229472/",
    },
    "Pyr": {
        "base_usd_2024": inflate_usd(2.20, 2011),
        "low_usd_2024": 1.18,
        "high_usd_2024": 5.70,
        "unit": "person protected per year",
        "source": "White et al. 2011; Conteh et al. 2021 reviews",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8324482/",
    },
    "Dual AI": {
        "base_usd_2024": inflate_usd(2.20, 2011) + inflate_usd(0.90, 2020)/(1.8*3),
        "low_usd_2024": 1.50,
        "high_usd_2024": 6.50,
        "unit": "person protected per year",
        "source": "Mosha et al. dual-AI LLIN economic evaluation; Nigeria PBO-net incremental-cost proxy for the unit-cost premium",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8971961/",
    },
    "Vac": {
        "base_usd_2024": 4 * (3.90 + 2.65),
        "low_usd_2024": 4 * (3.90 + 2.30),
        "high_usd_2024": 4 * (3.90 + 3.01),
        "unit": "fully vaccinated child, four-dose R21 course",
        "source": "R21 price proxy plus Baral et al. delivery-cost range",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9946791/",
    },
    "LSM": {
        "base_usd_2024": inflate_usd(1.50, 2011),
        "low_usd_2024": inflate_usd(0.79, 2011),
        "high_usd_2024": inflate_usd(25.06, 2017),
        "unit": "target-area resident protected per year",
        "source": "Worrall & Fillinger 2011; Phiri et al. 2021 high-cost sensitivity",
        "url": "https://link.springer.com/article/10.1186/1475-2875-10-338",
    },
}

# Averted-treatment cost is anchored to diagnosis + uncomplicated treatment.
TREATMENT_COST_SAVED_USD_2024 = COST_LIBRARY["CM"]["base_usd_2024"]

# Optional net monetary benefit threshold; kept editable and not used as a
# universal claim about Nigeria's willingness to pay.
WTP_PER_CASE_AVERTED_NGN = 150_000.0

SARIMA_CANDIDATES = [
    ((0,1,1),(0,1,1,12)),
    ((1,1,0),(0,1,1,12)),
    ((1,1,1),(0,1,1,12)),
    ((0,1,1),(1,0,0,12)),
    ((1,0,1),(1,0,0,12)),
    ((1,0,0),(1,0,0,12)),
]
MAX_FORECAST_MULTIPLIER = 20.0
