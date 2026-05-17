"""
Sentiment scoring via Anthropic Claude API.

For each article (title + optional snippet), we ask Claude for a structured
score: sentiment (-1 to +1), confidence (0 to 1), topic (one of a small set),
and a key quote.

We cache by (country, url) so reruns don't re-charge for the same article.

Run with: python -m src.module2_nlp.score
"""

from pathlib import Path
import json
import os
import time
import pandas as pd
from src.module2_nlp.config import COUNTRIES
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

RAW_DIR = Path(__file__).resolve().parents[2] / 'data' / 'raw' / 'news'
PROCESSED_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed' / 'sentiment'

ARTICLES_PATH = RAW_DIR / 'gdelt_articles.csv'
CACHE_PATH = PROCESSED_DIR / 'scored_articles.csv'

MODEL = 'claude-sonnet-4-6'
MAX_TOKENS = 400

TOPICS = [
    'monetary',      # central bank policy, rates, money supply
    'fiscal',        # government budget, debt, taxation
    'banking',       # commercial banks, NPLs, credit, financial sector
    'currency',      # FX rates, devaluation, capital controls
    'political',     # elections, conflict, governance, policy uncertainty
    'trade',         # imports/exports, trade balance, customs
    'investment',    # FDI, factory openings, M&A, capital inflows
    'infrastructure',# telecoms, transport, energy projects, logistics
    'commodities',   # oil, copper, cocoa, agricultural prices
    'other',         # genuinely uncategorisable
]

PROMPT_TEMPLATE = """You are a financial analyst at a private credit fund evaluating African \
markets. Read the URL slug and GDELT theme tags for the following news article about {country_name}, \
then return a JSON object with EXACTLY these four fields and no others:

- sentiment: float from -1.0 to +1.0. Negative means bad for SME credit deployment in this \
country (rising risk, deteriorating macro, political instability). Positive means good \
(stability improving, growth, market opening). Zero means neutral or factual without \
directional implication.
- confidence: float from 0.0 to 1.0. How confident you are in this assessment.
- topic: one of: monetary, fiscal, banking, currency, political, trade, investment, infrastructure, commodities, other. Use 'other' ONLY for articles that genuinely don't fit any of the above categories.
- key_quote: a short phrase (max 15 words) describing the key signal (from URL slug or themes) that drove your score.
Do NOT include reasoning, explanations, additional fields, preamble, or markdown fences. \
Return ONLY the four-field JSON object.

Source: {source}
URL: {url}
GDELT themes: {themes}
"""


def _make_client():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise RuntimeError('ANTHROPIC_API_KEY not found in environment. Check .env.')
    return Anthropic(api_key=api_key)


def score_article(client, country_name, source, url, themes):
    """Send one article to Claude and parse the JSON response."""
    prompt = PROMPT_TEMPLATE.format(
        country_name=country_name,
        source=source or '',
        url=url or '',
        themes=themes or '',
    )

    # Retry up to 3 times for transient API errors (500s, timeouts)
    last_err = None
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{'role': 'user', 'content': prompt}],
            )
            text = response.content[0].text.strip()
            break
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)  # 1s, 2s, 4s exponential backoff
    else:
        return {'error': f'{type(last_err).__name__}: {last_err}'}

    # Strip code fences if Claude added them despite instructions
    if text.startswith('```'):
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]
        text = text.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {'error': 'invalid_json', 'raw_response': text[:200]}

    # validate structure
    for key in ('sentiment', 'confidence', 'topic', 'key_quote'):
        if key not in parsed:
            return {'error': f'missing_field_{key}', 'raw_response': text[:200]}

    if parsed['topic'] not in TOPICS:
        parsed['topic'] = 'other'

    # clip to valid ranges
    parsed['sentiment'] = max(-1.0, min(1.0, float(parsed['sentiment'])))
    parsed['confidence'] = max(0.0, min(1.0, float(parsed['confidence'])))

    return parsed


def score_articles(articles_df, cache_df=None, max_per_run=None):
    """Score all unscored articles in articles_df. Writes incremental progress to cache."""
    client = _make_client()
    cached_urls = set(cache_df['url']) if cache_df is not None and not cache_df.empty else set()
    to_score = articles_df[~articles_df['DocumentIdentifier'].isin(cached_urls)].copy()
    if max_per_run:
        to_score = to_score.head(max_per_run)

    print(f'Scoring {len(to_score)} articles (cache hits: {len(articles_df) - len(to_score)})')

    rows = []
    for i, art in to_score.iterrows():
        # GDELT V2Themes is a semicolon-separated list of theme codes. Take first 8 themes
        # so we don't overwhelm the prompt while keeping the most relevant tags.
        themes_raw = art.get('V2Themes', '') or ''
        themes_short = ';'.join(themes_raw.split(';')[:8])

        # Map ISO3 to display name for the prompt
        iso = art.get('country', '')
        display_name = COUNTRIES.get(iso, (iso, iso))[0]
        
        result = score_article(
            client,
            country_name=display_name,
            source=art.get('SourceCommonName', ''),
            url=art.get('DocumentIdentifier', ''),
            themes=themes_short,
        )
        row = {
            'country': art['country'],
            'url': art['DocumentIdentifier'],
            'date': art.get('DATE', ''),
            'domain': art.get('SourceCommonName', ''),
            'themes': themes_short,
            **result,
        }
        rows.append(row)

        # Print progress and a tiny pause to avoid hitting Anthropic rate limits
        if (i + 1) % 10 == 0:
            print(f'  ...scored {i + 1}/{len(to_score)}')
        time.sleep(0.3)

    new_scored = pd.DataFrame(rows)
    combined = pd.concat([cache_df, new_scored], ignore_index=True) if cache_df is not None else new_scored
    return combined


if __name__ == '__main__':
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not ARTICLES_PATH.exists():
        print(f'No article data at {ARTICLES_PATH}. Run fetch_gdelt first.')
        raise SystemExit(1)

    articles = pd.read_csv(ARTICLES_PATH)
    print(f'Loaded {len(articles):,} articles from {ARTICLES_PATH.name}')

    cache = pd.read_csv(CACHE_PATH) if CACHE_PATH.exists() else None
    if cache is not None:
        print(f'Cache: {len(cache)} previously scored articles')

    scored = score_articles(articles, cache_df=cache)
    scored.to_csv(CACHE_PATH, index=False)

    n_errors = scored['error'].notna().sum() if 'error' in scored.columns else 0
    print(f'\nSaved {len(scored):,} scored articles to {CACHE_PATH}')
    print(f'Errors: {n_errors}')
    if 'sentiment' in scored.columns:
        valid = scored[scored['sentiment'].notna()]
        print(f'Mean sentiment: {valid["sentiment"].mean():.2f}')
        print(f'Topic distribution: {valid["topic"].value_counts().to_dict()}')