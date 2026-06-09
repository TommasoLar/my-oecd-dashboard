#!/usr/bin/env python3
"""
Process OECD private philanthropy CSV into clean JSON for the React flow-map app.
Filters regional/unspecified entries, aggregates flows, adds coordinates.
"""
import csv, json, math, re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# Normalize donor country names to display names
DONOR_NORMALIZE = {
    "China (People's Republic of)": "China",
    "Turkey": "Türkiye",
}


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

# ── Load CSV ───────────────────────────────────────────────────────────────── #to change to new source
csv_path = ROOT / 'data' / 'OECD Dataset.xlsx - complete_p4d3_df.csv'
with open(csv_path, encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print(f'Total rows: {len(rows)}')

# ── Filter ─────────────────────────────────────────────────────────────────── (for the map is fine excluding regional basket, however for everything else the flows need to be included)
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
    #here i will need to justt delete those that have aggregate years for the map as they cannot be used for this visualization (the foundations asked to remain in aggregate format, so only way that they can be included is through KPI total, KPi total foundations and in the lsit of donors)
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

# ── Sector list ────────────────────────────────────────────────────────────── (check if code still works, we do not want to simplify the name of the sectors so i deleted above the sector renames)
sector_totals = defaultdict(float)
for r in clean_rows:
    sector_totals[r['sector']] += r['amount']
sector_names = sorted(s for s in sector_totals if s and s != 'Other')
sectors_list = ['All'] + sector_names + (['Other'] if 'Other' in sector_totals else [])

# ── OECD Projects (deduplicated by row_id) ────────────────────────────────────
# Group by row_id; for each unique grant keep the row with max amount. (we need it to have not deduplicated as multiple row_ids are not duplicates, but they define projects that have been split into more than one sector code and the total divided so no double counting. only makes sense if we want to count original grants n' but not the case)
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

# ── Gates Foundation specific aggregations ─────────────────────────────────── (not sure what is the purpose of this individual aggregation)
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

# Gates-specific deduplicated projects (not sure specific purpose)
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
