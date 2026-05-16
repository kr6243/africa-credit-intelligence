"""
Pull article metadata from GDELT GKG via BigQuery for each country.

Uses BigQuery (not the GDELT Doc API) for two reasons:
  - The Doc API has a 90-day rolling window and aggressive rate limiting
  - BigQuery gives us the full GKG archive with no rate limits

Run with: python -m src.module2_nlp.fetch_gdelt
"""

import os
from pathlib import Path
import pandas as pd
from google.cloud import bigquery

from src.module2_nlp.config import (
    COUNTRIES,
    FINANCIAL_THEMES,
    START_DATE,
    END_DATE,
    LOCATION_POSITION_LIMIT,
    MAX_ARTICLES_PER_COUNTRY,
    GCP_PROJECT,
    GCP_KEY_PATH,
)

RAW_DIR = Path(__file__).resolve().parents[2] / 'data' / 'raw' / 'news'

# resolve the key path relative to the project root
KEY_FULL_PATH = Path(__file__).resolve().parents[2] / GCP_KEY_PATH


def _make_client():
    """BigQuery client authenticated via service account JSON."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(KEY_FULL_PATH)
    return bigquery.Client(project=GCP_PROJECT)


def _theme_clause():
    """Build the SQL clause matching any of the financial themes."""
    parts = [f"V2Themes LIKE '%{theme}%'" for theme in FINANCIAL_THEMES]
    return '(' + ' OR '.join(parts) + ')'


def fetch_country(client, country_iso, search_phrase, max_records):
    """Run a BigQuery query for one country and return a DataFrame."""
    # Most countries: search phrase is plain text, we wrap in #...#
    # DRC-style edge case: search phrase already has #...# (FIPS code), use as-is
    if search_phrase.startswith('#') and search_phrase.endswith('#'):
        match_pattern = search_phrase
    else:
        match_pattern = f'#{search_phrase}#'

    query = f"""
    SELECT
      DATE,
      V2Locations,
      V2Themes,
      V2Tone,
      DocumentIdentifier,
      SourceCommonName
    FROM `gdelt-bq.gdeltv2.gkg_partitioned`
    WHERE _PARTITIONTIME BETWEEN TIMESTAMP('{START_DATE}') AND TIMESTAMP('{END_DATE}')
      AND STRPOS(V2Locations, '{match_pattern}') BETWEEN 1 AND {LOCATION_POSITION_LIMIT}
      AND {_theme_clause()}
    ORDER BY DATE DESC
    LIMIT {max_records}
    """
    df = client.query(query).to_dataframe()
    if df.empty:
        return df
    df['country'] = country_iso
    return df


if __name__ == '__main__':
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    client = _make_client()
    print(f'Fetching GDELT (BigQuery) for {len(COUNTRIES)} countries, '
          f'{START_DATE} to {END_DATE}')
    print(f'Position limit: first {LOCATION_POSITION_LIMIT} chars of V2Locations')

    frames = []
    for iso, (display, search) in COUNTRIES.items():
        print(f'  {iso} ({display})...', end=' ', flush=True)
        df = fetch_country(client, iso, search, MAX_ARTICLES_PER_COUNTRY)
        if df.empty:
            print('0 articles')
        else:
            print(f'{len(df)} articles')
            frames.append(df)

    if not frames:
        print('\nNo articles returned. Aborting before save.')
        raise SystemExit(1)

    panel = pd.concat(frames, ignore_index=True)

    out_path = RAW_DIR / 'gdelt_articles.csv'
    panel.to_csv(out_path, index=False)

    print(f'\nSaved {len(panel):,} articles total to {out_path}')
    print(f'Countries with data: {panel["country"].nunique()} / {len(COUNTRIES)}')
    print(f'Sources: {panel["SourceCommonName"].nunique()} unique')