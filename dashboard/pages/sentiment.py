"""
Sentiment page: country-level news sentiment monitoring (Module 2).
Shows a ranked table of all 27 countries plus a country-detail panel with
weekly time series and recent articles.
"""

from datetime import datetime
from dash import html, dcc, dash_table, Input, Output
import plotly.graph_objects as go
import pandas as pd

from dashboard.data_loader import (
    SENTIMENT_SUMMARY, SENTIMENT_WEEKLY, SENTIMENT_ARTICLES,
    SENTIMENT_AVAILABLE, COUNTRY_NAMES, TLG_FOOTPRINT,
)
from dashboard.components.styling import (
    PAGE_STYLE, H1_STYLE, H2_STYLE, SUBTITLE_STYLE, COLORS, PLOTLY_LAYOUT,
)


# Minimum articles in the 30-day window for a country to be considered
# well-sampled. Below this we flag the score as low-volume.
MIN_ARTICLES_RELIABLE = 50

_DEFAULT_COUNTRY = 'KEN'


def _parse_gdelt_date(value):
    """GDELT date is an int like 20260516124500 -> datetime."""
    if pd.isna(value):
        return pd.NaT
    try:
        return datetime.strptime(str(int(value))[:8], '%Y%m%d')
    except (ValueError, TypeError):
        return pd.NaT


def _signal_tag(sentiment, n_articles, top_threshold, bottom_threshold):
    """Convert sentiment + volume into a relative position label.
    
    Uses quartiles of the country distribution rather than absolute thresholds,
    because African macro sentiment is structurally negative-skewed."""
    if pd.isna(sentiment):
        return 'no data'
    if n_articles < MIN_ARTICLES_RELIABLE:
        return 'low volume'
    if sentiment >= top_threshold:
        return 'top quartile'
    if sentiment <= bottom_threshold:
        return 'bottom quartile'
    return 'mid range'


def _build_summary_table():
    if not SENTIMENT_AVAILABLE or SENTIMENT_SUMMARY.empty:
        return None
    df = SENTIMENT_SUMMARY.copy()
    df['Country'] = df['country_name']
    df['TLG'] = df['country'].apply(lambda c: '●' if c in TLG_FOOTPRINT else '')
    # Compute quartile thresholds from the actual data
    valid = df['sentiment_30d'].dropna()
    top_threshold = valid.quantile(0.75)
    bottom_threshold = valid.quantile(0.25)
    df['Signal'] = df.apply(
        lambda r: _signal_tag(
            r['sentiment_30d'], r['n_articles_30d'],
            top_threshold, bottom_threshold,
        ),
        axis=1,
    )
    df['Sentiment (30d)'] = df['sentiment_30d'].round(2)
    df['Δ vs prior 30d'] = df['sentiment_change'].round(2)
    df['Articles (30d)'] = df['n_articles_30d'].astype('Int64')
    df['Articles (total)'] = df['n_articles_total'].astype('Int64')
    df['Top topic'] = df['top_topic']

    df = df[[
        'Country', 'TLG', 'Signal', 'Sentiment (30d)', 'Δ vs prior 30d',
        'Articles (30d)', 'Articles (total)', 'Top topic',
    ]].sort_values('Sentiment (30d)', ascending=False, na_position='last').reset_index(drop=True)

    return df


def _build_country_detail(country_iso):
    """Build the per-country panel: header, line chart, topic chart, article list."""
    if not SENTIMENT_AVAILABLE:
        return html.Div('Sentiment data not available.', style=SUBTITLE_STYLE)

    name = COUNTRY_NAMES.get(country_iso, country_iso)
    summary_row = SENTIMENT_SUMMARY[SENTIMENT_SUMMARY['country'] == country_iso]
    if summary_row.empty:
        return html.Div(f'No sentiment data for {name}.', style=SUBTITLE_STYLE)
    s = summary_row.iloc[0]

    # Header card
    sent_30d = s['sentiment_30d']
    sent_change = s['sentiment_change']
    n_30d = int(s['n_articles_30d']) if pd.notna(s['n_articles_30d']) else 0
    # Compute thresholds from the full distribution for the country detail header
    valid = SENTIMENT_SUMMARY['sentiment_30d'].dropna()
    top_threshold = valid.quantile(0.75)
    bottom_threshold = valid.quantile(0.25)
    signal = _signal_tag(sent_30d, n_30d, top_threshold, bottom_threshold)
    color = {
        'top quartile': COLORS['positive'],
        'bottom quartile': COLORS['negative'],
        'mid range': COLORS['text_muted'],
        'low volume': COLORS['text_muted'],
        'no data': COLORS['text_muted'],
    }.get(signal, COLORS['text_muted'])
    change_str = ('—' if pd.isna(sent_change)
                  else f'{sent_change:+.2f} vs prior 30d')
    sent_str = '—' if pd.isna(sent_30d) else f'{sent_30d:+.2f}'

    header = html.Div(
        style={
            'padding': '16px 20px', 'border': f'1px solid {COLORS["border"]}',
            'borderRadius': '6px', 'backgroundColor': COLORS['panel'],
            'marginBottom': '16px',
        },
        children=[
            html.Div(
                style={'display': 'flex', 'alignItems': 'baseline', 'gap': '20px'},
                children=[
                    html.Div(name, style={'fontSize': '22px', 'fontWeight': '600'}),
                    html.Div(f'30d sentiment: {sent_str}',
                             style={'fontSize': '16px', 'color': color,
                                    'fontWeight': '600'}),
                    html.Div(change_str,
                             style={'fontSize': '13px', 'color': COLORS['text_muted']}),
                ],
            ),
            html.Div(
                f'Signal: {signal}  ·  {n_30d} articles in last 30d  ·  '
                f'Top topic: {s["top_topic"]}',
                style={'fontSize': '13px', 'color': COLORS['text_muted'],
                       'marginTop': '6px'},
            ),
        ],
    )

    return html.Div([
        header,
        html.H2('Weekly sentiment trend', style=H2_STYLE),
        dcc.Graph(figure=_build_weekly_chart(country_iso),
                  config={'displayModeBar': False}),
        html.H2('Topic mix (last 90 days)', style=H2_STYLE),
        dcc.Graph(figure=_build_topic_chart(country_iso),
                  config={'displayModeBar': False}),
        html.H2('Recent articles driving sentiment', style=H2_STYLE),
        _build_article_table(country_iso),
    ])


def _build_weekly_chart(country_iso):
    df = SENTIMENT_WEEKLY[SENTIMENT_WEEKLY['country'] == country_iso].copy()
    if df.empty:
        return go.Figure().update_layout(
            **PLOTLY_LAYOUT, height=320,
            annotations=[{'text': 'No weekly data.', 'showarrow': False,
                          'xref': 'paper', 'yref': 'paper', 'x': 0.5, 'y': 0.5}],
        )

    df = df.sort_values('iso_week')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['iso_week'],
        y=df['weighted_sentiment'],
        mode='lines+markers',
        line={'color': COLORS['navy'], 'width': 2},
        marker={'size': 7, 'color': COLORS['navy']},
        hovertemplate='%{x}<br>Sentiment: %{y:+.2f}<br>Articles: %{customdata}<extra></extra>',
        customdata=df['n_articles'],
        name='Weighted sentiment',
    ))
    fig.add_hline(y=0, line_width=1, line_color=COLORS['text_muted'], line_dash='dot')
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=320,
        showlegend=False,
        yaxis_title='Confidence-weighted sentiment',
        xaxis_title='ISO week',
        yaxis_range=[-1, 1],
    )
    return fig


def _build_topic_chart(country_iso):
    df = SENTIMENT_ARTICLES[
        (SENTIMENT_ARTICLES['country'] == country_iso) &
        (SENTIMENT_ARTICLES['confidence'] >= 0.3)
    ]
    if df.empty:
        return go.Figure().update_layout(
            **PLOTLY_LAYOUT, height=280,
            annotations=[{'text': 'No topic data.', 'showarrow': False,
                          'xref': 'paper', 'yref': 'paper', 'x': 0.5, 'y': 0.5}],
        )

    grouped = df.groupby('topic').agg(
        n=('sentiment', 'size'),
        mean_sent=('sentiment', 'mean'),
    ).reset_index().sort_values('n', ascending=True)

    bar_colors = [
        COLORS['positive'] if v > 0 else COLORS['negative']
        for v in grouped['mean_sent']
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grouped['n'],
        y=grouped['topic'],
        orientation='h',
        marker={'color': bar_colors},
        hovertemplate='<b>%{y}</b><br>Articles: %{x}<br>'
                      'Mean sentiment: %{customdata:+.2f}<extra></extra>',
        customdata=grouped['mean_sent'],
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=280,
        showlegend=False,
        xaxis_title='Article count (colour = mean sentiment)',
        yaxis_title='',
    )
    return fig


def _build_article_table(country_iso):
    df = SENTIMENT_ARTICLES[
        (SENTIMENT_ARTICLES['country'] == country_iso) &
        (SENTIMENT_ARTICLES['confidence'] >= 0.3)
    ].copy()
    if df.empty:
        return html.Div('No articles to display.', style=SUBTITLE_STYLE)

    df['parsed_date'] = df['date'].apply(_parse_gdelt_date)
    df = df.dropna(subset=['parsed_date']).sort_values('parsed_date', ascending=False)
    df = df.head(15)
    df['Date'] = df['parsed_date'].dt.strftime('%Y-%m-%d')
    df['Source'] = df['domain']
    df['Sentiment'] = df['sentiment'].round(2)
    df['Topic'] = df['topic']
    df['Key signal'] = df['key_quote'].fillna('')

    return dash_table.DataTable(
        data=df[['Date', 'Source', 'Sentiment', 'Topic', 'Key signal']].to_dict('records'),
        columns=[
            {'name': 'Date', 'id': 'Date', 'type': 'text'},
            {'name': 'Source', 'id': 'Source', 'type': 'text'},
            {'name': 'Sentiment', 'id': 'Sentiment', 'type': 'numeric'},
            {'name': 'Topic', 'id': 'Topic', 'type': 'text'},
            {'name': 'Key signal', 'id': 'Key signal', 'type': 'text'},
        ],
        page_action='none',
        style_cell={
            'fontFamily': 'system-ui, -apple-system, sans-serif',
            'fontSize': '13px', 'padding': '8px 12px', 'textAlign': 'left',
            'border': f'1px solid {COLORS["border"]}',
            'whiteSpace': 'normal', 'height': 'auto',
        },
        style_header={
            'backgroundColor': COLORS['panel'], 'fontWeight': '600',
            'borderBottom': f'2px solid {COLORS["border"]}',
        },
        style_data_conditional=[
            {'if': {'filter_query': '{Sentiment} > 0.2', 'column_id': 'Sentiment'},
             'color': COLORS['positive'], 'fontWeight': '600'},
            {'if': {'filter_query': '{Sentiment} < -0.2', 'column_id': 'Sentiment'},
             'color': COLORS['negative'], 'fontWeight': '600'},
        ],
        style_cell_conditional=[
            {'if': {'column_id': 'Sentiment'}, 'textAlign': 'right', 'width': '90px'},
            {'if': {'column_id': 'Date'}, 'width': '110px'},
            {'if': {'column_id': 'Topic'}, 'width': '120px'},
        ],
    )


# Build the static parts of the layout
_summary_df = _build_summary_table()

if not SENTIMENT_AVAILABLE or _summary_df is None:
    layout = html.Div(
        style=PAGE_STYLE,
        children=[
            html.H1('Sentiment monitoring', style=H1_STYLE),
            html.Div(
                'Sentiment data not yet available. Run the Module 2 pipeline '
                '(fetch_gdelt → score → aggregate) to populate this page.',
                style=SUBTITLE_STYLE,
            ),
        ],
    )
else:
    _summary_style_rules = [
        {'if': {'filter_query': '{Signal} = "top quartile"', 'column_id': 'Signal'},
         'color': COLORS['positive'], 'fontWeight': '600'},
        {'if': {'filter_query': '{Signal} = "bottom quartile"', 'column_id': 'Signal'},
         'color': COLORS['negative'], 'fontWeight': '600'},
        {'if': {'filter_query': '{Signal} = "mid range"', 'column_id': 'Signal'},
         'color': COLORS['text_muted']},
        {'if': {'filter_query': '{Signal} = "low volume"', 'column_id': 'Signal'},
         'color': COLORS['text_muted'], 'fontStyle': 'italic'},
        {'if': {'filter_query': '{TLG} = "●"', 'column_id': 'TLG'},
         'color': COLORS['tlg'], 'fontWeight': '700', 'textAlign': 'center'},
        {'if': {'filter_query': '{Sentiment (30d)} > 0.05', 'column_id': 'Sentiment (30d)'},
         'color': COLORS['positive']},
        {'if': {'filter_query': '{Sentiment (30d)} < -0.05', 'column_id': 'Sentiment (30d)'},
         'color': COLORS['negative']},
    ]

    _country_dropdown_options = [
        {'label': COUNTRY_NAMES.get(c, c), 'value': c}
        for c in sorted(SENTIMENT_SUMMARY['country'].unique(),
                        key=lambda c: COUNTRY_NAMES.get(c, c))
    ]

    layout = html.Div(
        style=PAGE_STYLE,
        children=[
            html.H1('Sentiment monitoring', style=H1_STYLE),
            html.Div(
                'News sentiment across 27 African economies over the last 90 days. '
                f'{int(SENTIMENT_ARTICLES["country"].count()):,} articles from '
                f'{SENTIMENT_ARTICLES["domain"].nunique()} sources scored by Claude '
                'with confidence-weighted aggregation. Countries flagged "low volume" '
                f'have fewer than {MIN_ARTICLES_RELIABLE} articles in the 30-day window; '
                'treat their scores cautiously.',
                style=SUBTITLE_STYLE,
            ),

            html.H2('Country sentiment ranking (last 30 days)', style=H2_STYLE),
            dash_table.DataTable(
                data=_summary_df.to_dict('records'),
                columns=[
                    {'name': c, 'id': c,
                     'type': 'numeric' if c in ('Sentiment (30d)', 'Δ vs prior 30d',
                                                'Articles (30d)', 'Articles (total)')
                     else 'text'}
                    for c in _summary_df.columns
                ],
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
                style_data_conditional=_summary_style_rules,
                style_cell_conditional=[
                    {'if': {'column_id': c}, 'textAlign': 'right'}
                    for c in ['Sentiment (30d)', 'Δ vs prior 30d',
                              'Articles (30d)', 'Articles (total)']
                ],
            ),

            html.H2('Country detail', style=H2_STYLE),
            dcc.Dropdown(
                id='sentiment-country-dropdown',
                options=_country_dropdown_options,
                value=_DEFAULT_COUNTRY,
                clearable=False,
                style={'maxWidth': '320px', 'marginBottom': '24px'},
            ),

            html.Div(id='sentiment-country-detail'),
        ],
    )


def register_callbacks(app):
    @app.callback(
        Output('sentiment-country-detail', 'children'),
        Input('sentiment-country-dropdown', 'value'),
    )
    def update_country_detail(country_iso):
        return _build_country_detail(country_iso)