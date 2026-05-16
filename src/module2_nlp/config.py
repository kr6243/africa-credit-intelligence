"""
Config for module 2: news sentiment monitoring via GDELT BigQuery.
"""

from datetime import date, timedelta


# ISO3 -> (display name, country phrase used in GDELT V2Locations).
# The country phrase is what appears in GDELT's structured location field.
# E.g. V2Locations entries look like '1#Kenya#KE#KE##...', so we search '#Kenya#'.
COUNTRIES = {
    'NGA': ('Nigeria', 'Nigeria'),
    'GHA': ('Ghana', 'Ghana'),
    'CIV': ("Cote d'Ivoire", 'Ivory Coast'),
    'SEN': ('Senegal', 'Senegal'),
    'MLI': ('Mali', 'Mali'),
    'BFA': ('Burkina Faso', 'Burkina Faso'),
    'BEN': ('Benin', 'Benin'),
    'TGO': ('Togo', 'Togo'),
    'KEN': ('Kenya', 'Kenya'),
    'TZA': ('Tanzania', 'Tanzania'),
    'UGA': ('Uganda', 'Uganda'),
    'RWA': ('Rwanda', 'Rwanda'),
    'ETH': ('Ethiopia', 'Ethiopia'),
    'MUS': ('Mauritius', 'Mauritius'),
    'ZAF': ('South Africa', 'South Africa'),
    'ZMB': ('Zambia', 'Zambia'),
    'MOZ': ('Mozambique', 'Mozambique'),
    'BWA': ('Botswana', 'Botswana'),
    'NAM': ('Namibia', 'Namibia'),
    'AGO': ('Angola', 'Angola'),
    'CMR': ('Cameroon', 'Cameroon'),
    'COD': ('DR Congo', '#CG#'),  # use FIPS code, country name fragmented in V2Locations
    'EGY': ('Egypt', 'Egypt'),
    'MAR': ('Morocco', 'Morocco'),
    'TUN': ('Tunisia', 'Tunisia'),
    'DZA': ('Algeria', 'Algeria'),
    'CPV': ('Cabo Verde', 'Cape Verde'),
}

# GDELT theme codes for "financial relevance". Articles must match at least one.
FINANCIAL_THEMES = [
    'ECON_INFLATION',
    'ECON_MONETARY',
    'ECON_INTEREST_RATES',
    'ECON_WORLDCURRENCIES',
    'EPU_POLICY_FISCAL',
    'EPU_POLICY_MONETARY',
    'EPU_POLICY_CURRENCY',
    'FISCAL',
    'BANKING',
    'WB_BANKING_FINANCE',
]

# Time window. BigQuery has the full GDELT GKG archive; 90 days is enough
# for a current sentiment view without overrunning Claude API costs.
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=90)

# Position threshold in V2Locations. Country must appear within the first
# N characters of V2Locations for the article to count as "about" the country.
# 100 = strict, primary or secondary location only.
LOCATION_POSITION_LIMIT = 100

# Article cap per country to keep Claude API costs bounded.
MAX_ARTICLES_PER_COUNTRY = 200

# GCP project ID (must match the BigQuery project)
GCP_PROJECT = 'africa-credit-intelligence'

# Path to the service account key file (relative to project root)
GCP_KEY_PATH = 'gcp-key.json'