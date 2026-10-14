# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render completed finite native probes; never imports an integration worker."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads((HERE/'evidence-receipt.json').read_text())
    for name,digest in receipt['artifacts'].items():
        if sha(HERE/name)!=digest:
            raise ValueError('completed diagnostic artifact mismatch')
    complete=json.loads((HERE/'completion.json').read_text())
    summary=json.loads((HERE/'summary.json').read_text())
    manifest=json.loads((HERE/'manifest.json').read_text())
    if (complete['state']!='complete' or sha(HERE/'summary.json')!=complete['summary_sha256']
            or sha(HERE/'manifest.json')!=complete['manifest_sha256']):
        raise ValueError('sealed native diagnostic required')
    for name,digest in complete['journal_hashes'].items():
        if sha(HERE/name)!=digest:
            raise ValueError('diagnostic journal mismatch')
    tasks={t['identity']:t for t in manifest['tasks']}
    if len(summary['results'])!=6 or summary['native_evaluations']>60:
        raise ValueError('finite diagnostic scope mismatch')
    failed=[r for r in summary['results'] if r['status']!='complete']
    rows=[];center_table='';probe_table=''
    repeat_max=kernel_max=0.
    for value in summary['results']:
        task=tasks[value['identity']]
        if value['status']!='complete':
            continue
        label=task['segment_id'][:8]
        central=max(value['value_tangent_difference']['maximum_neu_m'])
        repeat=max(*value['value_repeat']['maximum_neu_m'],*value['tangent_repeat']['maximum_neu_m'])
        repeat_max=max(repeat_max,repeat);kernel_max=max(kernel_max,central)
        center_table+=(f"| {label} | {task['reference']['converged']} | {value['center_tangent_cost']:.6g} "
                      f"| {value['center_value_tangent_cost_relative_difference']:.3g} "
                      f"| {central*1e6:.4g} | {repeat*1e6:.4g} |\n")
        for probe in value['probes']:
            position=max(probe['tangent_position_change']['rms_neu_m'])
            maximum=max(probe['tangent_position_change']['maximum_neu_m'])
            kernel_max=max(kernel_max,max(probe['value_tangent_difference']['maximum_neu_m']))
            cost_ratio=probe['tangent_cost_relative_change']/1e-8
            stationarity_ratio=probe['fresh_stationarity']/1e-4
            all_checks=(cost_ratio<=1 and stationarity_ratio<=1 and position<=.001 and maximum<=.01)
            row=dict(identity=value['identity'],segment_id=task['segment_id'],model=task['model'],
                     case_id=task['case_id'],original_converged=task['reference']['converged'],
                     fraction=probe['fraction'],cost_change_ratio=cost_ratio,
                     fresh_stationarity_ratio=stationarity_ratio,position_rms_max_m=position,
                     position_epoch_max_m=maximum,probe_checks_pass=all_checks,
                     center_cost=value['center_tangent_cost'],tangent_cost=probe['tangent_cost'],
                     value_cost=probe['value_cost'],affine_predicted_cost=probe['affine_predicted_cost'],
                     value_tangent_max_m=max(probe['value_tangent_difference']['maximum_neu_m']),
                     qualifies_original_fit=False)
            rows.append(row)
            probe_table+=(f"| {label} | {probe['fraction']:.2f} | {cost_ratio:.4g} "
                         f"| {stationarity_ratio:.4g} | {position*1000:.4g} | {all_checks} |\n")
    if rows:
        with (HERE/'probes.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
            writer.writeheader();writer.writerows(rows)
    label='All six endpoints completed' if not failed else f'{6-len(failed)}/6 endpoints completed'
    observations=''
    if not failed:
        observations='''## What these checks establish

- Every central objective reproduced its saved endpoint within the frozen
  reproduction limit. Both implementations produced identical repeated coordinates.
- At the October 2009 IMU8 failure, the half correction passes all measured probe
  checks, while the full correction misses the relative-cost limit narrowly.
- At the September 2015 DMS disc failure, the quarter correction moves vertical
  predictions by about 0.94 mm RMS and passes these checks; the full correction
  moves them by about 3.77 mm RMS.
- At the October 2015 DMS background-field failure, full, half and quarter
  corrections all miss the relative-cost check. The progression is not monotonic.
- The October 2015 loaner endpoint was complete under the original solver. It
  fails this newer full-correction check, although its half and quarter probes
  pass. Original completion and a fresh check under a later policy are distinct.

The two implementations disagree far too little at these evaluated points to
explain the failed cost probes. Exact repeated evaluations also rule out random
variation at the same parameters in this diagnostic. They **do not rule out
deterministic roundoff as parameters change**, inaccurate derivatives or nonlinear
curvature. The saved local systems are poorly conditioned, with weak directions
dominated by gravity correction and correlated calibration parameters.

The useful next test is derivative and accumulation precision in those directions,
before qualifying a revised numerical strategy. More attempts or accepting whichever
step fraction passes would not establish that the original fit is fully resolved.

'''
    text=f'''# Prediction precision at the shared-recorder endpoints

**{label}**, using {summary['native_evaluations']} native integration evaluations
and **zero optimizer starts**. The published finding remains **30 globe preferences,
zero flat and 23 unresolved**. These checks do not promote an old fit or change its
acceptance rules.

The [finite plan](PLAN.md) tests the three failed model/processing endpoints and
their three successful-recorder counterparts. Each retains its original complete
stretch, observations, clock, covariance and calibration bounds. The
[saved recorder-pair audit](../ilvis0-shared-leg-diagnosis-20261014/README.md)
compares measurements on common UTC seconds and explains the exact stopping failures.

## Central prediction checks

Both integration implementations are evaluated at identical saved parameters.
The value implementation predicts the track; the tangent implementation predicts
the track and its derivatives. Neither uses fused Group-1 navigation as an observation.
Two identical evaluations of each implementation test deterministic repeatability.

| Stretch ID prefix | Original endpoint passed | Reproduced tangent cost | Central value/tangent relative cost difference | Largest coordinate difference (µm) | Largest repeated-coordinate difference (µm) |
|---|---|---:|---:|---:|---:|
{center_table}
The largest repeat difference is **{repeat_max*1e6:.4g} µm**. The largest difference
between value and tangent coordinates, including all noncentral probes, is
**{kernel_max*1e6:.4g} µm**. These comparisons test the two implementations at
the specified points; they do not independently verify every derivative or
establish a precision floor for nearby parameters.

## Full, half and quarter local corrections

The correction is the same bounded affine least-squares direction used by the
stability test. Each fraction receives a fresh prediction and derivative evaluation.
Ratios at most one pass the original cost and gradient limits; position RMS must
remain at most 1 mm per axis, and no epoch may move more than 1 cm.

| Stretch ID prefix | Correction fraction | Fresh cost change / limit | Fresh gradient / limit | Largest axis RMS change (mm) | These probe checks pass |
|---|---:|---:|---:|---:|---|
{probe_table}
Half or quarter steps passing here are **diagnostic observations, not accepted fits**.
Shrinking a correction arbitrarily can hide remaining work; a revised stopping
procedure needs independent known-answer qualification and a separately frozen
observed comparison. The CSV retains affine predicted costs alongside actual
costs, rather than assuming a locally linear prediction is exact.

{observations}The next numerical investigation should distinguish integration roundoff,
derivative accuracy and nonlinear curvature in the weak gravity/calibration
directions. The September disc endpoint also needs its vertical stability failure
addressed. This study supplies no new nuisance freedom or statistical significance.

## Reproduce the report

```sh
~/venv/bin/python docs/ilvis0-shared-leg-probes-20261014/build_report.py
```

[Individual probes](probes.csv) preserve objective values, physical movements and
checks. Report rendering performs no integration or optimization. Completed native
work is frozen and cannot resume; interrupted identities receive no retries.
'''
    (HERE/'README.md').write_text(text)
    result=dict(inputs={str((HERE/n).relative_to(ROOT)):sha(HERE/n) for n in
                        ('summary.json','manifest.json','completion.json','evidence-receipt.json')},
                sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},
                artifacts={n:sha(HERE/n) for n in ('README.md','probes.csv') if (HERE/n).exists()},
                original_labels_changed=False,observed_fit_starts=0,native_predictions=0)
    (HERE/'report-receipt.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(completed=6-len(failed),native_evaluations=summary['native_evaluations'],
                         repeat_max_m=repeat_max,value_tangent_max_m=kernel_max,report_native_predictions=0)))


if __name__=='__main__':
    main()
