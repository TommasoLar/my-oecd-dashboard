# ── CORE CLEANING (NO geographic filtering) ────────────────────────────────
core_rows = []
skipped_core = 0

for r in rows:
    country = str(r.get('country') or '').strip()
    donor = str(r.get('Donor_country') or '').strip()
    amount = to_float(r.get('usd_disbursements_defl'))
    year = str(r.get('year') or '').strip()

    # CORE RULES (keep EVERYTHING except broken rows)
    if not donor or not country or not year:
        skipped_core += 1
        continue
    if amount <= 0:
        skipped_core += 1
        continue

    year_clean = str(year).split('-')[0].strip()
    try:
        year_int = int(year_clean)
    except ValueError:
        skipped_core += 1
        continue

    donor = DONOR_NORMALIZE.get(donor, donor)
    sector = clean_sector(r.get('sector_description'))

    core_rows.append({
        'donorCountry': donor,
        'country': country,
        'sector': sector,
        'year': year_int,
        'amount': amount,
        'regionMacro': str(r.get('region_macro') or '').strip(),
        'region': str(r.get('region') or '').strip(),
        'raw_country': country,   # keep original for mapping decisions
    })

print(f'CORE rows: {len(core_rows)} (dropped {skipped_core})')