# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explain completed stopping evidence using saved metadata only."""
import importlib.util
import json
from pathlib import Path

from lll import ilvis0_solver_diagnosis as diagnosis

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prior_saved_diagnosis',
    HERE.parent/'ilvis0-solver-diagnosis-20261011/build_report.py')
prior=importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)


def probe_row(probe):
    row=dict(probe_passed=None,probe_reason='not_attempted',
        predicted_cost_change_ratio=None,predicted_residual_step_ratio=None,
        fresh_nonlinear_probe_recorded=False)
    if probe is None: return row
    if not isinstance(probe.get('passed'),bool): raise ValueError('invalid probe result')
    reason=probe.get('reason')
    allowed={'not_stationary','local_linear_solve_unfinished',
        'linear_correction_not_stable','fresh_stability_verified','fresh_probe_not_stable'}
    if reason not in allowed: raise ValueError('unknown probe reason')
    row.update(probe_passed=probe['passed'],probe_reason=reason)
    if reason in ('not_stationary','local_linear_solve_unfinished'):
        if probe['passed']: raise ValueError('unfinished probe marked passed')
        return row
    cost=diagnosis.finite(probe.get('predicted_cost_change'),True)/diagnosis.POLICY['relative_cost_change']
    step=diagnosis.finite(probe.get('predicted_residual_step'),True)/diagnosis.POLICY['relative_residual_step']
    row.update(predicted_cost_change_ratio=cost,predicted_residual_step_ratio=step)
    if reason=='linear_correction_not_stable':
        if probe['passed'] or cost<=1 and step<=1:
            raise ValueError('inconsistent linear stability rejection')
        return row
    if cost>1 or step>1: raise ValueError('fresh probe after failed linear check')
    actual_cost=diagnosis.finite(probe.get('actual_cost_change'),True)/diagnosis.POLICY['relative_cost_change']
    actual_step=diagnosis.finite(probe.get('actual_residual_step'),True)/diagnosis.POLICY['relative_residual_step']
    gradient=diagnosis.finite(probe.get('fresh_stationarity'),True)/diagnosis.POLICY['stationarity']
    passed=actual_cost<=1 and actual_step<=1 and gradient<=1
    if passed!=probe['passed'] or (reason=='fresh_stability_verified')!=passed:
        raise ValueError('inconsistent fresh stability result')
    row['fresh_nonlinear_probe_recorded']=True
    return row


def build(output=HERE):
    paths=[HERE.parent/name for name in ('ilvis0-verified-stop-trial-20261011',
        'ilvis0-unit-scale-trial-20261011','ilvis0-prediction-trial-20261011')]
    publications=[prior.publication(p) for p in paths]
    summary,manifest=publications[0]; current=prior.index(summary)
    previous=prior.index(publications[1][0]); original=prior.index(publications[2][0])
    for old,old_manifest in publications[1:]:
        for key in ('cases','clock','initialization','split_policy','covariance_policy'):
            if manifest.get(key)!=old_manifest.get(key): raise ValueError('unmatched scientific scope')
        if summary['split']!=old['split']: raise ValueError('unmatched receiver split')
    fits=[]; parameters=[]; modes=[]
    cases={c['case_id']:c for c in manifest['cases']}
    for key,fit in current.items():
        if fit['active_parameters']!=previous[key]['active_parameters'] or fit['active_parameters']!=original[key]['active_parameters']:
            raise ValueError('unmatched parameter definitions')
        row=diagnosis.inspect_fit(fit,previous[key],key[0])
        row.update(termination=fit['termination'],**probe_row(fit.get('stability_probe')))
        row['original_training_cost']=original[key]['residual_sum_squares']
        row['original_status']=prior.saved.fit_status(original[key])
        fits.append(row)
        p,m=diagnosis.parameter_diagnostics(fit)
        case=cases[key[0]]
        physical=prior.saved.parameter_rows(fit,case['limits'],profile=case['profile'])
        for a,b in zip(p,physical):
            parameters.append(dict(case_id=key[0],model=key[1],**a,
                physical_value=b['value'],unit=b['unit']))
        modes.extend(dict(case_id=key[0],model=key[1],**r) for r in m)
    target=next(r for r in fits if r['case_id']=='bias1_profiled_removal' and r['model']=='flat_still')
    if target['status']!='unresolved' or target['probe_reason']!='linear_correction_not_stable':
        raise ValueError('unexpected outcome for this completed diagnostic')
    matched=[r for r in fits if r['original_status']=='converged']
    worst=max((r['training_cost']-r['original_training_cost'])/max(r['original_training_cost'],1.) for r in matched)
    weak=[r for r in modes if r['case_id']==target['case_id'] and r['model']==target['model'] and r['weak_rank']==1]
    top=sorted(weak,key=lambda r:abs(r['loading']),reverse=True)[:5]
    loadings=', '.join(f"{r['parameter']} ({abs(r['loading']):.3f})" for r in top)
    table='\n'.join(f"| {r['case_id']} | {r['model']} | {r['status']} | {r['termination']} | {r['stationarity_ratio']:.3g} |" for r in fits)
    text=f'''# Completed stopping trial: why the sixth fit remains unfinished

**Five of six fits completed. The verified-stopping revision did not qualify.**
The remaining stationary-disc fit reached a nearly stationary point, but its bounded
local stability check failed the declared measurement-step limit. No saved fit is relabeled.

An **IMU (inertial measurement unit)** measures turning and acceleration. This audit
uses saved results from the same 7.30-minute IMU21 control, median ground speed
878.1 km/h. It performs **zero optimizer starts and zero native predictions**.

## Exact stopping evidence

The unfinished fit's stationarity ratio is **{target['stationarity_ratio']:.3g}**
against the unchanged 10⁻⁴ projected-gradient threshold. Its saved final cost and
gradient match the previous fixed-scale attempt. The last accepted callback is at
evaluation {target['last_callback_evaluation']}; only {target['terminal_stable_callbacks']}
terminal callback passes both cost and residual-step stability checks. Three are required
for the callback exit. SciPy did not report successful termination.

The additional bounded linear correction predicts a relative cost change of
**2.4148 × 10⁻¹²**, far below the 10⁻⁸ cost limit. However, its relative residual-vector
step is **1.5541 × 10⁻⁶**, or **{target['predicted_residual_step_ratio']:.4f} times**
the 10⁻⁶ step limit. The fresh nonlinear probe was therefore not attempted. A failed
linear screen is not evidence that a fresh nonlinear probe would fail or pass.

Cost and residual-vector movement measure different things: individual errors can change
while their squared sum barely changes. A tiny gradient or cost change alone cannot
replace the declared combined stopping rule. The trial used 736 evaluations, including
prediction diagnostics, and about 35.6 minutes. The allowance is spent; no retry is authorized.

| Processing case | Model | Saved status | Exit | Stationarity / threshold |
|---|---|---|---|---:|
{table}

All five originally completed fits remain completed. Their largest relative training-cost
increase is {worst*100:.5g}%, below the declared 0.1% agreement limit. Qualification
failed because the sixth fit remains unfinished, not because those five worsened.

## Calibration and interpretation

The unfinished fit retains {target['parameters_at_limits']} parameters at limits and a
full-Jacobian condition ratio of {target['jacobian_condition_ratio']:.3g}. Its weakest
direction mixes {loadings}. These normalized loadings describe a local full-Jacobian
direction, not feasible confidence limits or a physical calibration measurement.

The completed no-removal prediction comparison still favors globe. The removal-allowed
comparison remains unfinished, and rotation is withheld for the combined comparison.
An unfinished flat fit does not provide positive flat-Earth evidence. Numerical stopping
does not settle the separate clock, calibration or uncertainty questions.

[Fit checks](fit-diagnostics.csv), [parameter values](parameter-diagnostics.csv),
and [weak directions](weak-directions.csv) preserve the saved numerical evidence.
The [matched results](../ilvis0-verified-stop-trial-20261011/RESULTS.md) retain track
errors and the scientific status.

## What to do next

Do not loosen the stability threshold merely because this result misses it by a factor
of 1.55. Do not rerun the same failed identity or extend the completed allowance.
Prepare independent physical controls for the calibration/timing interaction and
alternative numerical strategies. In parallel, audit existing timestamp and residual
evidence as specified in the [focused diagnostic plan](../ILVIS0_DIAGNOSTIC_PLAN.md).
Joint Z gain–offset profiles and any fresh observed test require their own finite scope.
Recording replication and a corpus rerun remain deferred.

Reproduce this saved-data audit without fitting:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-verified-stop-diagnosis-20261011/build_report.py
```
'''
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    for name,rows in (('fit-diagnostics.csv',fits),('parameter-diagnostics.csv',parameters),('weak-directions.csv',modes)):
        prior.write_csv(output/name,rows)
    payload=dict(version='ilvis0-verified-stop-saved-diagnosis-v1',fits=fits,
        optimizer_starts=0,native_predictions=0,saved_statuses_unchanged=True,
        qualification_passed=False,scientific_decision='abstain')
    (output/'summary.json').write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
    (output/'README.md').write_text(text)
    names=('README.md','summary.json','fit-diagnostics.csv','parameter-diagnostics.csv','weak-directions.csv')
    receipt=dict(version=payload['version'],optimizer_starts=0,native_predictions=0,
        inputs={str((p/n).resolve()):prior.sha(p/n) for p in paths for n in
            ('summary.json','manifest.json','completion.json','evidence-receipt.json')},
        sources={str(p.resolve()):prior.sha(p) for p in
            (Path(__file__),Path(prior.__file__),Path(diagnosis.__file__),Path(prior.saved.__file__))},
        artifacts={n:prior.sha(output/n) for n in names})
    (output/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    return payload


if __name__=='__main__':
    build()
    print('Verified-stop diagnosis published; zero starts and zero native predictions.')
