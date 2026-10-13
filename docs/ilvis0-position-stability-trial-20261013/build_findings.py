# SPDX-License-Identifier: AGPL-3.0-or-later
"""Summarize sealed trial and first-pass metadata; no original data or refits."""
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASELINE = ROOT/'docs/ilvis0-highspeed-segments-20261008'
TRIAL = ROOT/'data/ilvis0-position-stability-trial-20261013'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def route_context(fixes):
    """Describe the saved receiver track, without using fused attitude or gyro data."""
    north = east = elapsed = latitude_sum = distance_km = 0.
    latitudes = [math.degrees(f['latitude_rad']) for f in fixes]
    for a, b in zip(fixes, fixes[1:]):
        dt = b['time_s'] - a['time_s']
        if dt <= 0:
            raise ValueError('receiver timestamps must increase')
        lat_a, lat_b = a['latitude_rad'], b['latitude_rad']
        delta_lon = b['longitude_rad'] - a['longitude_rad']
        y = math.sin(delta_lon) * math.cos(lat_b)
        x = math.cos(lat_a)*math.sin(lat_b) - math.sin(lat_a)*math.cos(lat_b)*math.cos(delta_lon)
        if math.hypot(x, y) == 0:
            raise ValueError('course undefined for coincident receiver positions')
        bearing = math.atan2(y, x)
        north += dt * math.cos(bearing)
        east += dt * math.sin(bearing)
        elapsed += dt
        latitude_sum += dt * math.degrees((lat_a + lat_b) / 2)
        h = math.sin((lat_b-lat_a)/2)**2 + math.cos(lat_a)*math.cos(lat_b)*math.sin(delta_lon/2)**2
        distance_km += 2*6371.*math.asin(math.sqrt(min(1., max(0., h))))
    if elapsed <= 0 or math.hypot(north, east) < 1e-12 * elapsed:
        raise ValueError('mean course undefined')
    return dict(mean_course_deg=math.degrees(math.atan2(east, north)) % 360,
                mean_latitude_deg=latitude_sum/elapsed,
                minimum_latitude_deg=min(latitudes), maximum_latitude_deg=max(latitudes),
                gps_track_km=distance_km)


def stretch_report(rows):
    text = '# All 53 selected flight stretches\n\n'
    tally = {label: sum(r['shape_preference'] == label for r in rows)
             for label in ('globe', 'flat', 'unresolved')}
    text += f"**{tally['globe']} globe preferences, {tally['flat']} flat, {tally['unresolved']} unresolved.** "
    text += 'Current dispositions combine the preserved first study with the completed, qualified '
    text += 'recovery trial. Partial fits from the ongoing wider recovery are not promoted to findings. '
    text += 'An unresolved comparison supplies no conclusion about shape. These are numerical '
    text += 'preferences; statistical significance has not yet been calibrated.\n\n'
    text += 'An inertial measurement unit (IMU) records angular and acceleration increments. '
    text += 'Every stretch below uses Applanix Group-4 increments and the primary receiver positions. '
    text += 'Recorded IMU types identify configurations, not individual serial numbers. '
    text += 'Overlapping tracks are not independent flights.\n\n'
    text += 'Selection requires at least four continuous minutes, every supported receiver ground-speed '
    text += 'sample at least 700 km/h, and the frozen motion, completeness and configuration checks. '
    text += 'Intervals were selected before comparing model residuals. '
    text += '[Full eligibility criteria](../ilvis0-highspeed-segments-20261008/ELIGIBILITY.md) '
    text += 'and [methodology](../METHODOLOGY.md) describe those checks.\n\n'
    text += '**Course** is direction of travel over the ground, clockwise from true north '
    text += '(0° north, 90° east). It is the time-weighted circular mean of bearings between '
    text += 'successive saved receiver positions, not aircraft nose heading. Latitude is the '
    text += 'time-weighted mean of receiver latitude, followed by its minimum–maximum range; '
    text += 'negative values are south. Track distances use a 6,371 km spherical radius for '
    text += 'route description only; they are not model-comparison evidence.\n\n'
    text += 'All resolved stretches also prefer the specified background-field globe over the '
    text += 'zero-field globe under both processing assumptions. This does not establish the '
    text += "field's cause or distinguish solar from sidereal rate. "
    text += '[Findings and recovery checks](FINDINGS.md) explain the comparisons. '
    text += '[The downloadable inventory](current-stretches.csv) includes exact source hashes, '
    text += 'intervals, course, latitude and result origins.\n\n'
    text += 'For deeper analysis, download the [comprehensive metadata CSV](stretch-analytics.csv). '
    text += 'It adds raw gyro means, explicitly labeled motion-correction diagnostics, north/east '
    text += 'velocities, transport predictions, all six saved model costs and stopping reasons, '
    text += 'and shared-leg IDs. [Definitions and limitations](ANALYTICS.md), '
    text += '[fit history](fit-analytics.csv) and [matched recorder differences](shared-leg-pairs.csv) '
    text += 'keep those quantities and their provenance separate.\n\n'
    text += '| Source recording / stretch ID | UTC interval | IMU type | Minutes | Ground speed min / median (km/h) | Mean course | Latitude mean (range), ° | Track (km) | Current disposition |\n'
    text += '|---|---|---:|---:|---:|---:|---:|---:|---|\n'
    directions = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
    for r in sorted(rows, key=lambda r: (r['start_utc'], r['filename'])):
        course = r['mean_course_deg']
        direction = directions[int((course+22.5)//45) % 8]
        disposition = {'globe': 'Globe preferred', 'flat': 'Flat preferred',
                       'unresolved': 'Unresolved', 'ambiguous': 'Conflicting comparisons'}[r['shape_preference']]
        text += (f"| `{r['filename']}`<br>`{r['segment_id']}` | {r['start_utc']}<br>to {r['end_utc']} "
                 f"| {r['imu_type']} | {float(r['duration_s'])/60:.2f} "
                 f"| {float(r['minimum_ground_speed_kmh']):.1f} / {float(r['median_ground_speed_kmh']):.1f} "
                 f"| {course:.1f}° {direction} | {r['mean_latitude_deg']:.2f} "
                 f"({r['minimum_latitude_deg']:.2f} to {r['maximum_latitude_deg']:.2f}) "
                 f"| {r['gps_track_km']:.1f} | {disposition} |\n")
    return text


def main():
    complete = json.loads((TRIAL/'completion.json').read_text())
    if complete['state'] != 'complete':
        raise ValueError('completed trial required')
    hashes = dict(complete['journal_hashes'], **{'manifest.json': complete['manifest_sha256'],
                                               'summary.json': complete['summary_sha256']})
    for name, digest in hashes.items():
        if sha(TRIAL/name) != digest:
            raise ValueError('sealed trial hash mismatch')
    trial = json.loads((TRIAL/'summary.json').read_text())
    if not trial['qualification']['qualified'] or not all(f['converged'] for f in trial['results'].values()):
        raise ValueError('full qualification required')
    receipt = json.loads((BASELINE/'evidence-receipt.json').read_text())
    if sha(BASELINE/'summary.json.gz') != receipt['artifacts']['summary.json.gz']:
        raise ValueError('original result hash mismatch')
    if sha(BASELINE/'eligible-stretches.csv') != receipt['artifacts']['eligible-stretches.csv']:
        raise ValueError('original inventory hash mismatch')
    if sha(BASELINE/'selection.json.gz') != receipt['artifacts']['selection.json.gz']:
        raise ValueError('original selection hash mismatch')
    original = json.loads(gzip.decompress((BASELINE/'summary.json.gz').read_bytes()))
    selection = json.loads(gzip.decompress((BASELINE/'selection.json.gz').read_bytes()))
    tracks = {r['segment']['segment_id']: r['segment']['receiver_fixes'] for r in selection['selected']}
    records = {r['segment_id']: r for r in original['results']}
    with (BASELINE/'eligible-stretches.csv').open() as stream:
        inventory = {r['segment_id']: r for r in csv.DictReader(stream)}
    recovered = [r for r in trial['comparisons']
                 if records[r['segment_id']]['profile']['conditional_shape_preference'] == 'unresolved']
    if len(records) != 53 or len(recovered) != 3:
        raise ValueError('frozen population changed')
    updates = {r['segment_id']: r for r in recovered}
    rows = []
    for sid, old in records.items():
        result = updates.get(sid, old)
        shape = result['profile']['conditional_shape_preference']
        rotation = result['profile']['rotation_diagnostics']
        background = bool(shape == 'globe' and rotation and
                          all(r['conditional_still_minus_rotating_cost'] > 0 for r in rotation))
        rows.append(dict(inventory[sid], result_origin='qualified_recovery' if sid in updates else 'original_first_pass',
                         shape_preference=shape, specified_background_preferred=background,
                         **route_context(tracks[sid])))
    tally = {label: sum(r['shape_preference'] == label for r in rows)
             for label in ('globe', 'flat', 'unresolved', 'ambiguous')}
    if tally != dict(globe=15, flat=0, unresolved=38, ambiguous=0):
        raise ValueError('combined tally differs from declared findings')
    finished = [r for r in rows if r['shape_preference'] == 'globe']
    with (HERE/'current-stretches.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r['start_utc'], r['filename'])))
    (HERE/'STRETCHES.md').write_text(stretch_report(rows))
    text = '# Updated airborne findings\n\n'
    text += '**15 globe preferences, zero flat, 38 unresolved** among the same 53 preselected stretches. '
    text += 'The original study supplied 12 complete comparisons; the qualified recovery adds three. '
    text += 'All fifteen favor the specified background-field globe over the zero-field globe in both '
    text += 'processing cases. This does not identify the field\'s physical cause or measure a solar-versus-sidereal difference.\n\n'
    text += 'These are numerical model preferences. Statistical significance and uncertainty remain '
    text += 'uncalibrated. The original observations, selected intervals and first-pass results are preserved.\n\n'
    text += '## The three newly completed stretches\n\n'
    text += '| Source recording | Recorded IMU type | UTC interval | Duration | Minimum / median ground speed |\n'
    text += '|---|---:|---|---:|---:|\n'
    for r in sorted((inventory[sid] for sid in updates), key=lambda r: (r['start_utc'], r['filename'])):
        text += f"| `{r['filename']}` | {r['imu_type']} | {r['start_utc']} to {r['end_utc']} | {float(r['duration_s'])/60:.2f} min | {float(r['minimum_ground_speed_kmh']):.1f} / {float(r['median_ground_speed_kmh']):.1f} km/h |\n"
    minutes = sum(float(inventory[sid]['duration_s']) for sid in updates)/60
    text += f'\nThe three stretches add **{minutes:.2f} minutes** of completed comparisons. '
    text += 'One is IMU8 and two are IMU21, so completed findings now include both recorded types. '
    text += 'These codes identify instrument/data configurations, not unique unit serial numbers '
    text += 'or different experiment protocols. Their conversion scales are checked separately; '
    text += 'the selection and physical model comparisons are the same.\n\n'
    text += 'The two October 20 recordings overlap in time and must not be counted as two independent flights. '
    text += f"The fifteen resolved stretches contain {len({r['source_sha256'] for r in finished})} distinct recording hashes "
    text += f"across {len({r['start_utc'][:10] for r in finished})} dates, not fifteen established independent replications. "
    text += '[All 53 stretches](STRETCHES.md) list current dispositions, courses and latitudes. '
    text += '[The current inventory](current-stretches.csv) preserves exact sources, hashes, intervals, speeds and result origins.\n\n'
    text += '## What changed in the calculation\n\n'
    text += 'The physical models, gyro-offset bounds, receiver weights and integration clock are unchanged. '
    text += 'The revised solver checks its final correction with a fresh full-model prediction in metres, '
    text += 'rather than rejecting it solely from a local residual approximation. The gradient and '
    text += 'objective-change limits remain; predicted movement must be at most 1 mm RMS per axis and '
    text += '1 cm at any receiver epoch. These are numerical stopping tolerances, not sensor accuracy claims.\n\n'
    text += 'The trial passed **24/24 fits**, including 15 primary recoveries, six controls and three '
    text += 'predetermined perturbed-start repeats, using 393 native sweeps. Each newly completed stretch '
    text += 'has all six model/case fits and a passing repeat. Repeat agreement demonstrates numerical '
    text += 'repeatability under these starts; it does not prove a global minimum. '
    text += '[Individual results](RESULTS.md) and the [finite plan](PLAN.md) retain the evidence.\n\n'
    text += '## Continuing the recovery\n\n'
    text += 'The [wider recovery run](../ilvis0-position-recovery-20261013/README.md) is active. '
    text += 'It reuses the qualified subset and permits 159 new starts with no retries. Partial fits '
    text += 'are not added to the headline until a stretch passes its complete comparison and repeat. '
    text += 'Incomplete calculations remain unknown, rather than evidence for either shape.\n'
    (HERE/'FINDINGS.md').write_text(text)
    inputs = [BASELINE/'summary.json.gz', BASELINE/'eligible-stretches.csv', BASELINE/'selection.json.gz', BASELINE/'evidence-receipt.json',
              TRIAL/'completion.json']+[TRIAL/n for n in hashes]
    report = dict(inputs={str(p.relative_to(ROOT)): sha(p) for p in inputs},
                  sources={str(Path(__file__).relative_to(ROOT)): sha(__file__)},
                  artifacts={n: sha(HERE/n) for n in ('FINDINGS.md', 'STRETCHES.md', 'current-stretches.csv')},
                  tally=tally, observed_starts=0, native_predictions=0, original_files_read=0)
    (HERE/'findings-receipt.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(tally=tally, added_minutes=minutes,
                          imu_types=sorted({r['imu_type'] for r in finished}), observed_starts=0)))


if __name__ == '__main__':
    main()
