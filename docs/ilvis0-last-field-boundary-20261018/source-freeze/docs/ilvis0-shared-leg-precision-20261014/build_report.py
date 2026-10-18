# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report completed arithmetic diagnostics without integration or fitting."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def passing(row):
    return (row['cost_relative_change']<=1e-8 and row['stationarity']<=1e-4
            and max(row['position_change']['rms_neu_m'])<=.001
            and max(row['position_change']['maximum_neu_m'])<=.01)


def main():
    receipt=json.loads((HERE/'evidence-receipt.json').read_text())
    for name,digest in receipt['artifacts'].items():
        if sha(HERE/name)!=digest:
            raise ValueError('precision artifact hash mismatch')
    summary=json.loads((HERE/'summary.json').read_text())
    manifest=json.loads((HERE/'manifest.json').read_text())
    complete=json.loads((HERE/'completion.json').read_text())
    if (complete['state']!='complete' or complete['manifest_sha256']!=sha(HERE/'manifest.json')
            or complete['summary_sha256']!=sha(HERE/'summary.json')):
        raise ValueError('completed precision freeze required')
    for name,digest in complete['journal_hashes'].items():
        if sha(HERE/name)!=digest:
            raise ValueError('precision journal mismatch')
    tasks={t['identity']:t for t in manifest['tasks']}
    centers='';probe_table='';corrections='';rows=[];successes=0;failures=[]
    for result in summary['results']:
        identity=result['identity'];task=tasks[identity];sid=task['segment_id'][:8]
        if result['status']!='complete':
            failures.append(identity);continue
        successes+=1
        shift=max(result['central_coordinate_difference']['rms_neu_m'])*1e6
        centers+=(f"| {sid} | {task['reference']['converged']} | {result['ordinary_center_cost']:.8g} "
                  f"| {result['extended_center_cost']:.8g} | {shift:.4g} "
                  f"| {result['central_stationarity'][0]:.3g} / {result['central_stationarity'][1]:.3g} |\n")
        fixed=result['fixed_correction_probes']
        for value in fixed:
            row=dict(identity=identity,segment_id=task['segment_id'],case_id=task['case_id'],model=task['model'],
                     original_converged=task['reference']['converged'],direction='frozen_ordinary_correction',
                     arithmetic=value['arithmetic'],fraction=value['fraction'],cost=value['cost'],
                     cost_change_ratio=value['cost_relative_change']/1e-8,
                     affine_predicted_cost=value['affine_predicted_cost'],
                     stationarity_ratio=value['stationarity']/1e-4,
                     position_rms_max_m=max(value['position_change']['rms_neu_m']),
                     linear_error_rms_max_m=max(value['linear_prediction_error']['rms_neu_m']),
                     probe_checks_pass=passing(value),qualifies_original_fit=False)
            rows.append(row)
        old=next(v for v in fixed if v['fraction']==1 and v['arithmetic']=='ordinary')
        new=next(v for v in fixed if v['fraction']==1 and v['arithmetic']=='extended')
        old_error=max(old['linear_prediction_error']['rms_neu_m'])*1e6
        new_error=max(new['linear_prediction_error']['rms_neu_m'])*1e6
        probe_table+=(f"| {sid} | {old['cost_relative_change']/1e-8:.4g} / {new['cost_relative_change']/1e-8:.4g} "
                      f"| {old_error:.4g} / {new_error:.4g} | {passing(old)} / {passing(new)} |\n")
        for value in result['extended_correction_probes']:
            rows.append(dict(rows[-1],direction='fresh_extended_correction',arithmetic=value['arithmetic'],fraction=1.,
                cost=value['cost'],cost_change_ratio=value['cost_relative_change']/1e-8,
                affine_predicted_cost=value['affine_predicted_cost'],stationarity_ratio=value['stationarity']/1e-4,
                position_rms_max_m=max(value['position_change']['rms_neu_m']),
                linear_error_rms_max_m=max(value['linear_prediction_error']['rms_neu_m']),probe_checks_pass=passing(value)))
        new=next(v for v in result['extended_correction_probes'] if v['arithmetic']=='extended')
        corrections+=(f"| {sid} | {new['cost_relative_change']/1e-8:.4g} | {new['stationarity']/1e-4:.4g} "
                       f"| {max(new['position_change']['rms_neu_m'])*1000:.4g} | {passing(new)} |\n")
    if rows:
        with (HERE/'probes.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
            writer.writeheader();writer.writerows(rows)
    bits=manifest['extended_kernel']['internal_mantissa_bits']
    old_pass=sum(r['probe_checks_pass'] for r in rows if r['direction']=='frozen_ordinary_correction' and r['arithmetic']=='ordinary' and r['fraction']==1.)
    wide_pass=sum(r['probe_checks_pass'] for r in rows if r['direction']=='frozen_ordinary_correction' and r['arithmetic']=='extended' and r['fraction']==1.)
    fresh_pass=sum(r['probe_checks_pass'] for r in rows if r['direction']=='fresh_extended_correction' and r['arithmetic']=='extended')
    text=f'''# Wider arithmetic at the same airborne endpoints

**{successes}/6 fixed endpoints completed**, using {summary['native_evaluations']}
integration evaluations and **zero optimizer starts**. Findings remain
**30 globe preferences, zero flat and 23 unresolved**. No fitted result is promoted.

The diagnostic changes internal arithmetic from 53 to **{bits} mantissa bits**,
keeping the same physical equations, observations, bounds, nominal packet clock
and timestamp branch choices. Inputs and exported coordinates/derivatives remain
float64. The generated source and compiler/binary hashes are retained.
The [finite plan](PLAN.md) explains all fourteen evaluations per endpoint.

Eleven known-answer software controls passed before archived evaluations: exact
straight-disc motion and its analytic velocity derivative, every active derivative
under all three models and both processing cases, and finite-call controls.
Software controls are not empirical calibration or Earth-model campaigns.

## Identical saved parameters

Costs are the same declared whitened sum of squared receiver-coordinate errors.
Coordinate shift is the largest axis RMS difference between arithmetic choices.
The paired recorder keeps its own original complete stretch; it does not replace
the failed recording or share fitted calibration without evidence.

| Stretch ID prefix | Saved endpoint passed | Ordinary cost | Wider cost | Central coordinate shift (µm) | Ordinary / wider stationarity |
|---|---|---:|---:|---:|---:|
{centers}
Small cost changes at identical parameters can matter to a numerical stopping
limit of 1e-8. They are not changes in the underlying observations or model identity.

## Same frozen correction under both arithmetic choices

The following uses the exact same parameter direction, at full size, for both
implementations. All five fractions appear in the downloadable CSV. Linear error
is the difference between the actual physical prediction change and that predicted
by the center's derivative, reported as the largest axis RMS. It includes nonlinear
curvature as well as numerical effects; it is not a direct instrument error.

| Stretch ID prefix | Ordinary / wider cost-change ratio | Ordinary / wider linear error (µm) | Full probe checks pass, ordinary / wider |
|---|---:|---:|---|
{probe_table}
The same full direction passes **{old_pass}/{successes}** ordinary-arithmetic probes
and **{wide_pass}/{successes}** wider-arithmetic probes. These are fixed diagnostics,
not counts of recovered fits. A wider kernel's center and correction must be
qualified together before a subsequent numerical trial.

## Correction calculated from the wider derivative

This table uses one bounded affine correction calculated at the wider center,
then evaluated with wider arithmetic. It is separate from the frozen-direction
comparison above. Ratios at most one pass the unchanged numerical limits.

| Stretch ID prefix | Cost change / limit | Fresh stationarity / limit | Largest axis RMS change (mm) | These probe checks pass |
|---|---:|---:|---:|---|
{corrections}
**{fresh_pass}/{successes}** pass these probes. An affine correction is not an
observed-data optimization, and a diagnostic pass does not establish a global
minimum or replace a primary/repeat comparison. The original failure labels remain.

## Interpretation and next qualification

The comparison isolates numerical representation while holding the declared model
fixed. Improvement in local prediction agreement supports further precision testing;
lack of improvement leaves nonlinear curvature or weak calibration combinations
as unresolved explanations. A general change needs known-answer solver checks and
a separately frozen paired-recording trial, retaining all models, both processing
assumptions, repeated starts and the original tolerances. No extra bias freedom,
automatic retries or corpus-wide rerun follows from this diagnostic.

## Reproduce the report

```sh
~/venv/bin/python docs/ilvis0-shared-leg-precision-20261014/build_report.py
```

[Individual precision probes](probes.csv) retain all fractions and both directions.
Rendering performs no integration or optimization. Completed native work is frozen.
'''
    (HERE/'README.md').write_text(text)
    result=dict(inputs={str((HERE/n).relative_to(ROOT)):sha(HERE/n) for n in
                        ('manifest.json','summary.json','completion.json','evidence-receipt.json','control-receipt.json')},
                sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},
                artifacts={n:sha(HERE/n) for n in ('README.md','probes.csv') if (HERE/n).exists()},
                native_predictions=0,observed_fit_starts=0,original_labels_changed=False,
                failed_diagnostic_identities=failures)
    (HERE/'report-receipt.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(completed=successes,native_evaluations=summary['native_evaluations'],
                         ordinary_full_pass=old_pass,extended_full_pass=wide_pass,
                         fresh_extended_full_pass=fresh_pass,internal_mantissa_bits=bits)))


if __name__=='__main__':
    main()
