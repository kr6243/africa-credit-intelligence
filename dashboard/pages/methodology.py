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
            'How the country-sector opportunity score is constructed.',
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
    ],
)