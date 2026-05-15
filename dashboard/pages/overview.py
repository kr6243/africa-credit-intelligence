"""
Overview page: ranked country opportunity scores with pillar breakdowns.
"""

from dash import html, dcc, dash_table
import plotly.graph_objects as go
import pandas as pd

from dashboard.data_loader import COUNTRY_SCORES, COUNTRY_NAMES, TLG_FOOTPRINT
from dashboard.components.styling import (
    PAGE_STYLE, H1_STYLE, H2_STYLE, SUBTITLE_STYLE, COLORS, PLOTLY_LAYOUT,
)


def _tier(percentile):
    """Convert a percentile to a tier label."""
    if pd.isna(percentile):
        return ''
    if percentile >= 75:
        return 'Top'
    if percentile >= 50:
        return 'Strong'
    if percentile >= 25:
        return 'Mid'
    return 'Weak'


def _build_table_df():
    df = COUNTRY_SCORES.copy()
    df['Country'] = df['country'].map(COUNTRY_NAMES).fillna(df['country'])
    df['TLG'] = df['country'].apply(lambda c: '●' if c in TLG_FOOTPRINT else '')
    df['Tier'] = df['percentile'].apply(_tier)

    df = df.rename(columns={
        'pillar_macro': 'Macro',
        'pillar_banking': 'Banking',
        'pillar_scale': 'Scale',
        'pillar_institutions': 'Institutions',
        'country_score': 'Score',
        'rank': 'Rank',
        'percentile': 'Percentile',
        'data_coverage': 'Coverage',
    })

    for col in ['Score', 'Macro', 'Banking', 'Scale', 'Institutions']:
        df[col] = df[col].round(2)
    df['Percentile'] = df['Percentile'].round(0).astype('Int64')
    df['Coverage'] = (df['Coverage'] * 100).round(0).astype('Int64')

    return df[[
        'Rank', 'Country', 'TLG', 'Tier', 'Percentile', 'Score',
        'Macro', 'Banking', 'Scale', 'Institutions', 'Coverage',
    ]].sort_values('Rank', na_position='last').reset_index(drop=True)


def _build_score_chart(df):
    """Horizontal bar chart of percentiles, TLG countries in gold."""
    plot_df = df.dropna(subset=['Percentile']).sort_values('Percentile', ascending=True)
    bar_colors = [
        COLORS['tlg'] if df.loc[df['Country'] == c, 'TLG'].iloc[0] == '●'
        else COLORS['navy']
        for c in plot_df['Country']
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=plot_df['Percentile'],
        y=plot_df['Country'],
        orientation='h',
        marker={'color': bar_colors},
        hovertemplate='<b>%{y}</b><br>%{x}th percentile<extra></extra>',
    ))
    fig.update_layout(
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k != 'xaxis'},
        height=600,
        showlegend=False,
        xaxis_title='Percentile within the 27-country universe',
        yaxis_title='',
        xaxis={
            'gridcolor': COLORS['border'],
            'zerolinecolor': COLORS['border'],
            'range': [0, 100],
        },
    )
    return fig


_df = _build_table_df()
_fig = _build_score_chart(_df)


_style_rules = [
    {
        'if': {'filter_query': '{Tier} = "Top"', 'column_id': 'Tier'},
        'color': COLORS['positive'], 'fontWeight': '600',
    },
    {
        'if': {'filter_query': '{Tier} = "Strong"', 'column_id': 'Tier'},
        'color': COLORS['positive'],
    },
    {
        'if': {'filter_query': '{Tier} = "Weak"', 'column_id': 'Tier'},
        'color': COLORS['negative'], 'fontWeight': '600',
    },
    {
        'if': {'filter_query': '{Tier} = "Mid"', 'column_id': 'Tier'},
        'color': COLORS['text_muted'],
    },
    {
        'if': {'filter_query': '{TLG} = "●"', 'column_id': 'TLG'},
        'color': COLORS['tlg'], 'fontWeight': '700', 'textAlign': 'center',
    },
]


layout = html.Div(
    style=PAGE_STYLE,
    children=[
        html.H1('Country opportunity ranking', style=H1_STYLE),
        html.Div(
            '27 African economies scored across four pillars: macro stability, '
            'banking depth, market scale, and institutional quality. Percentile '
            'shows the country\'s position within the universe; Score is the '
            'underlying composite z-score (mean = 0). TLG footprint markets '
            'are flagged in gold.',
            style=SUBTITLE_STYLE,
        ),

        html.H2('Ranking', style=H2_STYLE),
        dash_table.DataTable(
            data=_df.to_dict('records'),
            columns=[
                {'name': c, 'id': c,
                 'type': 'numeric' if c not in ('Country', 'TLG', 'Tier') else 'text'}
                for c in _df.columns
            ],
            sort_action='native',
            page_action='none',
            style_table={'overflowX': 'auto'},
            style_cell={
                'fontFamily': 'system-ui, -apple-system, sans-serif',
                'fontSize': '13px',
                'padding': '8px 12px',
                'textAlign': 'left',
                'border': f'1px solid {COLORS["border"]}',
            },
            style_header={
                'backgroundColor': COLORS['panel'],
                'fontWeight': '600',
                'borderBottom': f'2px solid {COLORS["border"]}',
            },
            style_data_conditional=_style_rules,
            style_cell_conditional=[
                {'if': {'column_id': c}, 'textAlign': 'right'}
                for c in ['Rank', 'Percentile', 'Score', 'Macro', 'Banking',
                          'Scale', 'Institutions', 'Coverage']
            ],
        ),

        html.H2('Percentile distribution', style=H2_STYLE),
        dcc.Graph(figure=_fig, config={'displayModeBar': False}),
    ],
)