# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review audit of the published 53-stretch cost table. Reads one CSV; runs no fits."""
import collections
import csv
import math
import statistics
import sys

PATH = sys.argv[1]
CASES = ('bias1_unsubtracted', 'bias1_profiled_removal')
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
rows = list(csv.DictReader(open(PATH, newline='')))
print('stretches', len(rows))


def cost(r, case, model):
    v = r[f'{case}__{model}__cost']
    return float(v) if v not in ('', 'None') else None


def bounds(r, case, model):
    v = r[f'{case}__{model}__active_bounds']
    return [x for x in v.split(';') if x]


def med(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else float('nan')


print('\n== per case/model: cost distribution, convergence, bounds, origin ==')
for case in CASES:
    for model in MODELS:
        costs = [cost(r, case, model) for r in rows]
        conv = collections.Counter(r[f'{case}__{model}__converged'] for r in rows)
        origin = collections.Counter(r[f'{case}__{model}__result_origin'] for r in rows)
        stop = collections.Counter(r[f'{case}__{model}__stop_reason'] for r in rows)
        nb = [len(bounds(r, case, model)) for r in rows]
        per_s = [c/float(r['duration_s']) for c, r in zip(costs, rows) if c is not None]
        print(f'{case:24s} {model:16s} cost min/med/max {min(c for c in costs if c is not None):.3g}/{med(costs):.3g}/{max(c for c in costs if c is not None):.3g}'
              f' | cost/s med {med(per_s):.3g} | bounds med {statistics.median(nb)} max {max(nb)}'
              f' | converged {dict(conv)} | stop {dict(stop)} | origin {dict(origin)}')

print('\n== which parameters sit on bounds (count of 53), unsubtracted case ==')
for model in MODELS:
    c = collections.Counter(b for r in rows for b in bounds(r, CASES[0], model))
    print(model, dict(c.most_common()))
print('== profiled case: earth_removal on bound ==')
for model in MODELS:
    n = sum('earth_removal' in bounds(r, CASES[1], model) for r in rows)
    print(model, n, 'of', len(rows))

print('\n== nesting: profiled cost should be <= unsubtracted (removal=0 is inside) ==')
for model in MODELS:
    worse = []; big_drop = []; same = 0
    for r in rows:
        a, b = cost(r, CASES[0], model), cost(r, CASES[1], model)
        if a is None or b is None:
            continue
        rel = (b-a)/max(a, 1e-300)
        if rel > 1e-6:
            worse.append(rel)
        elif rel < -0.01:
            big_drop.append(a/b)
        else:
            same += 1
    print(f'{model:16s} profiled worse than unsubtracted: {len(worse)} (max rel {max(worse, default=0):.3g})'
          f' | profiled lower by >1%: {len(big_drop)} (median factor {med(big_drop):.3g}, max {max(big_drop, default=0):.3g}) | equal within 1%: {same}')

print('\n== shape comparison per case: flat / best globe, and flat / still globe ==')
for case in CASES:
    ratio_best = []; ratio_still = []; ratio_rot = []; disc_beats_still = 0; disc_beats_rot = 0
    for r in rows:
        rot, still, flat = (cost(r, case, m) for m in MODELS)
        ratio_best.append(flat/min(rot, still)); ratio_still.append(flat/still); ratio_rot.append(still/rot)
        disc_beats_still += flat < still; disc_beats_rot += flat < rot
    print(f'{case:24s} flat/best-globe min {min(ratio_best):.3g} med {med(ratio_best):.3g} max {max(ratio_best):.3g}'
          f' | disc<still {disc_beats_still} | disc<rotating {disc_beats_rot}'
          f' | still/rotating min {min(ratio_rot):.3g} med {med(ratio_rot):.3g} max {max(ratio_rot):.3g}')

print('\n== weakest shape margins (flat / best globe), unsubtracted ==')
ranked = sorted(rows, key=lambda r: cost(r, CASES[0], 'flat_still')/min(cost(r, CASES[0], 'sphere_rotating'), cost(r, CASES[0], 'sphere_still')))
for r in ranked[:8]:
    rot, still, flat = (cost(r, CASES[0], m) for m in MODELS)
    print(f"{r['segment_id'][:10]} lat {float(r['mean_latitude_deg']):7.2f} course {float(r['mean_course_deg']):6.1f} dur {float(r['duration_s']):6.0f}s imu {r['imu_type']:>2s}"
          f" rot {rot:10.4g} still {still:10.4g} flat {flat:10.4g} flat/best {flat/min(rot, still):8.3g}")

print('\n== largest rotating-globe costs (absolute adequacy), unsubtracted ==')
for r in sorted(rows, key=lambda r: -cost(r, CASES[0], 'sphere_rotating'))[:8]:
    rot = cost(r, CASES[0], 'sphere_rotating')
    print(f"{r['segment_id'][:10]} lat {float(r['mean_latitude_deg']):7.2f} dur {float(r['duration_s']):6.0f}s imu {r['imu_type']:>2s} rot cost {rot:10.4g} cost/s {rot/float(r['duration_s']):.3g} bounds {len(bounds(r, CASES[0], 'sphere_rotating'))}")

print('\n== zero-field disc-favoring stretches: how pinned are those fits? ==')
for r in rows:
    still, flat = cost(r, CASES[0], 'sphere_still'), cost(r, CASES[0], 'flat_still')
    if flat < still:
        print(f"{r['segment_id'][:10]} lat {float(r['mean_latitude_deg']):7.2f} course {float(r['mean_course_deg']):6.1f} still {still:10.4g} ({len(bounds(r, CASES[0], 'sphere_still'))} bounds) flat {flat:10.4g} ({len(bounds(r, CASES[0], 'flat_still'))} bounds) rot {cost(r, CASES[0], 'sphere_rotating'):9.4g}")

print('\n== coverage ==')
lat = [float(r['mean_latitude_deg']) for r in rows]
print('south', sum(x < 0 for x in lat), 'north', sum(x > 0 for x in lat), 'lat range', min(lat), max(lat))
print('imu types', dict(collections.Counter(r['imu_type'] for r in rows)))
print('shared legs', len({r['shared_leg_id'] for r in rows}), 'files', len({r['filename'] for r in rows}))
print('dates', len({r['start_utc'][:10] for r in rows}), sorted(collections.Counter(r['start_utc'][:4] for r in rows).items()))
course = [float(r['mean_course_deg']) % 360 for r in rows]
print('course octants', sorted(collections.Counter(int(((c+22.5) % 360)//45) for c in course).items()))
print('speed kmh min/med/max', min(float(r['median_ground_speed_kmh']) for r in rows), med([float(r['median_ground_speed_kmh']) for r in rows]), max(float(r['median_ground_speed_kmh']) for r in rows))
print('duration s min/med/max', min(float(r['duration_s']) for r in rows), med([float(r['duration_s']) for r in rows]), max(float(r['duration_s']) for r in rows))
print('result_origin', dict(collections.Counter(r['result_origin'] for r in rows)))
print('latest_repeat_status', dict(collections.Counter(r['latest_repeat_status'] for r in rows)))
