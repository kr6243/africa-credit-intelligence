"""
Methodology page. Mostly static text explaining what the score means.
"""

from dash import html
from dashboard.components.styling import (
    PAGE_STYLE, H1_STYLE, H2_STYLE, SUBTITLE_STYLE, COLORS,
)


_paragraph = {'fontSize': '14px', 'lineHeight': '1.6', 'marginBottom': '12px'}
_table_style = {'fontSize': '13px', 'marginTop': '8px', 'marginBottom': '24px'}


layout = html.Div(
    style=PAGE_STYLE,
    children=[
        html.H1('Methodology', style=H1_STYLE),
        html.Div(
            'How the country-sector opportunity score and news sentiment '
            'monitoring are constructed.',
            style=SUBTITLE_STYLE,
        ),

        html.H2('Scope', style=H2_STYLE),
        html.P(
            'The country score covers 27 African economies across West, East, '
            'Southern, Central, and North Africa. The universe was selected to '
            'span TLG\'s current footprint plus adjacent markets where '
            'TLG-style private credit deployment is plausible.',
            style=_paragraph,
        ),

        html.H2('Pillars', style=H2_STYLE),
        html.P(
            'The country score is the equal-weighted mean of four pillars, each '
            'capturing a distinct dimension of investability:',
            style=_paragraph,
        ),
        html.Ul(
            style={'fontSize': '14px', 'lineHeight': '1.7'},
            children=[
                html.Li([html.B('Macro stability: '),
                         'GDP growth, inflation level and volatility, current account, '
                         'fiscal balance, reserves.']),
                html.Li([html.B('Banking sector: '),
                         'Private credit / GDP, NPL ratio, bank capital adequacy, '
                         'interest rate spread.']),
                html.Li([html.B('Market scale: '),
                         'GDP, GDP per capita PPP, population. Captures the size of '
                         'the addressable market.']),
                html.Li([html.B('Institutional quality: '),
                         'Mo Ibrahim Foundation IIAG composite scores for Security & '
                         'Rule of Law and Participation, Rights & Inclusion.']),
            ],
        ),

        html.H2('Aggregation rules', style=H2_STYLE),
        html.P(
            'Within each pillar, features are z-scored across the 27 countries and '
            'signed so a positive z-score always means "good for credit deployment". '
            'The pillar score is the mean of available features, but only if at least '
            '50% of the pillar\'s features are present; otherwise the pillar is null. '
            'The country score is the mean of pillar scores, computed only if at '
            'least 3 of 4 pillars are non-null. Countries failing this threshold are '
            'flagged "insufficient data" and excluded from the headline ranking.',
            style=_paragraph,
        ),

        html.P([
            html.B('Reading the numbers: '),
            'Percentiles describe a country\'s rank within the 27-country universe '
            '(50th = median, 100th = top). Composite scores are the underlying '
            'z-score values where 0 is the African average and ±1 means one '
            'standard deviation from it. The dashboard leads with percentiles for '
            'readability; z-scores are retained as a secondary column for analytical '
            'work and the sector heatmap, where relative magnitude carries meaning.',
        ], style=_paragraph),

        html.H2('Sensitivity', style=H2_STYLE),
        html.P(
            'The ranking was tested under 12 alternative methodological specifications '
            '(three coverage thresholds × four weighting schemes). Kendall rank '
            'correlation against the baseline ranged 0.78-1.00, with all scenarios '
            'preserving at least 8 of the top 10. The top 4 (South Africa, Mauritius, '
            'Botswana, Cabo Verde) are stable across all specifications. Nigeria\'s '
            'top-10 ranking is sensitive to the scale weighting, reflecting a real '
            'tension for SME credit deployment rather than a methodological artefact.',
            style=_paragraph,
        ),

        html.H2('Data sources and limitations', style=H2_STYLE),
        html.P(
            'Macro and banking data come from the World Bank WDI database via the '
            'wbgapi Python client, using 5-year averages (2019-2023). Institutional '
            'quality comes from the Mo Ibrahim Foundation IIAG 2024 release. The '
            'WGI Worldwide Governance Indicators were originally planned for Pillar 4 '
            'but the World Bank\'s source 3 API endpoint returned malformed JSON '
            'during the build; the IIAG is a stronger choice for an Africa-focused '
            'analysis regardless. Enterprise Survey indicators were considered for '
            'an SME financing pillar but coverage was too thin (most countries\' '
            'most recent surveys predated 2018); the pillar was reconceived as '
            'Market Scale, which is more relevant to a private credit fund\'s '
            'deployment question.',
            style=_paragraph,
        ),
        html.P(
            'Banking sector indicators are nulled for 4 of 27 countries (Benin, '
            'Mali, Togo, Tunisia) due to insufficient World Bank coverage. An '
            'extension using IMF Financial Soundness Indicators would close this '
            'gap, particularly for WAEMU and North African countries where '
            'national central bank reporting exists but is not consistently '
            'ingested into WDI.',
            style=_paragraph,
        ),

        html.H2('Sector overlays', style=H2_STYLE),
        html.P(
            'Sector scores are produced separately from the country score, so a '
            'TLG-style analyst can see both the country-level investability and '
            'the sector-specific opportunity within that country. Each sector is '
            'scored on 2-4 indicators (healthcare on health spending and beds, '
            'consumer on income and urbanisation, agribusiness on sector relevance, '
            'land, commercialisation and yields, education on spending, enrolment '
            'and literacy). Agribusiness scoring departed from a pure productivity '
            'metric because that would inappropriately reward small economies with '
            'high-tech but irrelevant agricultural sectors. Financial services '
            'overlay is covered by the banking pillar of the country score.',
            style=_paragraph,
        ),
        html.H2('News sentiment monitoring (Module 2)', style=H2_STYLE),
        html.P(
            'Sentiment monitoring scores news articles about each country and '
            'aggregates them into a country-week sentiment time series. The use '
            'case is current-state monitoring: "what is the narrative on country '
            'X right now, and is it shifting?" This complements the country score '
            '(which is a structural assessment) with a tactical, time-varying '
            'signal.',
            style=_paragraph,
        ),

        html.H2('News data source', style=H2_STYLE),
        html.P(
            'Articles are pulled from GDELT 2.0\'s Global Knowledge Graph (GKG) '
            'via Google BigQuery. The GDELT Doc API was initially considered but '
            'has a rolling 90-day window and aggressive rate limiting; BigQuery '
            'gives us access to the full GKG archive with no rate limits. The '
            'query filters for articles where the country appears within the '
            'first 100 characters of GDELT\'s V2Locations field (a strict '
            'positional filter that excludes articles where the country is merely '
            'mentioned in passing) and for articles tagged with at least one '
            'financial GDELT theme (ECON_INFLATION, ECON_MONETARY, BANKING, '
            'FISCAL, ECON_WORLDCURRENCIES, and others). Country names follow '
            'GDELT\'s FIPS 10-4 convention rather than ISO 3166; DR Congo in '
            'particular required a FIPS-code match to disambiguate from Republic '
            'of the Congo and Chad.',
            style=_paragraph,
        ),

        html.H2('Sentiment scoring', style=H2_STYLE),
        html.P(
            'Each article is scored by Anthropic\'s Claude Sonnet 4.6 model. The '
            'prompt frames the model as "a financial analyst at a private credit '
            'fund evaluating African markets" and asks for a JSON object with '
            'four fields: sentiment (-1 to +1), confidence (0 to 1), topic '
            '(from a 10-category taxonomy: monetary, fiscal, banking, currency, '
            'political, trade, investment, infrastructure, commodities, other), '
            'and a short key signal phrase. Claude scores from the article URL '
            'slug and GDELT theme tags rather than full article body, which '
            'accepts lower precision per article in exchange for scalability and '
            'avoidance of paywall and bot-detection issues. Results are cached '
            'by URL so reruns do not re-score the same article.',
            style=_paragraph,
        ),

        html.P(
            'A choice worth flagging: classical NLP approaches (FinBERT for '
            'English, CamemBERT for French) were considered and rejected. '
            'FinBERT is trained on US financial news and systematically '
            'misclassifies African contexts; multilingual coverage would require '
            'fine-tuning separate models per language; classification-only '
            'output does not support topic decomposition. The LLM approach '
            'handles multilingual coverage natively, understands African macro '
            'context (the importance of distinguishing the two Congos, what '
            'WAEMU means, what a eurobond restructuring implies), and produces '
            'structured topic and quote fields in a single call.',
            style=_paragraph,
        ),

        html.H2('Aggregation', style=H2_STYLE),
        html.P(
            'Article-level scores are rolled up to country-week and country-30-day '
            'summaries. Aggregation is confidence-weighted: the mean sentiment per '
            'group is computed as sum(sentiment × confidence) / sum(confidence), '
            'so high-conviction scores carry more weight than uncertain ones. '
            'Articles with confidence below 0.30 are excluded from aggregation '
            'because Claude tends to assign low confidence to off-topic articles '
            '(where the country is mentioned but not the subject). Countries are '
            'labelled by sentiment quartile within the universe rather than '
            'absolute thresholds, because the distribution is structurally '
            'negative-skewed: African macro news in this period is more often '
            'discussing risks than opportunities.',
            style=_paragraph,
        ),

        html.H2('Sentiment limitations', style=H2_STYLE),
        html.P(
            'Smaller-economy coverage is thin. Cabo Verde, Cote d\'Ivoire, and '
            'DR Congo have fewer than 50 articles in the 30-day window in this '
            'sample, which gives noisy aggregate scores. The dashboard flags '
            'these as "low volume" and treats their headline numbers with '
            'caution. Off-topic articles also contaminate small-volume countries '
            'disproportionately: Cabo Verde\'s sentiment in this period is '
            'pulled down by syndicated coverage of a hantavirus outbreak on a '
            'cruise ship in the Atlantic, where the ship was tagged near Cabo '
            'Verde but the article had nothing to do with the country\'s '
            'economy. Confidence weighting mitigates but does not eliminate '
            'this. An extension would tighten the relevance filter further or '
            'add a second-stage classifier that distinguishes "country is the '
            'subject" from "country is mentioned".',
            style=_paragraph,
        ),

        html.P(
            'The sentiment scale is also asymmetric. Claude\'s prompt is framed '
            'around credit deployment risk, so risk language is scored more '
            'sharply than opportunity language. Mean sentiment across the '
            'universe is around -0.07; very few countries cross into clearly '
            'positive territory. Comparison across countries (Country A is in '
            'the top quartile of the universe) is more meaningful than absolute '
            'levels (Country A\'s sentiment is +0.05).',
            style=_paragraph,
        ),
    ],
)