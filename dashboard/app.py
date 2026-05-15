"""
Main Dash app. Sets up multi-page routing using dcc.Location.
Run with: python -m dashboard.app
"""

from dash import Dash, html, dcc, Input, Output

from dashboard.components.header import make_header
from dashboard.components.styling import COLORS, FONTS

from dashboard.pages import overview, country, sectors, methodology


app = Dash(__name__, suppress_callback_exceptions=True, title='Africa Credit Intelligence')

app.layout = html.Div(
    children=[
        dcc.Location(id='url', refresh=False),
        make_header(),
        html.Div(id='page-content'),
    ],
    style={
        'fontFamily': FONTS['body'],
        'backgroundColor': COLORS['bg'],
        'minHeight': '100vh',
    },
)


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
)
def render_page(pathname):
    if pathname == '/country':
        return country.layout
    if pathname == '/sectors':
        return sectors.layout
    if pathname == '/methodology':
        return methodology.layout
    return overview.layout  # default = overview


# register page-specific callbacks (each page module exposes a `register_callbacks` fn)
country.register_callbacks(app)
sectors.register_callbacks(app)


if __name__ == '__main__':
    app.run(debug=True, port=8050)