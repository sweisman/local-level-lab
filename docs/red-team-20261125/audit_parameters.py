# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review audit of the fitted parameter values behind the published costs. Runs no fits."""
import collections
import csv
import json
import math
import statistics
import sys

csv.field_size_limit(10**9)
STRETCH, FITS = sys.argv[1], sys.argv[2]
CASES = ('bias1_unsubtracted', 'bias1_profiled_removal')
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
DPH = 3600*180/math.pi
stretches = {r['segment_id']: r for r in csv.DictReader(open(STRETCH, newline=''))}
fits = collections.defaultdict(list)
for r in csv.DictReader(open(FITS, newline='')):
    fits[(r['segment_id'], r['case_id'], r['model'])].append(r)
print('fit rows', sum(map(len, fits.values())), 'keys', len(fits))
print('roles', dict(collections.Counter(r['role'] for v in fits.values() for r in v)))


def published(seg, case, model):
    """The fit row whose cost equals the published stretch-table cost."""
    target = float(stretches[seg][f'{case}__{model}__cost'])
    best = None
    for r in fits[(seg, case, model)]:
        if not r['cost'] or not r['parameters']:
            continue
        gap = abs(float(r['cost'])-target)/max(target, 1e-300)
        if best is None or gap < best[0]:
            best = (gap, r)
    if best is None or best[0] > 1e-9:
        return None
    return json.loads(best[1]['parameters'])


missing = collections.Counter()
P = {}
for seg in stretches:
    for case in CASES:
        for model in MODELS:
            p = published(seg, case, model)
            if p is None:
                missing[(case, model)] += 1
            P[(seg, case, model)] = p
print('published fits without a matching parameter row:', dict(missing))

order = sorted(stretches, key=lambda s: stretches[s]['start_utc'])
print('\n== rotating globe, unsubtracted: fitted nuisance values (gyro bias deg/h, gain %, removal from profiled case) ==')
print('date       imu course   lat   dur | bias_x bias_y bias_z | gain_x gain_y gain_z | grav_d  acc_bz | lever_x lever_y lever_z | t_off  | removal')
for seg in order:
    s = stretches[seg]; p = P[(seg, CASES[0], 'sphere_rotating')]; q = P[(seg, CASES[1], 'sphere_rotating')]
    if p is None:
        print(s['start_utc'][:10], 'no parameters'); continue
    rem = 'n/a' if q is None else f"{q['earth_removal']:.3f}"
    print(f"{s['start_utc'][:10]} {s['imu_type']:>3s} {float(s['mean_course_deg']):6.1f} {float(s['mean_latitude_deg']):6.1f} {float(s['duration_s']):5.0f} |"
          f" {p['gyro_bias_x']*DPH:6.2f} {p['gyro_bias_y']*DPH:6.2f} {p['gyro_bias_z']*DPH:6.2f} |"
          f" {p['gyro_gain_x']*100:6.2f} {p['gyro_gain_y']*100:6.2f} {p['gyro_gain_z']*100:6.2f} |"
          f" {p['gravity_delta']:6.3f} {p['accel_bias_z']:7.3f} | {p['lever_x']:7.2f} {p['lever_y']:7.2f} {p['lever_z']:7.2f} | {p['time_offset']:6.3f} | {rem}")

print('\n== earth_removal fitted value, profiled case ==')
for model in MODELS:
    values = [P[(seg, CASES[1], model)]['earth_removal'] for seg in order if P[(seg, CASES[1], model)] is not None]
    at0 = sum(v < 1e-3 for v in values); at1 = sum(v > 1-1e-3 for v in values)
    interior = sorted(v for v in values if 1e-3 <= v <= 1-1e-3)
    print(f'{model:16s} n {len(values)} at 0: {at0} at 1: {at1} interior: {len(interior)}'
          + (f' (min {interior[0]:.3f} med {statistics.median(interior):.3f} max {interior[-1]:.3f})' if interior else ''))

print('\n== flat, unsubtracted vs profiled: removal value where profiled cost is >1% lower ==')
for seg in order:
    s = stretches[seg]
    a = float(s[f'{CASES[0]}__flat_still__cost']); b = float(s[f'{CASES[1]}__flat_still__cost'])
    q = P[(seg, CASES[1], 'flat_still')]
    if b < .99*a:
        print(f"{s['start_utc'][:10]} course {float(s['mean_course_deg']):6.1f} lat {float(s['mean_latitude_deg']):6.1f} unsub {a:10.4g} profiled {b:10.4g} factor {a/b:5.2f} removal {'n/a' if q is None else format(q['earth_removal'], '.3f')}")

print('\n== sign pattern at bounds, unsubtracted (count of + / - among values within 0.1% of the limit) ==')
LIMIT = dict(gyro_bias=math.radians(1)/3600, gyro_gain=.02, gravity_delta=.05, accel_bias=.25, accel_gain=.15, lever=10., time_offset=.15, position=100., velocity=20.)
for model in MODELS:
    signs = collections.defaultdict(lambda: [0, 0])
    for seg in order:
        p = P[(seg, CASES[0], model)]
        if p is None:
            continue
        for name, value in p.items():
            base = name if name in LIMIT else name.rsplit('_', 1)[0]
            if base in LIMIT and abs(abs(value)-LIMIT[base]) <= 1e-3*LIMIT[base]:
                signs[name][0 if value > 0 else 1] += 1
    print(model, {k: tuple(v) for k, v in sorted(signs.items())})
