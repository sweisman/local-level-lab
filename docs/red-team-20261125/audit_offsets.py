# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review audit of level-axis gyro offsets under the winning model, and of the heading each
candidate chose. Reads published tables; runs no fits."""
import collections
import csv
import json
import math
import statistics
import sys

csv.field_size_limit(10**9)
STRETCH, FITS = sys.argv[1], sys.argv[2]
CASES = ('bias1_unsubtracted', 'bias1_profiled_removal')
DPH = 3600*180/math.pi
stretches = {r['segment_id']: r for r in csv.DictReader(open(STRETCH, newline=''))}
fits = collections.defaultdict(list)
for r in csv.DictReader(open(FITS, newline='')):
    fits[(r['segment_id'], r['case_id'], r['model'])].append(r)


def published(seg, case, model):
    target = float(stretches[seg][f'{case}__{model}__cost'])
    rows = [r for r in fits[(seg, case, model)] if r['cost'] and r['parameters']]
    r = min(rows, key=lambda r: abs(float(r['cost'])-target))
    return json.loads(r['parameters'])


def stats(name, values):
    print(f'{name:34s} n {len(values)} mean {statistics.mean(values):7.3f} sd {statistics.pstdev(values):6.3f} min {min(values):7.3f} max {max(values):7.3f}')


segs = sorted(stretches, key=lambda s: stretches[s]['start_utc'])
rot = {s: published(s, CASES[0], 'sphere_rotating') for s in segs}
print('== rotating globe, unsubtracted: horizontal gyro offsets the fit asked for (deg/h; limit is 1) ==')
stats('gyro_bias_x', [rot[s]['gyro_bias_x']*DPH for s in segs])
stats('gyro_bias_y', [rot[s]['gyro_bias_y']*DPH for s in segs])
stats('|bias_xy|', [math.hypot(rot[s]['gyro_bias_x'], rot[s]['gyro_bias_y'])*DPH for s in segs])
for label, pick in (('imu 8', lambda s: stretches[s]['imu_type'] == '8'), ('imu 21, 2009-2011', lambda s: stretches[s]['imu_type'] == '21' and stretches[s]['start_utc'] < '2012'),
                    ('imu 21, 2015', lambda s: stretches[s]['start_utc'] >= '2015'), ('northern hemisphere', lambda s: float(stretches[s]['mean_latitude_deg']) > 0)):
    chosen = [s for s in segs if pick(s)]
    stats('  bias_y, '+label, [rot[s]['gyro_bias_y']*DPH for s in chosen])

# Speed dependence: if a constant pitch-axis offset stood in for curvature, the offset the globe
# fit asks for would track speed with slope -1/R. Regress fitted bias_y on the globe transport rate.
speed = [float(stretches[s]['mean_position_ground_speed_mps']) for s in segs]
tr = [v/6371000.*DPH for v in speed]
by = [rot[s]['gyro_bias_y']*DPH for s in segs]
mx, my = statistics.mean(tr), statistics.mean(by)
sxx = sum((x-mx)**2 for x in tr); sxy = sum((x-mx)*(y-my) for x, y in zip(tr, by))
slope = sxy/sxx; resid = [y-my-slope*(x-mx) for x, y in zip(tr, by)]
se = math.sqrt(sum(e*e for e in resid)/(len(tr)-2)/sxx)
print(f'transport rate v/R spans {min(tr):.2f} to {max(tr):.2f} deg/h; slope of fitted bias_y on v/R = {slope:.3f} +/- {se:.3f} (a constant offset replacing curvature predicts a slope of magnitude 1; curvature as modelled predicts 0)')

print('\n== yaw correction (attitude_z, deg) each candidate chose; rotating vs flat ==')
print('date       course | rot_unsub flat_unsub flat_profiled removal')
big = 0
for s in segs:
    f0 = published(s, CASES[0], 'flat_still'); f1 = published(s, CASES[1], 'flat_still')
    a, b, c = (math.degrees(p['attitude_z']) for p in (rot[s], f0, f1))
    big += abs(c-a) > 20
    if f1['earth_removal'] > .5 or abs(b-a) > 20:
        print(f"{stretches[s]['start_utc'][:10]} {float(stretches[s]['mean_course_deg']):6.1f} | {a:8.1f} {b:9.1f} {c:12.1f} {f1['earth_removal']:8.3f}")
all_rot = [math.degrees(rot[s]['attitude_z']) for s in segs]
all_f0 = [math.degrees(published(s, CASES[0], 'flat_still')['attitude_z'])-math.degrees(rot[s]['attitude_z']) for s in segs]
all_f1 = [math.degrees(published(s, CASES[1], 'flat_still')['attitude_z'])-math.degrees(rot[s]['attitude_z']) for s in segs]
stats('rotating attitude_z', all_rot)
stats('flat unsub minus rotating', all_f0)
stats('flat profiled minus rotating', all_f1)
print('flat profiled yaw differs from rotating by more than 20 deg in', big, 'of', len(segs))
