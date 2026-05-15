"""
Loads processed data files once at import time so every page can use them
without re-reading from disk.
"""

from pathlib import Path
import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[1] / 'data' / 'processed'

COUNTRY_SCORES = pd.read_csv(PROCESSED_DIR / 'country_scores.csv')
SECTOR_SCORES = pd.read_csv(PROCESSED_DIR / 'sector_scores.csv')
FEATURES = pd.read_csv(PROCESSED_DIR / 'features.csv')
SENSITIVITY = pd.read_csv(PROCESSED_DIR / 'sensitivity_rankings.csv')

# Friendly country names for display (ISO3 codes are not user-friendly).
COUNTRY_NAMES = {
    'NGA': 'Nigeria', 'GHA': 'Ghana', 'CIV': 'Cote d\'Ivoire', 'SEN': 'Senegal',
    'MLI': 'Mali', 'BFA': 'Burkina Faso', 'BEN': 'Benin', 'TGO': 'Togo',
    'KEN': 'Kenya', 'TZA': 'Tanzania', 'UGA': 'Uganda', 'RWA': 'Rwanda',
    'ETH': 'Ethiopia', 'MUS': 'Mauritius',
    'ZAF': 'South Africa', 'ZMB': 'Zambia', 'MOZ': 'Mozambique',
    'BWA': 'Botswana', 'NAM': 'Namibia', 'AGO': 'Angola',
    'CMR': 'Cameroon', 'COD': 'DR Congo',
    'EGY': 'Egypt', 'MAR': 'Morocco', 'TUN': 'Tunisia', 'DZA': 'Algeria',
    'CPV': 'Cabo Verde',
}

# TLG portfolio markets (approximate, based on public information). Used to
# highlight TLG-relevant countries in the dashboard.
TLG_FOOTPRINT = {
    'NGA', 'GHA', 'KEN', 'UGA', 'TZA', 'RWA', 'EGY', 'ZAF', 'MUS', 'CIV', 'SEN',
}


def country_label(iso3):
    """ISO3 to display label."""
    return COUNTRY_NAMES.get(iso3, iso3)