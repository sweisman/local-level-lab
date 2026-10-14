# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit sealed recovery and matched recorder metadata without new observations."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import scipy

from lll import ilvis0_pair_diagnosis as audit
from lll import ilvis0_boundary_diagnosis as tracks
from lll import ilvis0_rectangular_diagnosis as tangent

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RECOVERY = ROOT/'docs/ilvis0-position-recovery-20261013'
ANALYTICS = ROOT/'docs/ilvis0-position-stability-trial-20261013'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def write_csv(name, records):
    with (HERE/name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v
                         for k, v in record.items()} for record in records)


def main():
    inputs = {}
    receipt = json.loads((RECOVERY/'evidence-receipt.json').read_text())
    for name in ('summary.json', 'manifest.json', 'completion.json'):
        path = RECOVERY/name
        if sha(path) != receipt['artifacts'][name]:
            raise ValueError('sealed recovery artifact mismatch')
        inputs[str(path.relative_to(ROOT))] = sha(path)
    completion = json.loads((RECOVERY/'completion.json').read_text())
    summary = json.loads((RECOVERY/'summary.json').read_text())
    if completion['state'] != 'complete' or sha(RECOVERY/'summary.json') != completion['summary_sha256']:
        raise ValueError('completed recovery required')
    for name, report in (('current-stretches.csv', 'findings-receipt.json'),
                         ('shared-leg-pairs.csv', 'analytics-receipt.json')):
        evidence = json.loads((ANALYTICS/report).read_text())
        path = ANALYTICS/name
        if sha(path) != evidence['artifacts'][name]:
            raise ValueError('published inventory artifact mismatch')
        inputs[str(path.relative_to(ROOT))] = sha(path)
        inputs[str((ANALYTICS/report).relative_to(ROOT))] = sha(ANALYTICS/report)
    inventory = {r['segment_id']: r for r in rows(ANALYTICS/'current-stretches.csv')}
    pairs = rows(ANALYTICS/'shared-leg-pairs.csv')
    priorities = [r for r in pairs if r['priority_pair'] == 'True']
    if len(inventory) != 53 or len(pairs) != 12 or len(priorities) != 3:
        raise ValueError('frozen paired population changed')
    focus_ids = {r[k] for r in priorities for k in ('left_segment_id', 'right_segment_id')}
    comparisons = {r['segment_id']: r for r in summary['comparisons']}
    all_gates, focus_fits, repeat_rows = [], [], []
    for identity, fit in sorted(summary['results'].items()):
        sid, case, model, role = identity.split('::')
        row = dict(identity=identity, segment_id=sid, case_id=case, model=model, role=role,
                   converged=fit['converged'], cost=fit['residual_sum_squares'],
                   evaluations=fit['evaluations'], message=fit['message'],
                   **{k:v for k,v in audit.stopping_gates(fit).items() if k != 'converged'},
                   **audit.history_summary(fit))
        all_gates.append(row)
        if sid not in focus_ids:
            continue
        value = tangent.load_linearization(RECOVERY, fit)
        inputs[str((RECOVERY/fit['linearization_file']).relative_to(ROOT))] = fit['linearization_sha256']
        names, point, residual, jac = tangent._validated(value)
        tangent.check_saved_gradient(value, fit['gradient'])
        if not np.isclose(residual@residual, fit['residual_sum_squares'], rtol=1e-12, atol=1e-12):
            raise ValueError('saved cost does not reproduce')
        _, singular, right = np.linalg.svd(jac, full_matrices=False)
        order = np.argsort(-abs(right[-1]))[:5]
        row = dict(row, jacobian_condition=float(singular[0]/singular[-1]) if singular[-1] > 0 else None,
                   weakest_direction=[dict(parameter=names[i], weight=float(right[-1,i]**2)) for i in order],
                   active_bounds=fit['active_bounds'], track_rms_neu_m=fit['track_rms_neu_m'])
        focus_fits.append(row)
        if role == 'repeat':
            primary_id = identity.rsplit('::',1)[0]+'::primary'
            primary = summary['results'][primary_id]
            repeat = tracks.compare_saved_predictions(RECOVERY, primary, fit)
            repeat_rows.append(dict(identity=identity, **repeat))
            for endpoint in (primary, fit):
                inputs[str((RECOVERY/endpoint['epoch_file']).relative_to(ROOT))] = endpoint['epoch_sha256']
    pair_rows = []
    for pair in pairs:
        left, right = (inventory[pair[k]] for k in ('left_segment_id','right_segment_id'))
        pair_rows.append(dict(pair, left_disposition=left['shape_preference'],
                             right_disposition=right['shape_preference'],
                             completion_mismatch=left['shape_preference'] != right['shape_preference']))
    counts = dict(collections.Counter(';'.join(r['failed_gates']) or 'none'
                                      for r in all_gates if not r['converged']))
    failures = [r for r in focus_fits if not r['converged'] and r['role']=='primary']
    if len(failures) != 3:
        raise ValueError('priority failure population changed')
    result = dict(version=audit.VERSION, combined_tally=summary['combined_tally'],
                  pairs=pair_rows, focus_fits=focus_fits, repeated_predictions=repeat_rows,
                  failed_gate_counts=counts, observed_fit_starts=0, native_predictions=0,
                  original_files_read=0, original_labels_changed=False,
                  scientific_decision='abstain')
    (HERE/'diagnosis.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    write_csv('pairs.csv', pair_rows)
    write_csv('stopping-gates.csv', all_gates)
    write_csv('priority-fits.csv', focus_fits)
    table = ''
    for pair in priorities:
        left, right = (inventory[pair[k]] for k in ('left_segment_id','right_segment_id'))
        rates = [float(pair['raw_aircraft_difference_'+axis+'_dph']) for axis in ('x','y','z')]
        rms = [float(pair['raw_aircraft_difference_rms_'+axis+'_dph']) for axis in ('x','y','z')]
        table += (f"| {left['start_utc'][:10]} | {left['imu_type']} / {right['imu_type']} "
                  f"| {pair['raw_aircraft_matched_seconds']} | "
                  f"{rates[0]:+.3f}, {rates[1]:+.3f}, {rates[2]:+.3f} "
                  f"| {rms[0]:.3f}, {rms[1]:.3f}, {rms[2]:.3f} "
                  f"| {left['shape_preference']} / {right['shape_preference']} |\n")
    failed_table = ''
    for row in failures:
        cost = row['cost_change_ratio']
        failed_table += (f"| {inventory[row['segment_id']]['start_utc'][:10]} / {row['segment_id'][:8]} "
                         f"| {row['model']} / {row['case_id'].removeprefix('bias1_')} "
                         f"| {row['endpoint_stationarity_ratio']:.3g} "
                         f"| {cost:.3g} | {row['maximum_position_rms_m']*1000:.4g} "
                         f"| {', '.join(row['failed_gates'])} |\n")
    repeat_table = ''
    for row in repeat_rows:
        repeat_table += (f"| {row['identity'].split('::')[0][:8]} / {row['identity'].split('::')[2]} "
                         f"| {row['primary_converged']} / {row['repeat_converged']} "
                         f"| {row['relative_cost_difference']:.3g} "
                         f"| {max(row['track_difference_rms_neu_m'])*1000:.4g} |\n")
    mismatches = sum(r['completion_mismatch'] for r in pair_rows)
    text = f'''# Same flight leg, different recorder completion

The completed recovery reports **30 globe preferences, zero flat and 23 unresolved**.
The receiver-track inventory contains twelve overlapping recorder pairs; **{mismatches}**
have different current completion outcomes. These are candidate shared tracks, not
verified aircraft or installation identities. The three priority pairs each have
one unresolved recorder blocked by exactly one primary fit.

This audit reads sealed fits, saved tangents, prediction errors and the existing
matched-time rate summaries. It performs **zero new fits, zero native predictions
and zero original-file reads**. It does not change any result label.

## What the two recorders measured

An inertial measurement unit (IMU) measures turning and acceleration. The following
differences use summed original angular increments, converted to aircraft-mounted
axes, on the **same complete UTC seconds**. Signs are left recorder minus right;
the linked CSV identifies both filenames and exact overlapping bounds. These are
rates including aircraft motion, not inferred background fields or bias estimates.

| Date | IMU types, left / right | Matched seconds | Mean X, Y, Z difference (°/h) | RMS X, Y, Z difference (°/h) | Current result, left / right |
|---|---|---:|---|---|---|
{table}
The mean differences alone do not establish whether noise, mount alignment,
calibration or processing caused the solver difference. RMS differences preserve
time variation that an overall mean can hide. Mount conventions are applied
separately; matching a route does not establish identical lever arms or clocks.
The fuller course-frame correction uses fused Group-1 attitude and remains a
consistency diagnostic, never independent Earth-model evidence. The
[analytics definitions](../ilvis0-position-stability-trial-20261013/ANALYTICS.md)
explain the raw, level-course proxy and fused-context columns.

## The exact checks that failed

The endpoint and fresh gradient limits are 1e-4; relative-cost change must be at
most 1e-8; actual predicted-position movement must be at most 1 mm RMS per axis
and 1 cm at every receiver epoch. A ratio below one passes that check. These are
numerical tolerances, not instrument accuracy specifications.

| Date / unfinished stretch | Model / processing | Endpoint gradient / limit | Fresh cost change / limit | Largest axis RMS change (mm) | Failed checks |
|---|---|---:|---:|---:|---|
{failed_table}
All three already pass endpoint and fresh gradient checks. The October 2009 and
October 2015 background-field fits fail **only the relative-cost change check**;
their correction moves predicted positions by micrometres. The September 2015 disc
fit passes the cost check but moves vertical predictions by about 3.77 mm RMS,
exceeding the unchanged 1 mm limit. None ran out of its fit allowance.

The flat fit's stopping failure is not a flat preference. Its saved cost is much
larger than the globe-family cost on that recorder. Conversely, small movements
do not justify silently accepting the other two failures. Saved rejected steps
cannot establish the prediction noise floor or rule out nonlinear curvature.
The [priority fit CSV](priority-fits.csv) records objective values, bounds, local
conditioning and the weakest parameter combinations alongside these checks.

## What repeated starts show

These are primary-versus-repeat predictions from the **same recorder and interval**,
not cross-instrument comparisons. Agreement limits remain 1e-6 relative cost and
1 cm RMS on every axis; both starts must pass their own stopping checks as well.

| Stretch / repeated model | Primary / repeat passed | Relative cost difference | Largest axis prediction difference (mm) |
|---|---|---:|---:|
{repeat_table}
The October 2009 repeat passes while its primary does not. Approximate agreement
does not replace the failed primary. The October 2015 primary and repeat both
remain unresolved; the September repeat checks the zero-field globe, not its
unfinished disc fit. These different checks must not be conflated.

## Next bounded investigation

1. Measure fresh prediction and tangent agreement at the three failed endpoints
   and their corresponding successful-recorder endpoints. Preserve each original
   full stretch and compare the raw measurements on the common UTC interval.
2. Test deterministic repeat evaluation, value-versus-tangent prediction consistency,
   and full/half/quarter local corrections under the original bounds and clock.
   A physically small correction can still change a stringent whitened cost check.
3. Diagnose the vertical direction separately for the September disc failure.
   Changing the cost tolerance cannot resolve its position-stability failure.
4. Qualify any numerical change on known-answer controls and a separately frozen
   paired trial with all three models and both processing assumptions. Do not
   substitute a successful neighboring recorder or promote saved endpoints.

No broader rerun or additional nuisance freedom follows from this audit. The
completed recovery allowance remains closed. Background-field cause, absolute-fit
adequacy and statistical uncertainty remain separate questions.

## Reproduce

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py -- ~/venv/bin/python docs/ilvis0-shared-leg-diagnosis-20261014/build_report.py
```

[All twelve recorder pairs](pairs.csv), [all new and reused stopping endpoints](stopping-gates.csv),
and [priority fit details](priority-fits.csv) retain the numerical evidence. The
receipt hashes every inspected input and records the numerical environment.
'''
    (HERE/'README.md').write_text(text)
    sources = [Path(__file__), ROOT/'analysis/lll/ilvis0_pair_diagnosis.py',
               ROOT/'analysis/tests/test_ilvis0_pair_diagnosis.py',
               ROOT/'analysis/lll/ilvis0_boundary_diagnosis.py',
               ROOT/'analysis/lll/ilvis0_rectangular_diagnosis.py',
               ROOT/'analysis/lll/ilvis0_recovery_diagnosis.py']
    evidence = dict(version=audit.VERSION, inputs=inputs,
                    sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
                    artifacts={n:sha(HERE/n) for n in ('README.md','diagnosis.json','pairs.csv','stopping-gates.csv','priority-fits.csv')},
                    environment=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
                    observed_fit_starts=0, native_predictions=0, original_files_read=0)
    (HERE/'evidence-receipt.json').write_text(json.dumps(evidence, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(pair_count=len(pairs), mismatched_pairs=mismatches,
                         failed_gate_counts=counts, priority_failures=len(failures),
                         observed_fit_starts=0, native_predictions=0)))


if __name__ == '__main__':
    main()
