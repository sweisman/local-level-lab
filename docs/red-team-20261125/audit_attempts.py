# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review audit: does the shape ordering depend on which saved fit attempt is chosen? Runs no fits."""
import collections
import csv
import sys

csv.field_size_limit(10**9)
fits = collections.defaultdict(list)
for r in csv.DictReader(open(sys.argv[1], newline='')):
    if r['cost']:
        fits[(r['segment_id'], r['case_id'])].append(r)
print('segment/case pairs', len(fits))
flip_shape = 0; flip_rot = 0; flip_zero = 0; n = 0
attempts = collections.Counter(); unconverged_used = collections.Counter()
worst = []
for key, rows in sorted(fits.items()):
    by = collections.defaultdict(list)
    for r in rows:
        by[r['model']].append(float(r['cost']))
        attempts[r['model']] += 1
    if not all(m in by for m in ('sphere_rotating', 'sphere_still', 'flat_still')):
        print('incomplete', key, {m: len(v) for m, v in by.items()}); continue
    n += 1
    rot, still, flat = by['sphere_rotating'], by['sphere_still'], by['flat_still']
    # Worst case for the globe: its highest saved cost against the disc's lowest saved cost.
    margin = min(flat)/max(min(max(rot), max(still)), 1e-300)
    worst.append((margin, key, max(rot), min(flat)))
    flip_shape += min(flat) <= max(rot)
    flip_rot += min(still) <= max(rot)
    flip_zero += (min(flat) < max(still)) != (max(flat) < min(still))
print('pairs with all three models', n)
print('saved attempts per model', dict(attempts))
print('disc lowest attempt <= rotating globe highest attempt:', flip_shape)
print('still globe lowest attempt <= rotating globe highest attempt:', flip_rot)
print('zero-field ordering (disc vs still globe) depends on attempt chosen:', flip_zero, 'of', n)
worst.sort()
print('smallest worst-case margins (disc lowest / rotating-or-still highest):')
for margin, key, a, b in worst[:6]:
    print(f'  {key[0][:10]} {key[1]:24s} margin {margin:9.3g} globe-high {a:9.4g} disc-low {b:9.4g}')
roles = collections.Counter((r['role'], r['converged'], r['stop_reason']) for rows in fits.values() for r in rows)
print('role/converged/stop:', {k: v for k, v in sorted(roles.items())})
