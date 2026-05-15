"""
Sensitivity analysis for the country scoring.

We rerun the scoring under different methodological choices and report
how stable the top-10 ranking is:

  1. Pillar coverage threshold: 33%, 50% (default), 66%
  2. Pillar weighting schemes: equal (default), macro-tilt, banking-tilt,
     institutions-tilt

Outputs:
  - data/processed/sensitivity_rankings.csv: each country's rank under
    each scenario, side by side.
  - prints a summary of how much rankings move.

Run with: python -m src.module1_scoring.sensitivity
"""

from pathlib import Path
import pandas as pd
import numpy as np

from src.module1_scoring.config import PILLARS
from src.module1_scoring.score import (
    FEATURES_PATH,
    PROCESSED_DIR,
    zscore_signed,
    pillar_scores,
    country_score,
)

# weighting schemes: each must sum to 1.0
WEIGHT_SCHEMES = {
    'equal':            {'macro': 0.25, 'banking': 0.25, 'scale': 0.25, 'institutions': 0.25},
    'macro_tilt':       {'macro': 0.40, 'banking': 0.20, 'scale': 0.20, 'institutions': 0.20},
    'banking_tilt':     {'macro': 0.20, 'banking': 0.40, 'scale': 0.20, 'institutions': 0.20},
    'institutions_tilt':{'macro': 0.20, 'banking': 0.20, 'scale': 0.20, 'institutions': 0.40},
}

COVERAGE_THRESHOLDS = [0.33, 0.50, 0.66]


def weighted_country_score(pillar_df, features, weights, min_pillars=3):
    """Same logic as country_score in score.py but with custom pillar weights."""
    pillar_cols = [f'pillar_{p}' for p in PILLARS]
    out = pillar_df.copy()

    # weighted mean ignoring NaN pillars: renormalise weights over available pillars
    def row_weighted_mean(row):
        vals = np.array([row[c] for c in pillar_cols], dtype=float)
        w = np.array([weights[p] for p in PILLARS], dtype=float)
        mask = ~np.isnan(vals)
        if mask.sum() < min_pillars:
            return np.nan
        return np.sum(vals[mask] * w[mask]) / np.sum(w[mask])

    out['country_score'] = out.apply(row_weighted_mean, axis=1)
    out['rank'] = out['country_score'].rank(ascending=False, method='min')
    return out[['country', 'country_score', 'rank']]


def run_scenario(features, coverage_threshold, weights):
    """Run the full scoring pipeline under one set of assumptions."""
    z = zscore_signed(features)
    pillars = pillar_scores(z, min_coverage=coverage_threshold)
    scored = weighted_country_score(pillars, features, weights)
    return scored


def kendall_tau(rank_a, rank_b):
    """Kendall tau correlation between two ranking series (NaN-tolerant)."""
    df = pd.DataFrame({'a': rank_a, 'b': rank_b}).dropna()
    return df['a'].corr(df['b'], method='kendall')


if __name__ == '__main__':
    features = pd.read_csv(FEATURES_PATH)
    print(f'Sensitivity analysis: {len(features)} countries, '
          f'{len(COVERAGE_THRESHOLDS)} coverage thresholds x '
          f'{len(WEIGHT_SCHEMES)} weighting schemes')

    # baseline for comparison: equal weights, 50% threshold (matches main score.py)
    baseline = run_scenario(features, 0.50, WEIGHT_SCHEMES['equal'])
    baseline_rank = baseline.set_index('country')['rank']

    # build a wide table: one column per scenario, values are ranks
    scenarios = {}
    for threshold in COVERAGE_THRESHOLDS:
        for scheme, weights in WEIGHT_SCHEMES.items():
            label = f'thr{int(threshold * 100)}_{scheme}'
            df = run_scenario(features, threshold, weights)
            scenarios[label] = df.set_index('country')['rank']

    wide = pd.DataFrame(scenarios)
    wide = wide.merge(baseline_rank.rename('baseline'), left_index=True, right_index=True)
    wide = wide.sort_values('baseline')
    wide = wide.reset_index()

    out_path = PROCESSED_DIR / 'sensitivity_rankings.csv'
    wide.to_csv(out_path, index=False)

    # how much does the top 10 change?
    baseline_top10 = set(baseline.nsmallest(10, 'rank')['country'])
    print(f'\nBaseline top 10: {sorted(baseline_top10)}')

    print(f'\n=== Top 10 stability across scenarios ===')
    for label in scenarios:
        scenario_top10 = set(
            scenarios[label].sort_values().head(10).index
        )
        in_common = baseline_top10 & scenario_top10
        new_entries = scenario_top10 - baseline_top10
        dropped = baseline_top10 - scenario_top10
        tau = kendall_tau(baseline_rank, scenarios[label])
        print(f'  {label:30s}  overlap={len(in_common):2d}/10  '
              f'tau={tau:.3f}  new={sorted(new_entries)}  out={sorted(dropped)}')

    print(f'\nSaved to {out_path}')