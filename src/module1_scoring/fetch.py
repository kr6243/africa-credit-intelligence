"""
Builds the raw panel for module 1. Pulls WB indicators from the WDI API and
loads IIAG composite scores from a local CSV (the WB API endpoints for WGI
and Enterprise Surveys were broken at build time, so governance is sourced
from the Mo Ibrahim Foundation's IIAG instead).

Run with: python -m src.module1_scoring.fetch
"""

from pathlib import Path
import pandas as pd
import wbgapi as wb

from src.module1_scoring.config import (
    COUNTRIES,
    INDICATORS,
    IIAG_FEATURES,
    ISO3_TO_ISO2,
    SECTOR_INDICATORS,
    START_YEAR,
    END_YEAR,
)

RAW_DIR = Path(__file__).resolve().parents[2] / 'data' / 'raw'
IIAG_PATH = RAW_DIR / '2024-IIAG-csv-files' / '2024 IIAG_Composite Scores.csv'


def unique_indicator_codes(indicators):
    seen = []
    for code, _name, _pillar, _direction in indicators:
        if code not in seen:
            seen.append(code)
    return seen


def fetch_wb(codes, countries, start_year, end_year):
    """Pull WB indicators from WDI and return long format: country, year, indicator, value."""
    wide = wb.data.DataFrame(
        codes,
        economy=countries,
        time=range(start_year, end_year + 1),
    )
    wide = wide.reset_index()
    long = wide.melt(
        id_vars=['series', 'economy'],
        var_name='year',
        value_name='value',
    )
    long['year'] = long['year'].str.replace('YR', '', regex=False).astype(int)
    long = long.rename(columns={'series': 'indicator', 'economy': 'country'})
    long['source'] = 'WB'
    return long[['country', 'year', 'indicator', 'value', 'source']]


def load_iiag(path, iiag_features, countries_iso3, start_year, end_year):
    """
    Load IIAG composite scores. Returns long format matched to our country
    universe and year window. ISO2 codes in IIAG are mapped to ISO3.
    """
    # IIAG marks missing values with '.', so na_values='.' tells pandas to read those as NaN
    df = pd.read_csv(path, na_values='.')

    # filter to our countries (IIAG uses ISO2)
    iso2_to_iso3 = {v: k for k, v in ISO3_TO_ISO2.items()}
    iso2_set = set(iso2_to_iso3.keys())
    df = df[df['Country_ISO'].isin(iso2_set)].copy()
    df['country'] = df['Country_ISO'].map(iso2_to_iso3)

    # filter to year window
    df = df[df['Year'].between(start_year, end_year)].copy()
    df = df.rename(columns={'Year': 'year'})

    # melt the IIAG category columns we care about into long format
    iiag_cols = [col for col, _name, _pillar, _direction in iiag_features]
    keep = ['country', 'year'] + iiag_cols
    df = df[keep]

    long = df.melt(id_vars=['country', 'year'], var_name='indicator', value_name='value')
    long['source'] = 'IIAG'
    return long[['country', 'year', 'indicator', 'value', 'source']]


if __name__ == '__main__':
    print(f'Fetching {len(unique_indicator_codes(INDICATORS))} WB indicators '
          f'for {len(COUNTRIES)} countries, {START_YEAR}-{END_YEAR}')

    # combine main indicators with sector overlay indicators (deduplicated)
    main_codes = unique_indicator_codes(INDICATORS)
    sector_codes = []
    for codes in SECTOR_INDICATORS.values():
        sector_codes.extend(codes)
    all_codes = list(dict.fromkeys(main_codes + sector_codes))

    wb_df = fetch_wb(all_codes, COUNTRIES, START_YEAR, END_YEAR)
    print(f'  WB: {len(wb_df):,} rows, '
          f'{wb_df["value"].isna().mean():.1%} missing')

    print(f'Loading IIAG from {IIAG_PATH.name}')
    iiag_df = load_iiag(IIAG_PATH, IIAG_FEATURES, COUNTRIES, START_YEAR, END_YEAR)
    print(f'  IIAG: {len(iiag_df):,} rows, '
          f'{iiag_df["value"].isna().mean():.1%} missing')

    panel = pd.concat([wb_df, iiag_df], ignore_index=True)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / 'panel.csv'
    panel.to_csv(out_path, index=False)

    print(f'\nSaved {len(panel):,} rows to {out_path}')
    print(f'Countries: {panel["country"].nunique()}')
    print(f'Indicators: {panel["indicator"].nunique()}')
    print(f'Overall missing: {panel["value"].isna().mean():.1%}')