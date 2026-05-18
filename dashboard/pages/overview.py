"""
Overview page: ranked country opportunity scores with pillar breakdowns.
Countries with insufficient banking data are shown separately to avoid
misleading rank comparisons.
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


def _format_df(df):
    """Common formatting for both the full and partial tables."""
    df = df.copy()
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
    df['Percentile'] = pd.to_numeric(df['Percentile'], errors='coerce').round(0).astype('Int64')
    df['Coverage'] = (pd.to_numeric(df['Coverage'], errors='coerce') * 100).round(0).astype('Int64')
    return df


def _build_tables():
    """Split into full-data and partial-data tables. Re-rank full-data countries."""
    df = COUNTRY_SCORES.copy()
    
    # Partial-data: missing banking pillar (the most credit-relevant pillar)
    partial_mask = df['pillar_banking'].isna()
    
    full_df = df[~partial_mask].copy()
    partial_df = df[partial_mask].copy()
    
    # Re-rank the full-data countries against each other
    full_df = full_df.sort_values('country_score', ascending=False, na_position='last').reset_index(drop=True)
    full_df['rank'] = range(1, len(full_df) + 1)
    full_df['percentile'] = (1 - (full_df['rank'] - 1) / len(full_df)) * 100
    
    # Partial-data countries: no rank, no percentile (would be misleading)
    partial_df['rank'] = pd.NA
    partial_df['percentile'] = pd.NA
    partial_df = partial_df.sort_values('country_score', ascending=False)
    
    return _format_df(full_df), _format_df(partial_df)


def _build_score_chart(df):
    """Horizontal bar chart of percentiles, TLG countries in gold. Full-data only."""
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
        height=520,
        showlegend=False,
        xaxis_title='Percentile within the fully-scored universe',
        yaxis_title='',
        xaxis={
            'gridcolor': COLORS['border'],
            'zerolinecolor': COLORS['border'],
            'range': [0, 100],
        },
    )
    return fig


_full_df, _partial_df = _build_tables()
_fig = _build_score_chart(_full_df)


_style_rules = [
    {'if': {'filter_query': '{Tier} = "Top"', 'column_id': 'Tier'},
     'color': COLORS['positive'], 'fontWeight': '600'},
    {'if': {'filter_query': '{Tier} = "Strong"', 'column_id': 'Tier'},
     'color': COLORS['positive']},
    {'if': {'filter_query': '{Tier} = "Weak"', 'column_id': 'Tier'},
     'color': COLORS['negative'], 'fontWeight': '600'},
    {'if': {'filter_query': '{Tier} = "Mid"', 'column_id': 'Tier'},
     'color': COLORS['text_muted']},
    {'if': {'filter_query': '{TLG} = "●"', 'column_id': 'TLG'},
     'color': COLORS['tlg'], 'fontWeight': '700', 'textAlign': 'center'},
]


def _table(records, columns_to_show, show_rank=True):
    """Reusable DataTable with our standard style."""
    columns = [
        {'name': c, 'id': c,
         'type': 'numeric' if c not in ('Country', 'TLG', 'Tier') else 'text'}
        for c in columns_to_show
    ]
    return dash_table.DataTable(
        data=records,
        columns=columns,
        sort_action='native',
        page_action='none',
        style_table={'overflowX': 'auto'},
        style_cell={
            'fontFamily': 'system-ui, -apple-system, sans-serif',
            'fontSize': '13px', 'padding': '8px 12px', 'textAlign': 'left',
            'border': f'1px solid {COLORS["border"]}',
        },
        style_header={
            'backgroundColor': COLORS['panel'], 'fontWeight': '600',
            'borderBottom': f'2px solid {COLORS["border"]}',
        },
        style_data_conditional=_style_rules,
        style_cell_conditional=[
            {'if': {'column_id': c}, 'textAlign': 'right'}
            for c in ['Rank', 'Percentile', 'Score', 'Macro', 'Banking',
                      'Scale', 'Institutions', 'Coverage']
        ],
    )


_full_columns = ['Rank', 'Country', 'TLG', 'Tier', 'Percentile', 'Score',
                 'Macro', 'Banking', 'Scale', 'Institutions', 'Coverage']
_partial_columns = ['Country', 'TLG', 'Score',
                    'Macro', 'Banking', 'Scale', 'Institutions', 'Coverage']


layout = html.Div(
    style=PAGE_STYLE,
    children=[
        html.H1('Country opportunity ranking', style=H1_STYLE),
        html.Div(
            f'{len(_full_df)} fully-scored economies ranked across four pillars: '
            'macro stability, banking depth, market scale, and institutional '
            'quality. Percentile shows the country\'s position within the '
            'fully-scored universe (50th = median, 100th = top). Score is the '
            'underlying composite z-score (mean = 0). TLG footprint markets are '
            'flagged in gold.',
            style=SUBTITLE_STYLE,
        ),

        html.H2('Ranking (full data)', style=H2_STYLE),
        _table(_full_df.to_dict('records'), _full_columns),

        html.H2('Percentile distribution', style=H2_STYLE),
        dcc.Graph(figure=_fig, config={'displayModeBar': False}),

        html.H2('Partial-data countries', style=H2_STYLE),
        html.Div(
            f'{len(_partial_df)} countries (Benin, Mali, Togo, Tunisia) are '
            'excluded from the headline ranking because their banking pillar '
            'is unavailable from World Bank WDI coverage. Macro, scale, and '
            'institutions can be scored, but a credit-deployment ranking '
            'without the banking sector view is misleading. An extension using '
            'IMF Financial Soundness Indicators would close this gap. The '
            'scores below are shown for transparency, not for direct comparison '
            'with the ranked countries.',
            style=SUBTITLE_STYLE,
        ),
        _table(_partial_df.to_dict('records'), _partial_columns),
    ],
)