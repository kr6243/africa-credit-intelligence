"""
Re-score articles currently tagged as topic='other' using the expanded taxonomy.

The original sentiment scores stay the same; we only update the topic labels.
This refines the topic distribution without re-running the full pipeline.

Run with: python -m src.module2_nlp.rescore_other
"""

from pathlib import Path
import pandas as pd

from src.module2_nlp.score import score_article, _make_client
from src.module2_nlp.config import COUNTRIES

PROCESSED_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed' / 'sentiment'
SCORED_PATH = PROCESSED_DIR / 'scored_articles.csv'


if __name__ == '__main__':
    if not SCORED_PATH.exists():
        print(f'No scored data at {SCORED_PATH}. Run score.py first.')
        raise SystemExit(1)

    df = pd.read_csv(SCORED_PATH)
    print(f'Loaded {len(df):,} scored articles')

    # find articles to re-score
    mask = (df['topic'] == 'other')
    to_rescore = df[mask].copy()
    print(f'Re-scoring {len(to_rescore)} articles with topic="other"')

    client = _make_client()
    n_changed = 0
    n_errors = 0

    for i, (idx, art) in enumerate(to_rescore.iterrows()):
        iso = art['country']
        display = COUNTRIES.get(iso, (iso, iso))[0]
        themes_short = art.get('themes', '')

        result = score_article(
            client,
            country_name=display,
            source=art.get('domain', ''),
            url=art.get('url', ''),
            themes=themes_short,
        )

        if 'error' in result:
            n_errors += 1
        elif result.get('topic') and result['topic'] != 'other':
            # only update topic; keep original sentiment/confidence/key_quote
            df.at[idx, 'topic'] = result['topic']
            n_changed += 1

        if (i + 1) % 50 == 0:
            print(f'  ...processed {i + 1}/{len(to_rescore)} '
                  f'(changed: {n_changed}, errors: {n_errors})')

    df.to_csv(SCORED_PATH, index=False)
    print(f'\nDone. {n_changed} articles re-tagged, {n_errors} errors')
    print(f'New topic distribution:')
    print(df['topic'].value_counts().to_dict())