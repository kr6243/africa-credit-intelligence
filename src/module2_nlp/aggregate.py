"""
Aggregate scored articles into country-level sentiment signals.

Reads scored_articles.csv produced by score.py and produces:
  - country_week.csv: weekly time series per country
  - country_summary.csv: last-30d snapshot per country

Run with: python -m src.module2_nlp.aggregate
"""

from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.module2_nlp.config import COUNTRIES

PROCESSED_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed' / 'sentiment'
SCORED_PATH = PROCESSED_DIR / 'scored_articles.csv'
WEEK_OUT = PROCESSED_DIR / 'country_week.csv'
SUMMARY_OUT = PROCESSED_DIR / 'country_summary.csv'

# Drop articles below this confidence threshold from aggregation.
# Confidence weighting naturally downweights them too, but cutting the long
# tail of <0.3 conf scores keeps the signal cleaner.
MIN_CONFIDENCE = 0.3


def parse_gdelt_date(value):
    """GDELT date is an int like 20260516124500 -> datetime."""
    if pd.isna(value):
        return pd.NaT
    s = str(int(value))
    # YYYYMMDDHHMMSS
    return datetime.strptime(s[:8], '%Y%m%d')


def load_scored():
    """Load scored articles, parse dates, drop rows with errors or no sentiment."""
    df = pd.read_csv(SCORED_PATH)
    print(f'Loaded {len(df):,} scored rows from {SCORED_PATH.name}')

    # drop rows where the scorer returned an error
    if 'error' in df.columns:
        n_err = df['error'].notna().sum()
        df = df[df['error'].isna()].copy()
        print(f'  Dropped {n_err} rows with scorer errors')

    # ensure sentiment is numeric (could be NaN if missing)
    df = df[df['sentiment'].notna()].copy()
    df['sentiment'] = pd.to_numeric(df['sentiment'], errors='coerce')
    df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce')
    df = df.dropna(subset=['sentiment', 'confidence'])

    # parse the date
    df['parsed_date'] = df['date'].apply(parse_gdelt_date)
    df = df.dropna(subset=['parsed_date'])

    # add ISO week label (e.g. '2026-W19')
    df['iso_week'] = df['parsed_date'].dt.strftime('%G-W%V')

    return df


def aggregate_weekly(df):
    """Country x ISO week aggregation."""
    # Filter low confidence
    high_conf = df[df['confidence'] >= MIN_CONFIDENCE].copy()
    print(f'Aggregating {len(high_conf):,} of {len(df):,} articles '
          f'(dropped confidence < {MIN_CONFIDENCE})')

    # Confidence-weighted mean per group
    def weighted_mean(group):
        s = (group['sentiment'] * group['confidence']).sum()
        w = group['confidence'].sum()
        return s / w if w > 0 else np.nan

    grouped = high_conf.groupby(['country', 'iso_week'])
    weekly = grouped.apply(
        lambda g: pd.Series({
            'n_articles': len(g),
            'mean_sentiment': g['sentiment'].mean(),
            'weighted_sentiment': weighted_mean(g),
            'mean_confidence': g['confidence'].mean(),
        }),
        include_groups=False,
    ).reset_index()

    return weekly


def country_summary(df, scored_df):
    """Per-country snapshot: last 30 days vs prior 30 days."""
    high_conf = df[df['confidence'] >= MIN_CONFIDENCE].copy()
    if high_conf.empty:
        return pd.DataFrame()

    cutoff_recent = high_conf['parsed_date'].max() - timedelta(days=30)
    cutoff_prior = cutoff_recent - timedelta(days=30)

    rows = []
    for country, name_tuple in COUNTRIES.items():
        display = name_tuple[0]
        cdf = high_conf[high_conf['country'] == country]
        if cdf.empty:
            rows.append({
                'country': country,
                'country_name': display,
                'n_articles_total': 0,
                'n_articles_30d': 0,
                'sentiment_30d': np.nan,
                'sentiment_prior_30d': np.nan,
                'sentiment_change': np.nan,
                'top_topic': 'no_data',
            })
            continue

        recent = cdf[cdf['parsed_date'] > cutoff_recent]
        prior = cdf[(cdf['parsed_date'] > cutoff_prior) & (cdf['parsed_date'] <= cutoff_recent)]

        def wmean(d):
            if d.empty or d['confidence'].sum() == 0:
                return np.nan
            return (d['sentiment'] * d['confidence']).sum() / d['confidence'].sum()

        recent_sent = wmean(recent)
        prior_sent = wmean(prior)
        change = recent_sent - prior_sent if not pd.isna(recent_sent) and not pd.isna(prior_sent) else np.nan

        top_topic = cdf['topic'].mode().iat[0] if not cdf['topic'].mode().empty else 'mixed'

        rows.append({
            'country': country,
            'country_name': display,
            'n_articles_total': int(len(cdf)),
            'n_articles_30d': int(len(recent)),
            'sentiment_30d': recent_sent,
            'sentiment_prior_30d': prior_sent,
            'sentiment_change': change,
            'top_topic': top_topic,
        })

    return pd.DataFrame(rows)


if __name__ == '__main__':
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not SCORED_PATH.exists():
        print(f'No scored data at {SCORED_PATH}. Run score.py first.')
        raise SystemExit(1)

    scored = load_scored()
    print(f'After cleaning: {len(scored):,} usable rows')
    print(f'Date range: {scored["parsed_date"].min().date()} to {scored["parsed_date"].max().date()}')
    print(f'Countries: {scored["country"].nunique()}')

    weekly = aggregate_weekly(scored)
    weekly.to_csv(WEEK_OUT, index=False)
    print(f'Saved {len(weekly):,} country-week rows to {WEEK_OUT.name}')

    summary = country_summary(scored, scored)
    summary = summary.sort_values('sentiment_30d', ascending=False, na_position='last')
    summary.to_csv(SUMMARY_OUT, index=False)
    print(f'Saved {len(summary)} country summaries to {SUMMARY_OUT.name}')

    # quick sanity prints
    print('\nTop 5 by 30d sentiment:')
    print(summary.head(5)[['country_name', 'sentiment_30d', 'n_articles_30d', 'top_topic']].to_string())
    print('\nBottom 5 by 30d sentiment:')
    print(summary.tail(5)[['country_name', 'sentiment_30d', 'n_articles_30d', 'top_topic']].to_string())