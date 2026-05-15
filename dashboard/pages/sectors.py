"""
Sectors page: country x sector heatmap plus per-sector top 10.
"""

from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import pandas as pd

from dashboard.data_loader import (
    SECTOR_SCORES, COUNTRY_SCORES, COUNTRY_NAMES, TLG_FOOTPRINT,
)
from dashboard.components.styling import (
    PAGE_STYLE, H1_STYLE, H2_STYLE, SUBTITLE_STYLE, COLORS, PLOTLY_LAYOUT,
)


SECTORS = ['healthcare', 'consumer', 'agribusiness', 'education']


def _build_heatmap():
    """Country (rows) x sector (cols) heatmap, rows ordered by country score."""
    # wide-format pivot: countries x sectors
    pivot = SECTOR_SCORES.pivot(index='country', columns='sector', values='sector_score')

    # order rows by country score (best first)
    country_order = (
        COUNTRY_SCORES.set_index('country')['country_score']
        .sort_values(ascending=False)
        .index
    )
    pivot = pivot.reindex(country_order)
    pivot = pivot[SECTORS]  # consistent column order

    # row labels with TLG marker
    row_labels = [
        f'{COUNTRY_NAMES.get(c, c)}{"  ●" if c in TLG_FOOTPRINT else ""}'
        for c in pivot.index
    ]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[s.title() for s in pivot.columns],
        y=row_labels,
        colorscale=[
            [0.0, COLORS['negative']],
            [0.5, '#f4f4f6'],
            [1.0, COLORS['positive']],
        ],
        zmid=0,
        hovertemplate='<b>%{y}</b><br>%{x}: %{z:.2f}<extra></extra>',
        colorbar={'title': 'Score', 'thickness': 12, 'len': 0.8},
    ))
    fig.update_layout(
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ('xaxis', 'yaxis', 'margin')},
        height=700,
        xaxis={'side': 'top', 'tickfont': {'size': 12}},
        yaxis={'tickfont': {'size': 11}, 'autorange': 'reversed'},
        margin={'l': 140, 'r': 40, 't': 60, 'b': 40},
    )
    return fig


def _build_sector_top10(sector):
    """Bar chart of top 10 countries for a given sector, x-axis = percentile within sector."""
    sub = SECTOR_SCORES[SECTOR_SCORES['sector'] == sector].copy()
    sub = sub.dropna(subset=['sector_score']).sort_values('sector_score', ascending=False).head(10)
    sub['label'] = sub['country'].map(COUNTRY_NAMES).fillna(sub['country'])
    sub['color'] = sub['country'].apply(
        lambda c: COLORS['tlg'] if c in TLG_FOOTPRINT else COLORS['navy']
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sub['percentile'],
        y=sub['label'],
        orientation='h',
        marker={'color': sub['color']},
        text=sub['percentile'].round(0).astype(int).astype(str) + 'th pct',
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>%{x:.0f}th percentile<br>'
                      'Score: %{customdata:.2f}<extra></extra>',
        customdata=sub['sector_score'],
    ))
    fig.update_layout(
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k != 'yaxis' and k != 'xaxis'},
        height=350,
        showlegend=False,
        xaxis_title='Percentile within sector',
        yaxis_title='',
        xaxis={
            'gridcolor': COLORS['border'],
            'zerolinecolor': COLORS['border'],
            'range': [0, 115],  # extra space for text labels
        },
        yaxis={
            'gridcolor': COLORS['border'],
            'zerolinecolor': COLORS['border'],
            'autorange': 'reversed',
        },
    )
    return fig


_heatmap = _build_heatmap()

layout = html.Div(
    style=PAGE_STYLE,
    children=[
        html.H1('Sector view', style=H1_STYLE),
        html.Div(
            'Country-sector opportunity heatmap for the four TLG focus sectors. '
            'Rows are ordered by overall country score. Gold dots flag TLG '
            'footprint markets. Cells are z-scored within each sector.',
            style=SUBTITLE_STYLE,
        ),

        html.H2('Country × sector heatmap', style=H2_STYLE),
        dcc.Graph(figure=_heatmap, config={'displayModeBar': False}),

        html.H2('Top 10 per sector', style=H2_STYLE),
        dcc.Dropdown(
            id='sector-dropdown',
            options=[{'label': s.title(), 'value': s} for s in SECTORS],
            value='healthcare',
            clearable=False,
            style={'maxWidth': '260px', 'marginBottom': '16px'},
        ),
        dcc.Graph(id='sector-top10', config={'displayModeBar': False}),
    ],
)


def register_callbacks(app):
    @app.callback(
        Output('sector-top10', 'figure'),
        Input('sector-dropdown', 'value'),
    )
    def update_top10(sector):
        return _build_sector_top10(sector)