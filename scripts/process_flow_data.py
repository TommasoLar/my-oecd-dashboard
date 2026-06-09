#!/usr/bin/env python3
"""
Process OECD private philanthropy CSV into clean JSON for the React flow-map app.
Filters regional/unspecified entries, aggregates flows, adds coordinates.
"""
import csv, json, math, re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ── Coordinates (lat, lon) for all countries in the dataset ─────────────────
COORDS = {
    'Afghanistan': (33.9, 67.7), 'Albania': (41.2, 20.2), 'Algeria': (28.0, 1.7),
    'Angola': (-11.2, 17.9), 'Argentina': (-38.4, -63.6), 'Armenia': (40.1, 45.0),
    'Azerbaijan': (40.1, 47.6), 'Bangladesh': (23.7, 90.4), 'Belarus': (53.7, 28.0),
    'Belize': (17.2, -88.5), 'Benin': (9.3, 2.3), 'Bhutan': (27.5, 90.4),
    'Bolivia': (-16.3, -63.6), 'Bolivia (Plurinational State of)': (-16.3, -63.6),
    'Bosnia and Herzegovina': (43.9, 17.7), 'Botswana': (-22.3, 24.7),
    'Brazil': (-14.2, -51.9), 'Burkina Faso': (12.4, -1.6), 'Burundi': (-3.4, 29.9),
    'Cambodia': (12.6, 104.9), 'Cameroon': (5.7, 12.4), 'Canada': (56.1, -106.3),
    'Central African Republic': (6.6, 20.9), 'Chad': (15.5, 18.7),
    'Chile': (-35.7, -71.5), "China (People's Republic of)": (35.0, 103.0),
    'China': (35.0, 103.0), 'Colombia': (4.6, -74.1), 'Congo': (-0.2, 15.8),
    'Costa Rica': (9.7, -83.8), "Côte d'Ivoire": (7.5, -5.5), 'Cuba': (21.5, -79.5),
    'Democratic Republic of the Congo': (-4.0, 21.8), 'Djibouti': (11.8, 42.6),
    'Dominican Republic': (18.7, -70.2), 'Ecuador': (-1.8, -78.2),
    'Egypt': (26.8, 30.8), 'El Salvador': (13.8, -88.9), 'Eritrea': (15.2, 39.8),
    'Ethiopia': (8.6, 38.7), 'Gambia': (13.4, -15.3), 'Georgia': (42.3, 43.4),
    'Ghana': (7.9, -1.0), 'Guatemala': (15.8, -90.2), 'Guinea': (11.0, -10.9),
    'Guinea-Bissau': (11.8, -15.2), 'Haiti': (18.9, -72.3), 'Honduras': (15.2, -86.2),
    'India': (20.6, 78.9), 'Indonesia': (-0.8, 113.9), 'Iraq': (33.2, 43.7),
    'Jordan': (30.6, 36.2), 'Kazakhstan': (48.0, 68.0), 'Kenya': (-0.0, 37.9),
    'Kosovo': (42.6, 20.9), 'Kyrgyzstan': (41.2, 74.8), 'Lao PDR': (19.9, 102.5),
    'Lebanon': (33.9, 35.9), 'Lesotho': (-29.6, 28.2), 'Liberia': (6.4, -9.4),
    'Libya': (26.3, 17.2), 'Madagascar': (-18.8, 46.9), 'Malawi': (-13.3, 34.3),
    'Malaysia': (4.2, 108.0), 'Mali': (17.6, -2.0), 'Mauritania': (21.0, -10.9),
    'Mexico': (23.6, -102.6), 'Moldova': (47.4, 28.4), 'Mongolia': (46.9, 103.8),
    'Morocco': (31.8, -7.1), 'Mozambique': (-18.7, 35.5), 'Myanmar': (21.9, 95.9),
    'Namibia': (-22.9, 18.5), 'Nepal': (28.4, 84.1), 'Nicaragua': (12.9, -85.2),
    'Niger': (17.6, 8.1), 'Nigeria': (9.1, 8.7), 'Pakistan': (30.4, 69.3),
    'Panama': (8.5, -80.8), 'Papua New Guinea': (-6.3, 143.9),
    'Paraguay': (-23.4, -58.4), 'Peru': (-9.2, -75.0), 'Philippines': (12.9, 121.8),
    'Rwanda': (-1.9, 29.9), 'Senegal': (14.5, -14.5), 'Sierra Leone': (8.5, -11.8),
    'Somalia': (5.2, 46.2), 'South Africa': (-30.6, 22.9), 'South Sudan': (4.9, 31.3),
    'Sri Lanka': (7.9, 80.8), 'Sudan': (12.9, 30.2), 'Tajikistan': (38.9, 71.3),
    'Tanzania': (-6.4, 34.9), 'Thailand': (15.9, 100.9), 'Timor-Leste': (-8.9, 125.7),
    'Togo': (8.6, 0.8), 'Tunisia': (33.9, 9.5), 'Türkiye': (38.9, 35.2),
    'Turkey': (38.9, 35.2), 'Uganda': (1.4, 32.3), 'Ukraine': (48.4, 31.2),
    'Uzbekistan': (41.4, 64.6), 'Venezuela': (6.4, -66.6), 'Vietnam': (14.1, 108.3),
    'West Bank and Gaza Strip': (31.9, 35.2), 'Yemen': (15.6, 48.5),
    'Zambia': (-13.1, 27.9), 'Zimbabwe': (-19.0, 29.2),
    'Eswatini': (-26.5, 31.5), 'Libyan Arab Jamahiriya': (26.3, 17.2),
    'Syrian Arab Republic': (34.8, 38.9), 'Comoros': (-11.6, 43.3),
    'Myanmar/Burma': (21.9, 95.9),
    'Viet Nam': (14.1, 108.3), "Lao People's Democratic Republic": (19.9, 102.5),
    'Iran': (32.4, 53.7), "Iran (Islamic Republic of)": (32.4, 53.7),
    'Serbia': (44.0, 21.0), 'Fiji': (-17.7, 178.1), 'Cabo Verde': (15.1, -23.6),
    'Guyana': (4.9, -58.9), 'Montenegro': (42.7, 19.4), 'Jamaica': (18.1, -77.3),
    'North Macedonia': (41.6, 21.7), 'Vanuatu': (-15.4, 166.9),
    'Maldives': (1.9, 73.5), 'Samoa': (-13.8, -172.1), 'Turkmenistan': (38.9, 59.6),
    'Sao Tome and Principe': (0.2, 6.6), 'Saint Lucia': (13.9, -60.9),
    'Suriname': (3.9, -56.0), 'Equatorial Guinea': (1.7, 10.3),
    'Solomon Islands': (-9.6, 160.2), "Democratic People's Republic of Korea": (40.3, 127.5),
    'Marshall Islands': (7.1, 171.2), 'Dominica': (15.4, -61.4),
    'Kiribati': (-3.4, -168.7), 'Grenada': (12.1, -61.7),
    'Tonga': (-21.2, -175.2), 'Saint Vincent and the Grenadines': (13.3, -61.2),
    'Montserrat': (16.7, -62.2), 'Palau': (7.5, 134.6),
    'Saint Helena': (-15.9, -5.7), 'Mauritius': (-20.3, 57.6),
    'Gabon': (-0.8, 11.6),
    # Donor countries
    'Australia': (-25.3, 133.8), 'Austria': (47.5, 14.6), 'Belgium': (50.5, 4.5),
    'Denmark': (56.3, 9.5), 'Finland': (61.9, 25.7), 'France': (46.2, 2.2),
    'Germany': (51.2, 10.5), 'Ireland': (53.1, -8.2), 'Italy': (41.9, 12.6),
    'Japan': (36.2, 138.3), 'Kuwait': (29.3, 47.5), 'Luxembourg': (49.8, 6.1),
    'Netherlands': (52.3, 5.3), 'New Zealand': (-40.9, 174.9), 'Norway': (60.5, 8.5),
    'Portugal': (39.4, -8.2), 'Qatar': (25.4, 51.2), 'South Korea': (35.9, 127.8),
    'Spain': (40.5, -3.7), 'Sweden': (60.1, 18.6), 'Switzerland': (47.0, 8.2),
    'United Arab Emirates': (23.4, 53.8), 'United Kingdom': (55.4, -3.4),
    'United States': (37.1, -95.7),
}

# Normalize donor country names to display names
DONOR_NORMALIZE = {
    "China (People's Republic of)": "China",
    "Turkey": "Türkiye",
}

# ── Filters for regional / unspecified entries ───────────────────────────────
REGIONAL_PATTERNS = [
    r'regional', r'unspecified', r'bilateral', r'multilateral', r'\bglobal\b',
    r'states ex\.', r'far east asia', r'south & central', r'sub-saharan',
    r'middle east', r'north & central', r'southern africa', r'west africa',
    r'east africa', r'north africa', r'caribbean', r'oceania', r'central asia',
    r'central america', r'developing countr', r'south of sahara', r'middle africa',
    r'north of sahara', r'micronesia', r'europe, regional',
]
REGIONAL_RE = re.compile('|'.join(REGIONAL_PATTERNS), re.IGNORECASE)

# Multi-country rows (semicolon-separated countries)
def is_multi_country(name):
    return ';' in str(name)

def is_regional(name):
    n = str(name or '')
    if is_multi_country(n):
        return True
    return bool(REGIONAL_RE.search(n))

# Clean sector names
SECTOR_CLEAN = {
    'Population Policies/Programmes & Reproductive Health': 'Reproductive Health',
    'Agriculture, Forestry, Fishing': 'Agriculture',
    'Banking & Financial Services': 'Financial Services',
    'Government & Civil Society': 'Gov & Civil Society',
    'General Environment Protection': 'Environment',
    'Other Social Infrastructure & Services': 'Social Services',
    'Other Multisector': 'Other',
    'Unallocated / Unspecified': 'Unspecified',
    'Disaster Prevention & Preparedness': 'Disaster Prep',
    'Reconstruction Relief & Rehabilitation': 'Reconstruction',
    'Development Food Assistance': 'Food Aid',
    'Action Relating to Debt': 'Debt Relief',
    'Administrative Costs of Donors': 'Admin',
    'Industry, Mining, Construction': 'Industry',
    'Other Commodity Assistance': 'Commodity Aid',
    'Refugees in Donor Countries': 'Refugees',
    'Trade Policies & Regulations': 'Trade Policy',
    'Business & Other Services': 'Business Services',
}

def clean_sector(s):
    s = str(s or '').strip()
    if ';' in s:
        return 'Other'
    return SECTOR_CLEAN.get(s, s) if s else 'Unspecified'

def to_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0

def fmt(millions):
    v = float(millions or 0)
    if v >= 1000:
        return f'${v/1000:.1f}B'
    if v >= 1:
        return f'${v:.1f}M'
    return f'${v*1000:.0f}K'

def clean_text(v):
    return re.sub(r'\s+', ' ', str(v or '').strip())

def fallback_project_title(r):
    title = clean_text(r.get('grant_recipient_project_title'))
    if len(title) >= 6:
        return title

    desc = clean_text(r.get('project_description'))
    if len(desc) >= 6:
        return desc[:90].rstrip(' ,.;:-')

    subsector = clean_text(r.get('subsector_description'))
    country = clean_text(r.get('country'))
    if subsector and country:
        return f'{subsector} in {country}'
    if subsector:
        return subsector

    sector = clean_sector(r.get('sector_description'))
    return f'{sector} funding in {country}' if country else f'{sector} funding'

# ── Load CSV ─────────────────────────────────────────────────────────────────
csv_path = ROOT / 'data' / 'OECD Dataset.xlsx - complete_p4d3_df.csv'
with open(csv_path, encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print(f'Total rows: {len(rows)}')

# ── Filter ───────────────────────────────────────────────────────────────────
clean_rows = []
skipped = 0
for r in rows:
    country = str(r.get('country') or '').strip()
    donor = str(r.get('Donor_country') or '').strip()
    amount = to_float(r.get('usd_disbursements_defl'))
    year = str(r.get('year') or '').strip()

    if is_regional(country):
        skipped += 1
        continue
    if not donor or not country or not year:
        skipped += 1
        continue
    if amount <= 0:
        skipped += 1
        continue

    # Handle year ranges like "2020-2023" → use first year
    year_clean = str(year).split('-')[0].strip()
    try:
        year_int = int(year_clean)
    except ValueError:
        skipped += 1
        continue

    # Normalize donor name
    donor = DONOR_NORMALIZE.get(donor, donor)
    sector = clean_sector(r.get('sector_description'))

    clean_rows.append({
        'donorCountry': donor,
        'country': country,
        'sector': sector,
        'year': year_int,
        'amount': amount,
        'regionMacro': str(r.get('region_macro') or '').strip(),
        'region': str(r.get('region') or '').strip(),
    })

print(f'After cleaning: {len(clean_rows)} rows (dropped {skipped})')

# ── Aggregate records (donor → recipient × sector × year) ───────────────────
record_agg = defaultdict(float)
for r in clean_rows:
    key = (r['donorCountry'], r['country'], r['sector'], r['year'])
    record_agg[key] += r['amount']

records = [
    {'donorCountry': k[0], 'country': k[1], 'sector': k[2], 'year': k[3], 'amount': round(v, 6)}
    for k, v in record_agg.items()
]
records.sort(key=lambda x: -x['amount'])
print(f'Aggregated records: {len(records)}')

# ── Recipient country aggregates ─────────────────────────────────────────────
recipient_total = defaultdict(float)
recipient_meta = {}
for r in clean_rows:
    c = r['country']
    recipient_total[c] += r['amount']
    if c not in recipient_meta:
        recipient_meta[c] = {'region': r['region'], 'regionMacro': r['regionMacro']}

# Per-recipient: top donors, top sectors, year trend
rec_donors = defaultdict(lambda: defaultdict(float))
rec_sectors = defaultdict(lambda: defaultdict(float))
rec_years = defaultdict(lambda: defaultdict(float))
for r in clean_rows:
    c = r['country']
    rec_donors[c][r['donorCountry']] += r['amount']
    rec_sectors[c][r['sector']] += r['amount']
    rec_years[c][r['year']] += r['amount']

all_years = sorted({r['year'] for r in clean_rows})

recipients = []
for country, total in sorted(recipient_total.items(), key=lambda x: -x[1]):
    coords = COORDS.get(country)
    if not coords:
        print(f'  [WARN] No coords for recipient: {country}')
        continue
    meta = recipient_meta.get(country, {})
    top_donors = sorted(
        [{'donorCountry': k, 'amount': round(v, 4)} for k, v in rec_donors[country].items()],
        key=lambda x: -x['amount']
    )[:10]
    top_sectors = sorted(
        [{'sector': k, 'amount': round(v, 4)} for k, v in rec_sectors[country].items()],
        key=lambda x: -x['amount']
    )[:8]
    year_trend = [
        {'year': yr, 'amount': round(rec_years[country].get(yr, 0), 4)}
        for yr in all_years
    ]
    recipients.append({
        'country': country,
        'lat': coords[0],
        'lon': coords[1],
        'region': meta.get('region', ''),
        'regionMacro': meta.get('regionMacro', ''),
        'total': round(total, 4),
        'topDonors': top_donors,
        'topSectors': top_sectors,
        'yearTrend': year_trend,
    })

# Assign rank
for i, rec in enumerate(recipients, 1):
    rec['rank'] = i

# ── Donor country aggregates ─────────────────────────────────────────────────
donor_total = defaultdict(float)
for r in clean_rows:
    donor_total[r['donorCountry']] += r['amount']

donor_countries = []
for country, total in sorted(donor_total.items(), key=lambda x: -x[1]):
    coords = COORDS.get(country)
    if not coords:
        print(f'  [WARN] No coords for donor: {country}')
        continue
    donor_countries.append({
        'country': country,
        'lat': coords[0],
        'lon': coords[1],
        'total': round(total, 4),
    })

# ── Sector list ──────────────────────────────────────────────────────────────
sector_totals = defaultdict(float)
for r in clean_rows:
    sector_totals[r['sector']] += r['amount']
sector_names = sorted(s for s in sector_totals if s and s != 'Other')
sectors_list = ['All'] + sector_names + (['Other'] if 'Other' in sector_totals else [])

# ── OECD Projects (deduplicated by row_id) ────────────────────────────────────
# Group by row_id; for each unique grant keep the row with max amount.
proj_by_id = defaultdict(list)
for r in rows:
    rid = str(r.get('row_id') or '').strip()
    if not rid:
        continue
    country = str(r.get('country') or '').strip()
    if is_regional(country):
        continue
    amt = to_float(r.get('usd_disbursements_defl'))
    if amt <= 0:
        continue
    proj_by_id[rid].append(r)

projects_raw = []
for rid, rrows in proj_by_id.items():
    best = max(rrows, key=lambda x: to_float(x.get('usd_disbursements_defl')))
    year_str = str(best.get('year') or '').split('-')[0].strip()
    try:
        yr = int(year_str)
    except ValueError:
        continue
    donor = DONOR_NORMALIZE.get(str(best.get('Donor_country') or '').strip(),
                                 str(best.get('Donor_country') or '').strip())
    sector_raw = str(best.get('sector_description') or '').strip()
    subsector  = str(best.get('subsector_description') or '').strip()
    projects_raw.append({
        'id':          rid,
        'title':       fallback_project_title(best),
        'description': clean_text(best.get('project_description'))[:400],
        'org':         str(best.get('organization_name') or '').strip(),
        'donorCountry': donor,
        'country':     str(best.get('country') or '').strip(),
        'region':      str(best.get('region') or '').strip(),
        'regionMacro': str(best.get('region_macro') or '').strip(),
        'sector':      clean_sector(sector_raw),
        'subsector':   subsector[:80] if subsector else '',
        'amount':      round(to_float(best.get('usd_disbursements_defl')), 4),
        'year':        yr,
        'duration':    str(best.get('expected_duration') or '').strip(),
        'flowType':    str(best.get('type_of_flow') or '').strip(),
    })

projects_raw.sort(key=lambda x: -x['amount'])
print(f'OECD projects: {len(projects_raw)}, first="{projects_raw[0]["title"][:60]}"')

# ── Gates Foundation specific aggregations ───────────────────────────────────
gates_rows = [r for r in rows if str(r.get('organization_name') or '').strip() == 'Gates Foundation']
print(f'Gates Foundation rows: {len(gates_rows)}')

gates_year   = defaultdict(float)
gates_sector = defaultdict(float)
gates_country= defaultdict(float)
gates_region = defaultdict(float)

for r in gates_rows:
    yr_str = str(r.get('year') or '').split('-')[0].strip()
    try:
        yr = int(yr_str)
    except ValueError:
        continue
    amt = to_float(r.get('usd_disbursements_defl'))
    if amt <= 0:
        continue
    country = str(r.get('country') or '').strip()
    sector_raw = str(r.get('sector_description') or '').strip()
    region_mac = str(r.get('region_macro') or '').strip()

    gates_year[yr] += amt
    gates_sector[clean_sector(sector_raw)] += amt
    if not is_regional(country):
        gates_country[country] += amt
    if region_mac and not is_regional(region_mac):
        gates_region[region_mac] += amt

gates_total = sum(gates_year.values())
gates_year_trend = [{'year': yr, 'amount': round(gates_year.get(yr, 0), 4)} for yr in all_years]
gates_by_sector  = sorted([{'sector': k, 'amount': round(v, 4)} for k, v in gates_sector.items() if k not in ('Unspecified','Other','Admin')], key=lambda x: -x['amount'])
gates_by_country = sorted([{'country': k, 'amount': round(v, 4)} for k, v in gates_country.items()], key=lambda x: -x['amount'])[:12]
gates_by_region  = sorted([{'region': k, 'amount': round(v, 4)} for k, v in gates_region.items()], key=lambda x: -x['amount'])

# Gates-specific deduplicated projects
gates_proj_by_id = defaultdict(list)
for r in gates_rows:
    rid = str(r.get('row_id') or '').strip()
    if not rid:
        continue
    country = str(r.get('country') or '').strip()
    if is_regional(country):
        continue
    if to_float(r.get('usd_disbursements_defl')) <= 0:
        continue
    gates_proj_by_id[rid].append(r)

gates_projects = []
for rid, rrows in gates_proj_by_id.items():
    best = max(rrows, key=lambda x: to_float(x.get('usd_disbursements_defl')))
    yr_str = str(best.get('year') or '').split('-')[0].strip()
    try:
        yr = int(yr_str)
    except ValueError:
        continue
    sector_raw = str(best.get('sector_description') or '').strip()
    gates_projects.append({
        'id':          str(best.get('row_id') or '').strip(),
        'title':       fallback_project_title(best),
        'description': clean_text(best.get('project_description'))[:400],
        'org':         'Gates Foundation',
        'donorCountry':'United States',
        'country':     str(best.get('country') or '').strip(),
        'region':      str(best.get('region') or '').strip(),
        'regionMacro': str(best.get('region_macro') or '').strip(),
        'sector':      clean_sector(sector_raw),
        'subsector':   str(best.get('subsector_description') or '').strip()[:80],
        'amount':      round(to_float(best.get('usd_disbursements_defl')), 4),
        'year':        yr,
        'duration':    str(best.get('expected_duration') or '').strip(),
    })
gates_projects.sort(key=lambda x: -x['amount'])
print(f'Gates projects: {len(gates_projects)}, total: {fmt(gates_total)}')

# ── Org-by-country-sector aggregation (for simulator org lists) ───────────────
org_by_cs = defaultdict(lambda: defaultdict(float))
for r in rows:
    country = str(r.get('country') or '').strip()
    if is_regional(country):
        continue
    yr_str = str(r.get('year') or '').split('-')[0].strip()
    try:
        int(yr_str)
    except ValueError:
        continue
    sector_raw = str(r.get('sector_description') or '').strip()
    sector = clean_sector(sector_raw)
    org = str(r.get('organization_name') or '').strip()
    amt = to_float(r.get('usd_disbursements_defl'))
    if not org or amt <= 0:
        continue
    org_by_cs[(country, sector)][org] += amt

orgs_by_cs_out = {}
for (country, sector), orgs in org_by_cs.items():
    key = f"{country}|||{sector}"
    orgs_by_cs_out[key] = sorted(
        [{'org': o, 'amount': round(a, 4)} for o, a in orgs.items()],
        key=lambda x: -x['amount']
    )[:5]
print(f'orgsByCS entries: {len(orgs_by_cs_out)}')

# ── Global metrics ────────────────────────────────────────────────────────────
source_rows = [r for r in rows if to_float(r.get('usd_disbursements_defl')) > 0]
source_total_funding = sum(to_float(r.get('usd_disbursements_defl')) for r in source_rows)
source_recipients = {
    str(r.get('country') or '').strip()
    for r in source_rows
    if str(r.get('country') or '').strip()
}
source_donors = {
    str(r.get('Donor_country') or '').strip()
    for r in source_rows
    if str(r.get('Donor_country') or '').strip()
}
source_by_year = defaultdict(lambda: {
    'totalFunding': 0.0,
    'recipientSet': set(),
    'donorSet': set(),
    'recordCount': 0,
})
for r in source_rows:
    yr_str = str(r.get('year') or '').split('-')[0].strip()
    try:
        yr = int(yr_str)
    except ValueError:
        continue

    country = str(r.get('country') or '').strip()
    donor = str(r.get('Donor_country') or '').strip()
    metric = source_by_year[yr]
    metric['totalFunding'] += to_float(r.get('usd_disbursements_defl'))
    metric['recordCount'] += 1
    if country:
        metric['recipientSet'].add(country)
    if donor:
        metric['donorSet'].add(donor)

source_metrics_by_year = {
    str(yr): {
        'totalFunding': round(metric['totalFunding'], 2),
        'totalFundingLabel': fmt(metric['totalFunding']),
        'recipientCount': len(metric['recipientSet']),
        'donorCount': len(metric['donorSet']),
        'recordCount': metric['recordCount'],
    }
    for yr, metric in sorted(source_by_year.items())
}
mapped_total_funding = sum(r['amount'] for r in clean_rows)

output = {
    'metrics': {
        'totalFunding': round(source_total_funding, 2),
        'totalFundingLabel': fmt(source_total_funding),
        'recipientCount': len(source_recipients),
        'donorCount': len(source_donors),
        'recordCount': len(source_rows),
        'mappedTotalFunding': round(mapped_total_funding, 2),
        'mappedTotalFundingLabel': fmt(mapped_total_funding),
        'mappedRecipientCount': len(recipients),
        'mappedDonorCount': len(donor_countries),
        'mappedRecordCount': len(clean_rows),
        'projectCount': len(projects_raw),
    },
    'metricsByYear': source_metrics_by_year,
    'years': all_years,
    'sectors': sectors_list,
    'recipients': recipients,
    'donorCountries': donor_countries,
    'records': records,
    'orgsByCS': orgs_by_cs_out,
    'gatesFunding': {
        'org': 'Gates Foundation',
        'total': round(gates_total, 2),
        'totalLabel': fmt(gates_total),
        'yearTrend': gates_year_trend,
        'bySector':  gates_by_sector,
        'byCountry': gates_by_country,
        'byRegion':  gates_by_region,
        'projects':  gates_projects,
    },
}

import os
public_dir = ROOT / 'flow-map' / 'public'
os.makedirs(public_dir, exist_ok=True)

out_path = public_dir / 'flow-data.json'
with open(out_path, 'w') as f:
    json.dump(output, f, separators=(',', ':'))
print(f'\nWrote {out_path} ({os.path.getsize(out_path)//1024:.0f} KB)')

projects_path = public_dir / 'projects.json'
with open(projects_path, 'w') as f:
    json.dump(projects_raw, f, separators=(',', ':'))
print(f'Wrote {projects_path} ({os.path.getsize(projects_path)//1024:.0f} KB, {len(projects_raw)} projects)')
print(f'Recipients: {len(recipients)}, Donors: {len(donor_countries)}, Records: {len(records)}')
print(f'Total funding: {fmt(source_total_funding)}')
print(f'Mapped country-level funding: {fmt(mapped_total_funding)}')
print(f'Years: {all_years}')
print(f'Sectors: {sectors_list[:8]}')
