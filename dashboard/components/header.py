"""
Shared top navigation bar. Renders on every page.
"""

from dash import html, dcc
from dashboard.components.styling import COLORS, FONTS


NAV_LINKS = [
    ('Overview', '/'),
    ('Country detail', '/country'),
    ('Sectors', '/sectors'),
    ('Sentiment', '/sentiment'),
    ('Methodology', '/methodology'),
]


def make_header():
    nav_style = {
        'fontFamily': FONTS['body'],
        'fontSize': '14px',
        'color': COLORS['navy'],
        'marginRight': '24px',
        'textDecoration': 'none',
    }
    return html.Div(
        children=[
            html.Div(
                'African Private Credit Market Intelligence',
                style={
                    'fontSize': '18px',
                    'fontWeight': '600',
                    'color': COLORS['navy'],
                    'marginRight': 'auto',
                },
            ),
            *[
                dcc.Link(label, href=href, style=nav_style)
                for label, href in NAV_LINKS
            ],
        ],
        style={
            'display': 'flex',
            'alignItems': 'center',
            'padding': '16px 32px',
            'borderBottom': f'1px solid {COLORS["border"]}',
            'backgroundColor': COLORS['bg'],
            'maxWidth': '1200px',
            'margin': '0 auto',
        },
    )