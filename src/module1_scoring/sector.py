"""
Sector overlay scoring.

For each TLG focus sector (healthcare, consumer, agribusiness, education),
compute a sector score per country using 3 sector-specific WB indicators.

Methodology mirrors the country score:
  - 5-year mean per indicator, requires >=3 of 5 years
  - z-score across the 27 countries
  - mean of available features per country, requires >=50% coverage
  - rank within sector

Output: data/processed/sector_scores.csv (long format: country, sector, score)

Run with: python -m src.module1_scoring.sector
"""

from pathlib import Path
import pandas as pd
import numpy as np

from src.module1_scoring.config import SECTOR_INDICATORS, START_YEAR, END_YEAR

RAW_PATH = Path(__file__).resolve().parents[2] / 'data' / 'raw' / 'panel.csv'
PROCESSED_DIR = Path(__file__).resolve().parents[2] / 'data' / 'processed'

MIN_YEARS = 3
MIN_SECTOR_COVERAGE = 0.5

# direction: all sector indicators are +1 (higher = better) except a few we flag
# below. Mapping is by WB code.
SECTOR_DIRECTIONS = {
    # healthcare
    'SH.XPD.CHEX.GD.ZS': +1,   # health spending % GDP, higher = better
    'SH.XPD.OOPC.CH.ZS': -1,   # out-of-pocket % of health spending, lower = better
    'SH.MED.BEDS.ZS':    +1,   # hospital beds per 1000, higher = better
    # consumer
    'NY.GDP.PCAP.PP.KD': +1,   # GDP per capita PPP
    'SP.URB.TOTL.IN.ZS': +1,   # urban population %
    'SP.URB.GROW':       +1,   # urban population growth
    # agribusiness: sector relevance + market size + commercialisation + productivity
    'NV.AGR.TOTL.ZS':    +1,   # agriculture % GDP (sector relevance)
    'AG.LND.AGRI.K2':    +1,   # agricultural land sq km (market size)
    'TX.VAL.AGRI.ZS.UN': +1,   # ag raw materials exports % merchandise (commercialisation)
    'AG.YLD.CREL.KG':    +1,   # cereal yield kg/hectare (productivity)
    # education
    'SE.XPD.TOTL.GD.ZS': +1,   # education spending % GDP
    'SE.TER.ENRR':       +1,   # tertiary enrolment
    'SE.ADT.LITR.ZS':    +1,   # literacy rate
}


def country_means(panel, codes, min_years=MIN_YEARS):
    """Wide df: rows=countries, cols=indicator codes, values=5yr mean (>=min_years obs)."""
    sub = panel[panel['indicator'].isin(codes)].copy()
    rows = []
    for country, g in sub.groupby('country'):
        row = {'country': country}
        for code in codes:
            vals = g[g['indicator'] == code]['value'].dropna()
            row[code] = vals.mean() if len(vals) >= min_years else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def score_sector(panel, sector_name, codes, min_coverage=MIN_SECTOR_COVERAGE):
    """
    Return a df with one row per country for this sector:
    country, sector, sector_score, rank, percentile, data_coverage.
    """
    means = country_means(panel, codes)

    # z-score each indicator, applying direction
    z = means.set_index('country').copy()
    for code in codes:
        if code not in z.columns:
            continue
        mu, sd = z[code].mean(), z[code].std(ddof=1)
        if sd == 0 or np.isnan(sd):
            z[code] = np.nan
        else:
            direction = SECTOR_DIRECTIONS.get(code, +1)
            z[code] = direction * (z[code] - mu) / sd

    # coverage = fraction of sector indicators country has data for
    coverage = z.notna().sum(axis=1) / len(codes)
    score = z.mean(axis=1, skipna=True).where(coverage >= min_coverage)

    out = pd.DataFrame({
        'country': z.index,
        'sector': sector_name,
        'sector_score': score.values,
        'data_coverage': coverage.values,
    })
    out['rank'] = out['sector_score'].rank(ascending=False, method='min').astype('Int64')
    out['percentile'] = out['sector_score'].rank(pct=True) * 100
    return out.sort_values('rank').reset_index(drop=True)


if __name__ == '__main__':
    panel = pd.read_csv(RAW_PATH)
    print(f'Loaded panel: {len(panel):,} rows, {panel["country"].nunique()} countries')

    all_sectors = []
    for sector_name, codes in SECTOR_INDICATORS.items():
        scored = score_sector(panel, sector_name, codes)
        all_sectors.append(scored)
        print(f'\n=== {sector_name.upper()} top 5 ===')
        cols = ['country', 'sector_score', 'rank', 'data_coverage']
        print(scored.head(5)[cols].round(2).to_string(index=False))

    combined = pd.concat(all_sectors, ignore_index=True)

    out_path = PROCESSED_DIR / 'sector_scores.csv'
    combined.to_csv(out_path, index=False)
    print(f'\nSaved {len(combined)} rows ({combined["sector"].nunique()} sectors × '
          f'{combined["country"].nunique()} countries) to {out_path}')