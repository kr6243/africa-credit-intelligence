"""
Country universe, indicator definitions, and scoring config for module 1.
"""

COUNTRIES = [
    'NGA', 'GHA', 'CIV', 'SEN', 'MLI', 'BFA', 'BEN', 'TGO',
    'KEN', 'TZA', 'UGA', 'RWA', 'ETH', 'MUS',
    'ZAF', 'ZMB', 'MOZ', 'BWA', 'NAM', 'AGO',
    'CMR', 'COD',
    'EGY', 'MAR', 'TUN', 'DZA',
    'CPV',
]

# ISO3 to ISO2 mapping. IIAG uses ISO2, WB uses ISO3.
ISO3_TO_ISO2 = {
    'NGA': 'NG', 'GHA': 'GH', 'CIV': 'CI', 'SEN': 'SN', 'MLI': 'ML',
    'BFA': 'BF', 'BEN': 'BJ', 'TGO': 'TG',
    'KEN': 'KE', 'TZA': 'TZ', 'UGA': 'UG', 'RWA': 'RW', 'ETH': 'ET', 'MUS': 'MU',
    'ZAF': 'ZA', 'ZMB': 'ZM', 'MOZ': 'MZ', 'BWA': 'BW', 'NAM': 'NA', 'AGO': 'AO',
    'CMR': 'CM', 'COD': 'CD',
    'EGY': 'EG', 'MAR': 'MA', 'TUN': 'TN', 'DZA': 'DZ',
    'CPV': 'CV',
}

# WB indicators only. WGI dropped (API broken). Enterprise Surveys dropped
# (coverage too thin). Pillar 4 governance now sourced from IIAG, see below.
# Each tuple: (WB code, short name, pillar, direction)
# direction: +1 means higher is better, -1 means lower is better, 0 means use volatility
INDICATORS = [
    # macro stability
    ('NY.GDP.MKTP.KD.ZG', 'gdp_growth', 'macro', 1),
    ('FP.CPI.TOTL.ZG', 'inflation', 'macro', -1),
    ('FP.CPI.TOTL.ZG', 'inflation_vol', 'macro', 0),
    ('BN.CAB.XOKA.GD.ZS', 'current_account_gdp', 'macro', 1),
    ('GC.NLD.TOTL.GD.ZS', 'fiscal_balance_gdp', 'macro', 1),
    ('FI.RES.TOTL.MO', 'reserves_months', 'macro', 1),
    # banking sector
    ('FS.AST.PRVT.GD.ZS', 'private_credit_gdp', 'banking', 1),
    ('FB.AST.NPER.ZS', 'npl_ratio', 'banking', -1),
    ('FB.BNK.CAPA.ZS', 'bank_capital_assets', 'banking', 1),
    ('FR.INR.LNDP', 'interest_spread', 'banking', -1),
    # market scale (replaces SME pillar for v1, Enterprise Survey coverage was insufficient)
    ('NY.GDP.PCAP.PP.KD', 'gdp_per_capita_ppp', 'scale', 1),
    ('NY.GDP.MKTP.CD', 'gdp_usd', 'scale', 1),
    ('SP.POP.TOTL', 'population', 'scale', 1),
]

# IIAG composite-score columns we use for pillar 4. Columns come from the
# IIAG composite scores CSV. Direction is +1 for all (IIAG scores: higher = better).
IIAG_FEATURES = [
    ('SECURITY & RULE OF LAW', 'iiag_security_rol', 'institutions', 1),
    ('PARTICIPATION, RIGHTS & INCLUSION', 'iiag_participation_rights', 'institutions', 1),
]

START_YEAR = 2019
END_YEAR = 2023
PILLARS = ['macro', 'banking', 'scale', 'institutions']

# Sector overlays (v1: simple add-on, not in main country score)
SECTOR_INDICATORS = {
    'healthcare': ['SH.XPD.CHEX.GD.ZS', 'SH.XPD.OOPC.CH.ZS', 'SH.MED.BEDS.ZS'],
    'consumer': ['NY.GDP.PCAP.PP.KD', 'SP.URB.TOTL.IN.ZS', 'SP.URB.GROW'],
    'agribusiness': ['NV.AGR.TOTL.ZS', 'AG.LND.AGRI.K2', 'TX.VAL.AGRI.ZS.UN', 'AG.YLD.CREL.KG'],
    'education': ['SE.XPD.TOTL.GD.ZS', 'SE.TER.ENRR', 'SE.ADT.LITR.ZS'],
}