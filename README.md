# African Private Credit Market Intelligence

A dashboard and analytical pipeline for evaluating country-sector opportunities in African private credit markets. Built to support investment thesis development for funds deploying SME and mid-cap debt across the continent.

> Status: Modules 1 and 2 complete. Module 3 (FX early warning) planned.
> Live dashboard: https://africa-credit-intelligence.onrender.com

## What this is

Three integrated modules in a single Dash app:

1. **Country-sector opportunity scoring** across 27 African economies, combining macro stability, banking sector depth, market scale, and institutional quality with sector overlays for healthcare, consumer, agribusiness, and education.
2. **News sentiment monitoring** on 5,000+ African financial news articles, scored by Anthropic's Claude with confidence-weighted aggregation into country-week sentiment time series and a 10-topic taxonomy.
3. **Currency risk early warning model** for African FX against USD (planned).

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

## Module 2: how the sentiment scoring works

The sentiment pipeline pulls financial news articles from GDELT 2.0's Global Knowledge Graph via Google BigQuery, filtering for articles where the country appears as a primary location (within the first 100 characters of GDELT's V2Locations field) and where at least one financial GDELT theme is tagged (inflation, monetary, fiscal, banking, currency, and related categories). The 90-day window across 27 countries produced 5,305 articles from 1,514 unique sources.

Each article is scored by Anthropic's Claude Sonnet 4.6 with a structured prompt framed around private credit deployment risk. The model returns sentiment (-1 to +1), confidence (0 to 1), topic (from a 10-category taxonomy spanning monetary, fiscal, banking, currency, political, trade, investment, infrastructure, commodities, and other), and a short key signal phrase. LLM-based scoring was chosen over classical NLP (FinBERT, CamemBERT) because it handles multilingual coverage natively, understands African macro context out of the box, and produces structured topic decomposition in a single call.

Article scores aggregate to country-week sentiment using confidence weighting: `sum(sentiment × confidence) / sum(confidence)`. Articles below 0.30 confidence are dropped because Claude assigns low confidence to off-topic articles (where the country is mentioned but not the subject). Countries are labelled by sentiment quartile within the universe rather than absolute thresholds, since the distribution is structurally negative-skewed.

## Robustness

The ranking was tested under 12 alternative methodological specifications (three coverage thresholds × four pillar weighting schemes). Kendall rank correlation against the baseline ranged 0.78-1.00, with all scenarios preserving at least 8 of the top 10. The top 4 countries (South Africa, Mauritius, Botswana, Cabo Verde) are stable across all specifications. Nigeria's top-10 ranking is contingent on the scale pillar weighting, which reflects a real tension for SME credit deployment in Nigeria rather than a methodological artefact.

## Repository structure

src/module1_scoring/   Country scoring: data fetch, cleaning, sensitivity, sector overlays
src/module2_nlp/       Sentiment: BigQuery fetch, Claude scoring, aggregation
dashboard/             Multi-page Dash app
data/raw/              Local raw data (not committed)
data/processed/        Cleaned features, country scores, sentiment series

## Running locally

```bash
# Clone
git clone https://github.com/kr6243/africa-credit-intelligence.git
cd africa-credit-intelligence

# Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Module 1: country scoring pipeline
python -m src.module1_scoring.fetch
python -m src.module1_scoring.clean
python -m src.module1_scoring.score
python -m src.module1_scoring.sensitivity
python -m src.module1_scoring.sector

# Module 2: sentiment monitoring (requires gcp-key.json and ANTHROPIC_API_KEY in .env)
python -m src.module2_nlp.fetch_gdelt
python -m src.module2_nlp.score
python -m src.module2_nlp.aggregate

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
- Sentiment scoring uses URL slugs and GDELT theme tags rather than full article body, which trades precision per article for scalability and avoidance of paywalls.
- Smaller economies (Cabo Verde, Cote d'Ivoire, DR Congo) have thin article coverage in the 30-day window, producing noisier aggregate sentiment. The dashboard flags these as "low volume".
- The strict country relevance filter (first 100 characters of V2Locations) still admits some off-topic articles. Cabo Verde's negative sentiment is partly driven by syndicated coverage of a hantavirus outbreak on a cruise ship tagged near its waters. Confidence weighting mitigates but does not eliminate this.
- The sentiment scale is negative-skewed because the scoring prompt emphasises credit deployment risk; mean sentiment across the universe is around -0.07. Comparisons across countries are more meaningful than absolute levels.

## Author

Katerina Roumbos
MSc Applied Social Data Science, LSE
BAHons Economics, Finance & Accounting (First Class Honours)

Prior work: SME financing gap analysis across 40 Sub-Saharan African countries (https://github.com/kr6243/sme-africa-analysis)