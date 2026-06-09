# ── MAP DATASET (STRICT GEOGRAPHY FILTER) ────────────────────────────────
map_rows = []
skipped_map = 0

for r in core_rows:
    country = r['country']

    # only map restriction
    if is_regional(country):
        skipped_map += 1
        continue

    # also remove multi-country flows for map clarity
    if ';' in country:
        skipped_map += 1
        continue

    map_rows.append(r)

print(f'MAP rows: {len(map_rows)} (dropped {skipped_map})')