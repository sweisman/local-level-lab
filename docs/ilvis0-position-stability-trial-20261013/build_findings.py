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
RECOVERY = ROOT/'docs/ilvis0-position-recovery-20261013'
PRECISION = ROOT/'docs/ilvis0-paired-precision-trial-20261014'
COST_PRECISION = ROOT/'docs/ilvis0-cost-precision-recovery-20261014'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recovery_updates(original, recovery):
    """Promote complete per-stretch comparisons, never a failed whole-run gate."""
    expected = {r['segment_id'] for r in original['results']
                if r['profile']['conditional_shape_preference'] == 'unresolved'}
    rows = recovery['comparisons']
    updates = {r['segment_id']: r for r in rows}
    if recovery['state'] != 'complete' or set(updates) != expected or len(rows) != len(expected):
        raise ValueError('completed recovery must cover each original unfinished stretch once')
    for row in rows:
        shape = row['profile']['conditional_shape_preference']
        if shape != 'unresolved':
            fits = [f for case in row['cases'] for f in case['fits']]
            if (not recovery['qualification']['controls_passed']
                    or not row['recovery_checks_passed'] or len(row['cases']) != 2
                    or len(fits) != 6 or not all(f['converged'] for f in fits)):
                raise ValueError('resolved recovery lacks complete primary/control/repeat checks')
    return updates


def precision_updates(previous, trial, targets):
    """Require a sealed, fully qualified trial; never replace a resolved result."""
    rows = trial['comparisons']
    updates = {r['segment_id']: r for r in rows}
    checks = trial['qualification']
    repeats = checks['repeatability']
    if (trial['state'] != 'complete' or not checks['qualified'] or not checks['controls_passed']
            or len(rows) != len(targets) or set(updates) != set(targets)
            or len(repeats) != len(targets)
            or {r['identity'].split('::')[0] for r in repeats} != set(targets)
            or not all(r['passed'] for r in repeats)):
        raise ValueError('complete precision qualification required')
    for sid, row in updates.items():
        fits = [f for c in row['cases'] for f in c['fits']]
        if (sid not in previous or previous[sid]['profile']['conditional_shape_preference'] != 'unresolved'
                or len(row['cases']) != 2 or len(fits) != 6 or not all(f['converged'] for f in fits)):
            raise ValueError('precision result must cover six fits of an unresolved stretch')
    return updates


def cost_precision_updates(previous, trial, targets):
    """A failed whole-run gate does not erase individually qualified stretches."""
    rows = trial['comparisons']
    updates = {r['segment_id']: r for r in rows}
    checks = trial['qualification']
    repeats = checks['repeatability']
    repeat_by_id = {r['identity'].split('::')[0]: r['passed'] for r in repeats}
    if (trial['state'] != 'complete' or len(rows) != len(targets) or set(updates) != set(targets)
            or len(repeats) != len(targets) or set(repeat_by_id) != set(targets)):
        raise ValueError('completed cost recovery must cover each frozen target once')
    for sid, row in updates.items():
        if sid not in previous or previous[sid]['profile']['conditional_shape_preference'] != 'unresolved':
            raise ValueError('cost recovery cannot replace a resolved comparison')
        fits = [f for c in row['cases'] for f in c['fits']]
        if row['profile']['conditional_shape_preference'] != 'unresolved' and (
                not checks['controls_passed'] or not repeat_by_id[sid] or len(row['cases']) != 2
                or len(fits) != 6 or not all(f['converged'] for f in fits)):
            raise ValueError('resolved cost recovery lacks primary/control/repeat checks')
    return updates


def sealed_precision(directory=PRECISION):
    receipt = json.loads((directory/'evidence-receipt.json').read_text())
    for name, digest in receipt['artifacts'].items():
        if Path(name).name != name or sha(directory/name) != digest:
            raise ValueError('precision publication hash mismatch')
    complete = json.loads((directory/'completion.json').read_text())
    if (complete['state'] != 'complete'
            or sha(directory/'summary.json') != complete['summary_sha256']
            or sha(directory/'manifest.json') != complete['manifest_sha256']
            or any(sha(directory/n) != h for n, h in complete['journal_hashes'].items())):
        raise ValueError('sealed precision trial required')
    return (json.loads((directory/'summary.json').read_text()),
            json.loads((directory/'manifest.json').read_text()))


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
    text += 'recovery run. Each recovered result passed all six primary fits, its scheduled repeat '
    text += 'and the fresh controls. Failed or partial comparisons remain unresolved. '
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
    recovery_receipt = json.loads((RECOVERY/'evidence-receipt.json').read_text())
    for name in ('summary.json', 'completion.json', 'manifest.json'):
        if sha(RECOVERY/name) != recovery_receipt['artifacts'][name]:
            raise ValueError('recovery publication hash mismatch')
    recovery_complete = json.loads((RECOVERY/'completion.json').read_text())
    if (recovery_complete['state'] != 'complete'
            or sha(RECOVERY/'summary.json') != recovery_complete['summary_sha256']
            or sha(RECOVERY/'manifest.json') != recovery_complete['manifest_sha256']):
        raise ValueError('sealed recovery required')
    recovery = json.loads((RECOVERY/'summary.json').read_text())
    updates = recovery_updates(original, recovery)
    precision, precision_manifest = sealed_precision()
    precision_rows = precision_updates(updates, precision, precision_manifest['plan']['target_segment_ids'])
    updates.update(precision_rows)
    cost_precision, cost_manifest = sealed_precision(COST_PRECISION)
    cost_rows = cost_precision_updates(updates, cost_precision, cost_manifest['plan']['target_segment_ids'])
    updates.update(cost_rows)
    recovered = [r for r in updates.values()
                 if r['profile']['conditional_shape_preference'] == 'globe']
    if len(records) != 53 or len(recovered) != 29:
        raise ValueError('frozen population changed')
    rows = []
    for sid, old in records.items():
        result = updates.get(sid, old)
        shape = result['profile']['conditional_shape_preference']
        rotation = result['profile']['rotation_diagnostics']
        background = bool(shape == 'globe' and rotation and
                          all(r['conditional_still_minus_rotating_cost'] > 0 for r in rotation))
        origin = 'completed_cost_precision' if sid in cost_rows else 'qualified_paired_precision' if sid in precision_rows else 'completed_recovery' if sid in updates else 'original_first_pass'
        rows.append(dict(inventory[sid], result_origin=origin,
                         shape_preference=shape, specified_background_preferred=background,
                         **route_context(tracks[sid])))
    tally = {label: sum(r['shape_preference'] == label for r in rows)
             for label in ('globe', 'flat', 'unresolved', 'ambiguous')}
    if tally != dict(globe=41, flat=0, unresolved=12, ambiguous=0):
        raise ValueError('combined tally differs from declared findings')
    finished = [r for r in rows if r['shape_preference'] == 'globe']
    with (HERE/'current-stretches.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r['start_utc'], r['filename'])))
    (HERE/'STRETCHES.md').write_text(stretch_report(rows))
    text = '# Updated airborne findings\n\n'
    text += '**41 globe preferences, zero flat, 12 unresolved** among the same 53 preselected stretches. '
    text += 'The original study supplied 12 complete comparisons; numerical recovery adds 29, '
    text += 'including the three previously recovered in the qualification trial. '
    text += 'All forty-one favor the specified background-field globe over the zero-field globe in both '
    text += 'processing cases. This does not identify the field\'s physical cause or measure a solar-versus-sidereal difference.\n\n'
    text += 'These are numerical model preferences. Statistical significance and uncertainty remain '
    text += 'uncalibrated. The original observations, selected intervals and first-pass results are preserved.\n\n'
    text += '## The twenty-nine recovered stretches\n\n'
    text += '| Source recording | Recorded IMU type | UTC interval | Duration | Minimum / median ground speed |\n'
    text += '|---|---:|---|---:|---:|\n'
    for r in sorted((inventory[item['segment_id']] for item in recovered), key=lambda r: (r['start_utc'], r['filename'])):
        text += f"| `{r['filename']}` | {r['imu_type']} | {r['start_utc']} to {r['end_utc']} | {float(r['duration_s'])/60:.2f} min | {float(r['minimum_ground_speed_kmh']):.1f} / {float(r['median_ground_speed_kmh']):.1f} km/h |\n"
    minutes = sum(float(inventory[r['segment_id']]['duration_s']) for r in recovered)/60
    text += f'\nThe twenty-nine stretches add **{minutes:.2f} minutes** of completed comparisons. '
    types = {kind: sum(str(r['imu_type']) == kind for r in finished) for kind in ('8', '21')}
    text += f"Completed findings include {types['8']} IMU8 and {types['21']} IMU21 stretches. "
    text += 'These codes identify instrument/data configurations, not unique unit serial numbers '
    text += 'or different experiment protocols. Their conversion scales are checked separately; '
    text += 'the selection and physical model comparisons are the same.\n\n'
    text += 'The two October 20 recordings overlap in time and must not be counted as two independent flights. '
    text += f"The forty-one resolved stretches contain {len({r['source_sha256'] for r in finished})} distinct recording hashes "
    text += f"across {len({r['start_utc'][:10] for r in finished})} dates, not forty-one established independent replications. "
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
    text += '## Completed wider recovery and remaining failures\n\n'
    text += 'The [wider recovery](../ilvis0-position-recovery-20261013/README.md) completed all '
    text += '159 new starts and 22,355 native integration sweeps, with 117 passing fits: '
    text += '84/115 primary recoveries, 27/38 repeats and all six controls. There were no execution errors. '
    text += 'The combined tally improves from 15/0/38 after the subset to 30/0/23. '
    text += 'Some primary and repeat checks failed, so the entire run did not qualify every comparison; '
    text += 'only individually complete comparisons contribute to the findings. '
    text += 'Incomplete calculations remain unknown, rather than evidence for either shape.\n\n'
    text += '\n## Qualified wider-arithmetic recovery\n\n'
    text += 'The [paired precision trial](../ilvis0-paired-precision-trial-20261014/RESULTS.md) passed '
    text += 'all 16 fits, including both controls and both perturbed repeats, in 129 native sweeps. '
    text += 'It adds the October 24, 2009 IMU8 and October 7, 2015 DMS stretches, bringing the tally '
    text += 'to 32/0/21. Wider internal arithmetic removes rounding sensitivity in these cost-only '
    text += 'stopping failures; measurements, physical models, calibration bounds, clock, receiver '
    text += 'weights and stopping tolerances are unchanged. Neither repeats nor probes replace failed '
    text += 'original fits. All earlier outcomes remain available.\n\n'
    text += 'The [completed cost-only recovery](../ilvis0-cost-precision-recovery-20261014/RESULTS.md) '
    text += 'passed 83/86 fits in 891 sweeps and about four hours: 69/72 primaries, both controls and '
    text += 'all twelve repeats. Nine additional stretches pass their complete comparisons, giving '
    text += '41/0/12. Three primary fits exhausted their forty-evaluation allowance, so those stretches '
    text += 'remain unresolved; the nine excluded stationarity/position-failure stretches remain unchanged. '
    text += 'The run did not qualify every target. Only individually complete comparisons are reported.\n\n'
    text += 'Next are bounded continuations of the three budget failures, followed by a separate '
    text += 'investigation of the other nine. [All stretch metadata](ANALYTICS.md) retains last costs, '
    text += 'stopping reasons and recorder-pair differences. No recorded interval or physical bound '
    text += 'was changed to obtain these recoveries.\n'
    (HERE/'FINDINGS.md').write_text(text)
    inputs = [BASELINE/'summary.json.gz', BASELINE/'eligible-stretches.csv', BASELINE/'selection.json.gz', BASELINE/'evidence-receipt.json',
              TRIAL/'completion.json']+[TRIAL/n for n in hashes]
    inputs += [RECOVERY/n for n in ('evidence-receipt.json', 'summary.json', 'completion.json', 'manifest.json')]
    inputs += [PRECISION/n for n in ('evidence-receipt.json', 'summary.json', 'completion.json', 'manifest.json', 'starts.jsonl', 'sweeps.jsonl')]
    inputs += [COST_PRECISION/n for n in ('evidence-receipt.json', 'summary.json', 'completion.json', 'manifest.json', 'starts.jsonl', 'sweeps.jsonl')]
    report = dict(inputs={str(p.relative_to(ROOT)): sha(p) for p in inputs},
                  sources={str(Path(__file__).relative_to(ROOT)): sha(__file__)},
                  artifacts={n: sha(HERE/n) for n in ('FINDINGS.md', 'STRETCHES.md', 'current-stretches.csv')},
                  tally=tally, observed_starts=0, native_predictions=0, original_files_read=0)
    (HERE/'findings-receipt.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(tally=tally, added_minutes=minutes,
                          imu_types=sorted({r['imu_type'] for r in finished}), observed_starts=0)))


if __name__ == '__main__':
    main()
