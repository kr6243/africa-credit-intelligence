"""
Shared visual style. Keep this small and consistent so the dashboard reads
as one piece rather than four loosely-related pages.
"""

# Professional palette: navy / charcoal / muted accents. Avoid the default
# Plotly rainbow which looks generic.
COLORS = {
    'bg': '#ffffff',
    'panel': '#f8f9fb',
    'border': '#e3e6ee',
    'text': '#1a2332',
    'text_muted': '#6b7280',
    'navy': '#1e3a5f',
    'accent': '#c89b3c',     # muted gold for highlights
    'positive': '#2d6a4f',   # forest green for good scores
    'negative': '#9b2c2c',   # dark red for bad scores
    'tlg': '#c89b3c',        # gold for TLG footprint flag
}

FONTS = {
    'body': 'system-ui, -apple-system, "Segoe UI", sans-serif',
    'mono': '"SF Mono", Menlo, Consolas, monospace',
}

# Common style objects we'll reuse across pages.
PAGE_STYLE = {
    'fontFamily': FONTS['body'],
    'backgroundColor': COLORS['bg'],
    'color': COLORS['text'],
    'padding': '24px 32px',
    'maxWidth': '1200px',
    'margin': '0 auto',
    'minHeight': '100vh',
}

H1_STYLE = {
    'fontSize': '24px',
    'fontWeight': '600',
    'color': COLORS['text'],
    'marginBottom': '4px',
}

H2_STYLE = {
    'fontSize': '16px',
    'fontWeight': '600',
    'color': COLORS['text'],
    'marginTop': '32px',
    'marginBottom': '12px',
    'borderBottom': f'1px solid {COLORS["border"]}',
    'paddingBottom': '6px',
}

SUBTITLE_STYLE = {
    'fontSize': '13px',
    'color': COLORS['text_muted'],
    'marginBottom': '24px',
}

PLOTLY_LAYOUT = {
    'font': {'family': FONTS['body'], 'color': COLORS['text'], 'size': 12},
    'paper_bgcolor': COLORS['bg'],
    'plot_bgcolor': COLORS['bg'],
    'margin': {'l': 60, 'r': 20, 't': 30, 'b': 40},
    'xaxis': {'gridcolor': COLORS['border'], 'zerolinecolor': COLORS['border']},
    'yaxis': {'gridcolor': COLORS['border'], 'zerolinecolor': COLORS['border']},
}