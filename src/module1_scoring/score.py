"""
Country opportunity scoring.

Pipeline:
  1. Z-score each feature across the 27 countries.
  2. Multiply by direction (+1 if higher is better, -1 if lower is better)
     so a positive z always means 'good for credit deployment'.
  3. Pillar score = mean of signed z-scores within the pillar, computed
     over features the country has data for. Requires at least
     MIN_PILLAR_COVERAGE of the pillar's features to be present.
  4. Country score = mean of pillar scores (equal weights). Requires at
     least MIN_PILLARS pillars to be non-null; otherwise country is
     flagged as insufficient data and excluded from the ranking.
  5. Rank, percentile, save.

Run with: python -m src.module1_scoring.score
"""

from pathlib import Path
import pandas as pd
import numpy as np

from src.module1_scoring.config import (
    INDICATORS,
    IIAG_FEATURES,
    PILLARS,
)

PROCESSED_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed'
FEATURES_PATH = PROCESSED_DIR / 'features.csv'

# coverage rules
MIN_PILLAR_COVERAGE = 0.5   # need 50% of features in a pillar
MIN_PILLARS = 3             # need 3 of 4 pillars to be ranked


def feature_directions():
    """Return dict: feature name -> (pillar, signed direction)."""
    out = {}
    for _code, name, pillar, direction in INDICATORS:
        # direction 0 (volatility) means 'lower is better'
        signed = -1 if direction == 0 else direction
        out[name] = (pillar, signed)
    for _col, name, pillar, direction in IIAG_FEATURES:
        out[name] = (pillar, direction)
    return out


def zscore_signed(features):
    """Z-score each feature across countries and apply direction sign."""
    directions = feature_directions()
    z = features.set_index('country').copy()

    for col in z.columns:
        if col not in directions:
            continue
        _pillar, sign = directions[col]
        mean = z[col].mean()
        std = z[col].std(ddof=1)
        if std == 0 or np.isnan(std):
            z[col] = np.nan
        else:
            z[col] = sign * (z[col] - mean) / std

    return z.reset_index()


def pillar_scores(signed_z, min_coverage=MIN_PILLAR_COVERAGE):
    """
    Average signed z-scores within each pillar.
    A pillar score is NaN if fewer than min_coverage of its features are present.
    """
    directions = feature_directions()
    z = signed_z.set_index('country')

    out = pd.DataFrame(index=z.index)
    for pillar in PILLARS:
        pillar_cols = [name for name, (p, _s) in directions.items() if p == pillar]
        pillar_cols = [c for c in pillar_cols if c in z.columns]
        n_features = len(pillar_cols)

        sub = z[pillar_cols]
        coverage = sub.notna().sum(axis=1) / n_features
        raw_mean = sub.mean(axis=1, skipna=True)

        # null out pillar scores where coverage falls short
        out[f'pillar_{pillar}'] = raw_mean.where(coverage >= min_coverage)

    return out.reset_index()


def country_score(pillar_df, features, min_pillars=MIN_PILLARS):
    """
    Equal-weighted mean of pillar scores.
    
    Countries with fewer than min_pillars non-null pillars get country_score = NaN
    and are flagged with insufficient_data = True.
    
    Countries missing the banking pillar specifically are scored but excluded
    from the headline ranking. Banking is the most credit-relevant pillar; ranking
    a country without it against fully-scored peers would be misleading.
    """
    pillar_cols = [c for c in pillar_df.columns if c.startswith('pillar_')]
    out = pillar_df.copy()

    n_pillars_present = out[pillar_cols].notna().sum(axis=1)
    out['country_score'] = out[pillar_cols].mean(axis=1, skipna=True)
    out['country_score'] = out['country_score'].where(n_pillars_present >= min_pillars)
    out['insufficient_data'] = n_pillars_present < min_pillars

    # Flag countries missing the banking pillar specifically
    out['missing_banking_pillar'] = out['pillar_banking'].isna()

    # overall data coverage across all features
    feat_cols = [c for c in features.columns if c != 'country']
    coverage = features.set_index('country')[feat_cols].notna().mean(axis=1)
    out = out.merge(
        coverage.rename('data_coverage').reset_index(),
        on='country',
    )

    # Rank only countries that have ALL four pillars and aren't insufficient_data.
    # Partial-data countries (e.g. missing banking) get no rank/percentile to
    # avoid misleading comparison with fully-scored peers.
    ranked_mask = ~out['insufficient_data'] & ~out['missing_banking_pillar']
    
    out['rank'] = pd.NA
    out['percentile'] = pd.NA
    
    if ranked_mask.any():
        ranked_scores = out.loc[ranked_mask, 'country_score']
        ranks = ranked_scores.rank(ascending=False, method='min')
        # percentile within the ranked group
        n = ranked_mask.sum()
        percentiles = (1 - (ranks - 1) / n) * 100
        
        out.loc[ranked_mask, 'rank'] = ranks.astype('Int64')
        out.loc[ranked_mask, 'percentile'] = percentiles
    
    out['rank'] = out['rank'].astype('Int64')

    return out.sort_values(
        ['insufficient_data', 'missing_banking_pillar', 'rank'],
        ascending=[True, True, True],
    ).reset_index(drop=True)

if __name__ == '__main__':
    print(f'Loading features from {FEATURES_PATH.name}')
    features = pd.read_csv(FEATURES_PATH)
    print(f'  {len(features)} countries, {features.shape[1] - 1} features')
    print(f'  Rules: pillar requires >={MIN_PILLAR_COVERAGE:.0%} feature coverage, '
          f'country requires >={MIN_PILLARS}/4 pillars, '
          f'plus banking pillar present for ranking')

    z = zscore_signed(features)
    pillars = pillar_scores(z)
    scored = country_score(pillars, features)

    out_path = PROCESSED_DIR / 'country_scores.csv'
    scored.to_csv(out_path, index=False)

    n_insufficient = scored['insufficient_data'].sum()
    n_partial = scored['missing_banking_pillar'].sum() - n_insufficient
    n_ranked = len(scored) - n_insufficient - n_partial

    print(f'\n{n_ranked} countries fully ranked')
    print(f'{n_partial} countries excluded from ranking (banking pillar missing)')
    print(f'{n_insufficient} countries flagged as insufficient_data')

    cols_to_show = ['country', 'country_score', 'rank', 'percentile', 'data_coverage']
    pillar_cols = [c for c in scored.columns if c.startswith('pillar_')]

    print(f'\n=== Top 10 (full data) ===')
    ranked_df = scored[~scored['insufficient_data'] & ~scored['missing_banking_pillar']]
    print(ranked_df.head(10)[cols_to_show + pillar_cols].round(2).to_string(index=False))

    print(f'\n=== Bottom 5 (full data) ===')
    print(ranked_df.tail(5)[cols_to_show + pillar_cols].round(2).to_string(index=False))

    if n_partial > 0:
        print(f'\n=== Partial data: banking pillar missing ===')
        partial_df = scored[scored['missing_banking_pillar'] & ~scored['insufficient_data']]
        print(partial_df[['country', 'country_score', 'data_coverage'] + pillar_cols].round(2).to_string(index=False))

    if n_insufficient > 0:
        print(f'\n=== Insufficient data ===')
        print(scored[scored['insufficient_data']][['country', 'data_coverage'] + pillar_cols].round(2).to_string(index=False))