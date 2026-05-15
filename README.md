# African Private Credit Market Intelligence

A dashboard and analytical pipeline for evaluating country-sector opportunities in African private credit markets. Built to support investment thesis development for funds deploying SME and mid-cap debt across the continent.

> Status: Module 1 complete. Modules 2 (NLP sentiment) and 3 (FX early warning) in development.

## What this is

Three integrated modules in a single Dash app:

1. **Country-sector opportunity scoring** across 27 African economies, combining macro stability, banking sector depth, market scale, and institutional quality with sector overlays for healthcare, consumer, agribusiness, and education.
2. **NLP sentiment monitoring** on African financial news, central bank statements, and IMF country reports (in development).
3. **Currency risk early warning model** for African FX against USD (in development).

## Why this matters for African private credit

Funds deploying debt into African SMEs and mid-cap companies make country-allocation and sector-allocation decisions on a continent where data is fragmented across multilateral databases, central banks, and industry sources. This project consolidates that data into a defensible, transparent framework that distinguishes "deployable today" markets from "adjacent opportunity" and "monitor only" markets, and surfaces sector-specific signals within them.

## Module 1: how the scoring works

The country score is the equal-weighted mean of four pillars, each capturing a distinct dimension of investability:

| Pillar | Features | Source |
|---|---|---|
| **Macro stability** | GDP growth, inflation level and volatility, current account, fiscal balance, reserves | World Bank WDI |
| **Banking sector** | Private credit / GDP, NPL ratio, bank capital adequacy, interest rate spread | World Bank WDI |
| **Market scale** | GDP, GDP per capita PPP, population | World Bank WDI |
| **Institutional quality** | IIAG Security & Rule of Law, Participation Rights & Inclusion | Mo Ibrahim Foundation IIAG 2024 |

Within each pillar, features are z-scored across the 27 countries and signed so positive always means "good for credit deployment". Pillar scores require at least 50% of features present; country scores require at least 3 of 4 pillars non-null. Countries failing the threshold are flagged "insufficient data" and excluded from the headline ranking.

Sector overlays are produced separately from the country score so a user can see both country-level investability and sector-specific opportunity within a country. Agribusiness scoring was deliberately departed from a pure productivity composite (which inappropriately rewarded small economies with high-tech but irrelevant agriculture) to a four-indicator composite covering sector relevance, market size, commercialisation, and productivity.

## Robustness

The ranking was tested under 12 alternative methodological specifications (three coverage thresholds × four pillar weighting schemes). Kendall rank correlation against the baseline ranged 0.78-1.00, with all scenarios preserving at least 8 of the top 10. The top 4 countries (South Africa, Mauritius, Botswana, Cabo Verde) are stable across all specifications. Nigeria's top-10 ranking is contingent on the scale pillar weighting, which reflects a real tension for SME credit deployment in Nigeria rather than a methodological artefact.

## Repository structure
src/module1_scoring/   Data fetch, cleaning, scoring, sensitivity analysis
dashboard/             Multi-page Dash app
data/raw/              Local raw data (not committed)
data/processed/        Cleaned features and scored outputs
docs/                  Methodology write-up

## Running locally

```bash
# Clone
git clone https://github.com/kr6243/africa-credit-intelligence.git
cd africa-credit-intelligence

# Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build the data and scoring pipeline
python -m src.module1_scoring.fetch
python -m src.module1_scoring.clean
python -m src.module1_scoring.score
python -m src.module1_scoring.sensitivity
python -m src.module1_scoring.sector

# Launch the dashboard
python -m dashboard.app
```

Open http://127.0.0.1:8050 in your browser.

The IIAG 2024 dataset is not committed to this repo. Download it from https://iiag.online/downloads.html and place the unzipped folder at `data/raw/2024-IIAG-csv-files/`.

## Limitations

- Banking sector indicators are nulled for 4 of 27 countries (Benin, Mali, Togo, Tunisia) due to insufficient World Bank coverage. An extension using IMF Financial Soundness Indicators would close this gap.
- The original Pillar 4 design used the Worldwide Governance Indicators, but the World Bank API endpoint serving that database returned malformed JSON during the build. The Mo Ibrahim IIAG is a stronger choice for an Africa-focused analysis regardless.
- An SME-specific pillar was considered using Enterprise Survey indicators but coverage was too thin; the pillar was reconceived as Market Scale, which more directly answers the deployment question.
- Sector overlays are coarse, especially for agribusiness where commercial-vs-subsistence breakdown isn't directly observable in the available indicators.

## Author

Katerina Roumbos
MSc Applied Social Data Science, LSE
BAHons Economics, Finance & Accounting (First Class Honours)

Prior work: SME financing gap analysis across 40 Sub-Saharan African countries (https://github.com/kr6243/sme-africa-analysis)