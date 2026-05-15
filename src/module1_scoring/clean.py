"""
Turn the long raw panel into a wide one-row-per-country feature table.

Logic:
  - For each level indicator: take the mean across years if we have >=3 of 5 years.
  - For inflation_vol: take the std across years if we have >=3 of 5 years.
  - Map WB codes and IIAG columns to friendly names from config.
  - No imputation here. Scoring handles missing values by averaging
    over available features per pillar.

Run with: python -m src.module1_scoring.clean
"""

from pathlib import Path
import pandas as pd
import numpy as np

from src.module1_scoring.config import (
    INDICATORS,
    IIAG_FEATURES,
    COUNTRIES,
    START_YEAR,
    END_YEAR,
)

RAW_PATH = Path(__file__).resolve().parents[2] / 'data' / 'raw' / 'panel.csv'
PROCESSED_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed'

MIN_YEARS = 3  # need at least this many observations to compute a statistic


def _wb_lookup():
    """Build a map from WB code to list of (friendly_name, pillar, direction, agg).
    A code maps to a list because the same code can produce multiple features
    (e.g. inflation level and inflation_vol both come from FP.CPI.TOTL.ZG)."""
    out = {}
    for code, name, pillar, direction in INDICATORS:
        agg = 'std' if direction == 0 else 'mean'
        out.setdefault(code, []).append((name, pillar, direction, agg))
    return out


def _iiag_lookup():
    """Build a map from IIAG column name to (friendly_name, pillar, direction, agg)."""
    return {
        col: (name, pillar, direction, 'mean')
        for col, name, pillar, direction in IIAG_FEATURES
    }


def compute_features(panel):
    """
    Reduce the long panel to one row per country with all features as columns.
    """
    wb_lookup = _wb_lookup()
    iiag_lookup = _iiag_lookup()

    rows = []
    for country, group in panel.groupby('country'):
        row = {'country': country}

        for indicator, sub in group.groupby('indicator'):
            values = sub['value'].dropna()
            n = len(values)

            # WB indicator -> may produce one or more features (mean, std)
            if indicator in wb_lookup:
                for name, _pillar, _direction, agg in wb_lookup[indicator]:
                    if n < MIN_YEARS:
                        row[name] = np.nan
                    elif agg == 'mean':
                        row[name] = values.mean()
                    elif agg == 'std':
                        row[name] = values.std(ddof=1)

            # IIAG column -> always mean
            elif indicator in iiag_lookup:
                name, _pillar, _direction, _agg = iiag_lookup[indicator]
                row[name] = values.mean() if n >= MIN_YEARS else np.nan

        rows.append(row)

    return pd.DataFrame(rows).sort_values('country').reset_index(drop=True)


def coverage_report(features):
    """Per-feature: how many of 27 countries have a value."""
    n = len(features)
    report = (
        features.drop(columns='country')
        .notna()
        .sum()
        .rename('countries_with_data')
        .to_frame()
    )
    report['coverage_pct'] = (report['countries_with_data'] / n * 100).round(1)
    return report.sort_values('coverage_pct')


if __name__ == '__main__':
    print(f'Loading panel from {RAW_PATH.name}')
    panel = pd.read_csv(RAW_PATH)
    print(f'  {len(panel):,} rows, {panel["country"].nunique()} countries, '
          f'{panel["indicator"].nunique()} indicators')

    features = compute_features(panel)
    print(f'\nFeature table: {features.shape[0]} countries, '
          f'{features.shape[1] - 1} features')

    print('\n=== Coverage by feature ===')
    print(coverage_report(features).to_string())

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / 'features.csv'
    features.to_csv(out_path, index=False)
    print(f'\nSaved to {out_path}')