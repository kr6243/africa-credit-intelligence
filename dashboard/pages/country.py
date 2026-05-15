"""
Country detail page. Pick a country from the dropdown, see its pillar
breakdown, feature-level table, and sector scores.
"""

from dash import html, dcc, dash_table, Input, Output
import plotly.graph_objects as go

from dashboard.data_loader import (
    COUNTRY_SCORES, FEATURES, SECTOR_SCORES, COUNTRY_NAMES, TLG_FOOTPRINT,
)
from dashboard.components.styling import (
    PAGE_STYLE, H1_STYLE, H2_STYLE, SUBTITLE_STYLE, COLORS, PLOTLY_LAYOUT,
)


# Display labels for the features. Maps raw column names to friendlier ones.
FEATURE_LABELS = {
    'gdp_growth': 'GDP growth (5yr avg, %)',
    'inflation': 'Inflation (5yr avg, %)',
    'inflation_vol': 'Inflation volatility (5yr std, %)',
    'current_account_gdp': 'Current account (% GDP)',
    'fiscal_balance_gdp': 'Fiscal balance (% GDP)',
    'reserves_months': 'Reserves (months of imports)',
    'private_credit_gdp': 'Private credit / GDP (%)',
    'npl_ratio': 'NPL ratio (%)',
    'bank_capital_assets': 'Bank capital / assets (%)',
    'interest_spread': 'Interest spread (lending - deposit, %)',
    'gdp_per_capita_ppp': 'GDP per capita PPP (USD)',
    'gdp_usd': 'GDP (USD)',
    'population': 'Population',
    'iiag_security_rol': 'IIAG: Security & Rule of Law (0-100)',
    'iiag_participation_rights': 'IIAG: Participation, Rights & Inclusion (0-100)',
}


# Default selection on first load
_DEFAULT_COUNTRY = 'ZAF'


_dropdown_options = [
    {'label': COUNTRY_NAMES.get(c, c), 'value': c}
    for c in sorted(COUNTRY_SCORES['country'].unique(), key=lambda c: COUNTRY_NAMES.get(c, c))
]


layout = html.Div(
    style=PAGE_STYLE,
    children=[
        html.H1('Country detail', style=H1_STYLE),
        html.Div(
            'Pillar breakdown, feature-level values, and sector overlays for '
            'a single country. Use the dropdown to switch.',
            style=SUBTITLE_STYLE,
        ),

        dcc.Dropdown(
            id='country-dropdown',
            options=_dropdown_options,
            value=_DEFAULT_COUNTRY,
            clearable=False,
            style={'maxWidth': '320px', 'marginBottom': '24px'},
        ),

        html.Div(id='country-header'),
        html.H2('Pillar scores vs African average', style=H2_STYLE),
        dcc.Graph(id='country-radar', config={'displayModeBar': False}),

        html.H2('Feature breakdown', style=H2_STYLE),
        html.Div(id='country-feature-table'),

        html.H2('Sector overlays', style=H2_STYLE),
        dcc.Graph(id='country-sectors', config={'displayModeBar': False}),
    ],
)


def _build_header(country_iso):
    row = COUNTRY_SCORES[COUNTRY_SCORES['country'] == country_iso].iloc[0]
    name = COUNTRY_NAMES.get(country_iso, country_iso)
    is_tlg = country_iso in TLG_FOOTPRINT
    score = row['country_score']
    rank = row['rank']
    percentile = row['percentile']
    coverage = row['data_coverage']

    if pd.notna(rank) and pd.notna(percentile):
        headline = f'{int(percentile)}th percentile'
        sub = f'Rank {int(rank)} of 27  ·  Composite score {score:+.2f}'
    else:
        headline = 'Insufficient data'
        sub = 'Excluded from ranking'

    tlg_label = '  ●  TLG footprint' if is_tlg else ''

    return html.Div(
        style={
            'display': 'flex', 'flexDirection': 'column',
            'padding': '16px 20px', 'border': f'1px solid {COLORS["border"]}',
            'borderRadius': '6px', 'backgroundColor': COLORS['panel'],
            'marginBottom': '8px',
        },
        children=[
            html.Div(
                style={'display': 'flex', 'alignItems': 'baseline', 'gap': '20px'},
                children=[
                    html.Div(name, style={'fontSize': '22px', 'fontWeight': '600'}),
                    html.Div(headline,
                             style={'fontSize': '16px', 'color': COLORS['navy'],
                                    'fontWeight': '600'}),
                    html.Div(tlg_label,
                             style={'fontSize': '13px', 'color': COLORS['tlg'],
                                    'fontWeight': '600'}),
                ],
            ),
            html.Div(
                f'{sub}  ·  Data coverage {coverage:.0%}',
                style={'fontSize': '13px', 'color': COLORS['text_muted'],
                       'marginTop': '4px'},
            ),
        ],
    )


def _build_radar(country_iso):
    row = COUNTRY_SCORES[COUNTRY_SCORES['country'] == country_iso].iloc[0]
    pillars = ['Macro', 'Banking', 'Scale', 'Institutions']
    values = [
        row['pillar_macro'], row['pillar_banking'],
        row['pillar_scale'], row['pillar_institutions'],
    ]
    # Replace NaN with 0 for plotting and note it in hover text
    plot_values = [0 if pd.isna(v) else v for v in values]
    hover = [
        f'{p}: {"insufficient data" if pd.isna(v) else f"{v:+.2f}"}'
        for p, v in zip(pillars, values)
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=plot_values + [plot_values[0]],
        theta=pillars + [pillars[0]],
        fill='toself',
        line={'color': COLORS['navy'], 'width': 2},
        fillcolor='rgba(30, 58, 95, 0.15)',
        hovertext=hover + [hover[0]],
        hoverinfo='text',
        name=COUNTRY_NAMES.get(country_iso, country_iso),
    ))
    fig.update_layout(
        font={'family': PLOTLY_LAYOUT['font']['family'], 'size': 12, 'color': COLORS['text']},
        paper_bgcolor=COLORS['bg'],
        height=400,
        showlegend=False,
        margin={'l': 60, 'r': 60, 't': 30, 'b': 30},
        polar={
            'bgcolor': COLORS['bg'],
            'radialaxis': {
                'visible': True, 'range': [-2.5, 2.5],
                'gridcolor': COLORS['border'], 'tickfont': {'size': 10},
            },
            'angularaxis': {
                'gridcolor': COLORS['border'], 'tickfont': {'size': 12},
            },
        },
    )
    return fig


def _build_feature_table(country_iso):
    """Build a table comparing this country's features to the African median."""
    feat = FEATURES.set_index('country')
    if country_iso not in feat.index:
        return html.Div('No data for this country.')

    country_row = feat.loc[country_iso]
    medians = feat.median(numeric_only=True)

    rows = []
    for col, label in FEATURE_LABELS.items():
        if col not in feat.columns:
            continue
        v = country_row[col]
        m = medians[col]
        rows.append({
            'Feature': label,
            'Value': 'n/a' if pd.isna(v) else _fmt_value(col, v),
            'African median': _fmt_value(col, m),
            'Position': _position_label(v, m, col),
        })

    return dash_table.DataTable(
        data=rows,
        columns=[
            {'name': c, 'id': c, 'type': 'text'}
            for c in ['Feature', 'Value', 'African median', 'Position']
        ],
        page_action='none',
        style_cell={
            'fontFamily': 'system-ui, -apple-system, sans-serif',
            'fontSize': '13px', 'padding': '8px 12px', 'textAlign': 'left',
            'border': f'1px solid {COLORS["border"]}',
        },
        style_header={
            'backgroundColor': COLORS['panel'], 'fontWeight': '600',
            'borderBottom': f'2px solid {COLORS["border"]}',
        },
        style_cell_conditional=[
            {'if': {'column_id': c}, 'textAlign': 'right'}
            for c in ['Value', 'African median']
        ],
        style_data_conditional=[
            {'if': {'filter_query': '{Position} = "favourable"', 'column_id': 'Position'},
             'color': COLORS['positive'], 'fontWeight': '600'},
            {'if': {'filter_query': '{Position} = "unfavourable"', 'column_id': 'Position'},
             'color': COLORS['negative'], 'fontWeight': '600'},
        ],
    )


def _fmt_value(col, value):
    """Format a feature value sensibly based on its column."""
    if pd.isna(value):
        return 'n/a'
    if col in ('gdp_usd', 'population'):
        return f'{value:,.0f}'
    if col == 'gdp_per_capita_ppp':
        return f'{value:,.0f}'
    return f'{value:.2f}'


def _position_label(value, median, col):
    """Return 'favourable' or 'unfavourable' relative to the median for SME credit.
    Direction-aware: e.g. low inflation is favourable, low private credit is not."""
    if pd.isna(value) or pd.isna(median):
        return ''
    lower_better = {'inflation', 'inflation_vol', 'npl_ratio', 'interest_spread'}
    if col in lower_better:
        return 'favourable' if value < median else 'unfavourable'
    return 'favourable' if value > median else 'unfavourable'


def _build_sector_chart(country_iso):
    sub = SECTOR_SCORES[SECTOR_SCORES['country'] == country_iso].copy()
    if sub.empty:
        return go.Figure().update_layout(annotations=[
            {'text': 'No sector data for this country.', 'showarrow': False}
        ])

    sub = sub.sort_values('sector')
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sub['sector'].str.title(),
        y=sub['sector_score'],
        marker={'color': [COLORS['positive'] if s > 0 else COLORS['negative']
                          for s in sub['sector_score'].fillna(0)]},
        hovertemplate='<b>%{x}</b><br>Score: %{y:.2f}<extra></extra>',
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=320,
        showlegend=False,
        yaxis_title='Sector score (z-score units)',
        xaxis_title='',
    )
    fig.add_hline(y=0, line_width=1, line_color=COLORS['text_muted'], line_dash='dot')
    return fig


def register_callbacks(app):
    @app.callback(
        Output('country-header', 'children'),
        Output('country-radar', 'figure'),
        Output('country-feature-table', 'children'),
        Output('country-sectors', 'figure'),
        Input('country-dropdown', 'value'),
    )
    def update_country(country_iso):
        return (
            _build_header(country_iso),
            _build_radar(country_iso),
            _build_feature_table(country_iso),
            _build_sector_chart(country_iso),
        )


# pandas import down here because we use pd.isna and pd.notna throughout
import pandas as pd  # noqa: E402