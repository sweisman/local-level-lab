# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish a saved-diagnostic audit; no optimizer or native kernel imports."""
import csv
import hashlib
import json
from pathlib import Path

from lll import ilvis0_saved_audit as saved
from lll import ilvis0_solver_diagnosis as diagnosis

HERE=Path(__file__).resolve().parent
CURRENT=HERE.parent/'ilvis0-unit-scale-trial-20261011'
BASELINE=HERE.parent/'ilvis0-prediction-trial-20261011'


def load(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def publication(directory):
    saved.verify_artifacts(directory,load(directory/'evidence-receipt.json'))
    completion=load(directory/'completion.json')
    if (completion.get('state')!='complete' or completion.get('starts')!=6 or
        completion.get('summary_sha256')!=sha(directory/'summary.json') or
        completion.get('manifest_sha256')!=sha(directory/'manifest.json')):
        raise ValueError('invalid completed publication')
    return load(directory/'summary.json'),load(directory/'manifest.json')


def index(summary):
    rows={}
    for case in summary['cases']:
        for fit in case['fits']:
            key=case['case_id'],fit['model']
            if key in rows: raise ValueError('duplicate fit identity')
            rows[key]=fit
    expected={(case,model) for case in ('bias1_unsubtracted','bias1_profiled_removal')
        for model in ('sphere_rotating','sphere_still','flat_still')}
    if set(rows)!=expected: raise ValueError('unexpected saved fit population')
    return rows


def write_csv(path,rows):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def build(output=HERE,current=CURRENT,baseline=BASELINE):
    output,current,baseline=map(Path,(output,current,baseline))
    new,manifest=publication(current); old,old_manifest=publication(baseline)
    for key in ('cases','clock','initialization','split_policy','covariance_policy'):
        if manifest.get(key)!=old_manifest.get(key): raise ValueError('unmatched scientific scope')
    if new['split']!=old['split']: raise ValueError('unmatched receiver split')
    a,b=index(new),index(old)
    fits=[]; parameters=[]; modes=[]; histories=[]
    cases={c['case_id']:c for c in manifest['cases']}
    for key,f in a.items():
        if f['active_parameters']!=b[key]['active_parameters']:
            raise ValueError('unmatched parameter definitions')
        fits.append(diagnosis.inspect_fit(f,b[key],key[0]))
        p,m=diagnosis.parameter_diagnostics(f)
        case=cases[key[0]]
        physical=saved.parameter_rows(f,case['limits'],profile=case['profile'])
        prior=saved.parameter_rows(b[key],case['limits'],profile=case['profile'])
        for row,value,before in zip(p,physical,prior):
            parameters.append(dict(case_id=key[0],model=key[1],**row,
                unit=value['unit'],physical_value=value['value'],baseline_value=before['value'],
                physical_change=value['value']-before['value'],baseline_boundary=before['boundary']))
        modes.extend(dict(case_id=key[0],model=key[1],**row) for row in m)
        histories.extend(dict(case_id=key[0],model=key[1],**row) for row in f['accepted_step_history'])
    inputs={str((p/n).resolve()):sha(p/n) for p in (current,baseline)
        for n in ('summary.json','manifest.json','completion.json','evidence-receipt.json')}
    table='\n'.join(f"| {r['case_id']} | {r['model']} | {r['status']} | "
        f"{r['baseline_stationarity_ratio']:.3g} → {r['stationarity_ratio']:.3g} | "
        f"{r['first_three_stable_evaluation'] or 'none'} | {r['terminal_stable_callbacks']} |"
        for r in fits)
    target=next(r for r in fits if r['case_id']=='bias1_profiled_removal' and r['model']=='flat_still')
    names=('gyro_bias_z','gyro_gain_z','gravity_delta')
    boundary_table='\n'.join(f"| {name} | "
        f"{sum(r['parameter']==name and r['boundary']!='interior' for r in parameters)}/6 |"
        for name in names)
    weak=[r for r in modes if r['case_id']==target['case_id'] and r['model']==target['model'] and r['weak_rank']==1]
    top=sorted(weak,key=lambda r:abs(r['loading']),reverse=True)[:5]
    weak_text=', '.join(f"{r['parameter']} ({abs(r['loading']):.3f})" for r in top)
    text=f'''# Why the final flat-disc fit is still unfinished

**The fixed-scale solver reached a nearly stationary flat-disc fit, but did not complete
its required stopping procedure.** All five previously completed fits stayed completed
with closely matched objectives. The sixth remains unfinished; this audit changes no labels.

An **IMU (inertial measurement unit)** records turning and acceleration. This audit reads
the saved results from the same IMU-type-21 recording used in the prediction trial:
2015-10-05, 7.30 minutes, median ground speed 878.1 km/h. No original measurements are
reprocessed. It performs **zero optimizer starts and zero native predictions**.

## What improved and what did not

The unfinished flat-disc fit's stationarity ratio fell from
**{target['baseline_stationarity_ratio']:.2f}** times the permitted threshold to
**{target['stationarity_ratio']:.3g}**. Its fresh scaled projected gradient was about
9.35 × 10⁻¹⁰, below the unchanged 10⁻⁴ threshold. The training cost changed from
{target['baseline_training_cost']:.6f} to {target['training_cost']:.6f}, a
{abs(target['relative_objective_change'])*100:.4f}% decrease. A small gradient describes
local first-order stationarity within the permitted box; it does not prove a global optimum,
unique calibration, adequate observations or statistical significance.

SciPy did not report successful termination before the 200-evaluation allowance ended.
The last recorded callback was at evaluation {target['last_callback_evaluation']}; its cost
matches the fresh final point. It met the measurement-step and cost-change stability
thresholds, but only **one** consecutive recorded callback met both. The earlier step
changed the residual vector by about 6.15 × 10⁻⁵, above the 10⁻⁶ stability threshold.
Three consecutive stable callbacks were not recorded. The intervening evaluation count
does not establish additional accepted steps or stability.

The replay below uses the already published three-step diagnostic thresholds. It is a
historical diagnostic, not evidence that a different stopping rule would have terminated
these fits at these exact points.

| Processing case | Model | Saved status | Stationarity / threshold: old → new | First three stable callbacks: evaluation | Stable callbacks at end |
|---|---|---|---:|---:|---:|
{table}

Some successful SciPy stops have fewer than three stable callbacks. Their original
convergence criterion was SciPy success plus the fresh stationarity check; the replay
neither invalidates those saved results nor promotes the unfinished one.

## Calibration and weak directions

| Calibration parameter | New fits at a permitted limit |
|---|---:|
{boundary_table}

The unfinished fit has {target['parameters_at_limits']} parameters at limits. Its full
Jacobian condition ratio is about {target['jacobian_condition_ratio']:.3g} in normalized
parameter coordinates. Its weakest direction mixes {weak_text}. These are absolute
loadings; the overall sign of a singular vector is arbitrary. The full direction is
blocked by box limits in {'both signs' if not weak[0]['positive_direction_feasible'] and not weak[0]['negative_direction_feasible'] else 'at least one sign'}.
Full-Jacobian conditioning therefore cannot be read as feasible parameter uncertainty.
Repeated limit saturation still requires a calibration/observation adequacy explanation.
Numerical completion alone cannot settle it.

[Fit diagnostics](fit-diagnostics.csv), [signed parameter changes](parameter-diagnostics.csv),
[three weakest directions per fit](weak-directions.csv) and
[complete recorded callback histories](callback-history.csv) preserve the details.
The [original prediction audit](../ilvis0-prediction-audit-20261011/README.md) documents
the Z gain reversal between whole-stretch and training-only fitting.

## Next numerical test

The evidence supports testing termination based on scaled stationarity **with an
independent stability verification**, rather than treating SciPy's unscaled stopping
flag as the only successful exit. It does not justify gradient-only acceptance, an
automatic budget extension, looser physical bounds or relabeling completed studies.
See [the proposed stopping-rule test](STOPPING_PLAN.md). Qualify that implementation on
known-optimum and false-stop controls before requesting a separate bounded airborne trial.
Do not advance the current fixed-scale candidate to recording replication.

The completed no-removal prediction comparison favors globe. The full comparison
remains unresolved because the removal-allowed flat-disc fit is unfinished. That failure
is not equal support for flat and globe. Rotation remains withheld by the existing hierarchy.

To reproduce this report from saved evidence:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-solver-diagnosis-20261011/build_report.py
```
'''
    output.mkdir(parents=True,exist_ok=True)
    for name,rows in (('fit-diagnostics.csv',fits),('parameter-diagnostics.csv',parameters),
                      ('weak-directions.csv',modes),('callback-history.csv',histories)):
        write_csv(output/name,rows)
    payload=dict(version=diagnosis.VERSION,diagnostic_policy=diagnosis.POLICY,fits=fits,
        optimizer_starts=0,native_predictions=0,saved_statuses_unchanged=True,
        scientific_decision='abstain',parameter_uncertainty_estimated=False)
    (output/'summary.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    (output/'README.md').write_text(text)
    artifacts={n:sha(output/n) for n in ('README.md','summary.json','fit-diagnostics.csv',
        'parameter-diagnostics.csv','weak-directions.csv','callback-history.csv')}
    sources={str(p.resolve()):sha(p) for p in
        (Path(__file__),Path(diagnosis.__file__),Path(saved.__file__))}
    receipt=dict(version=diagnosis.VERSION,inputs=inputs,sources=sources,artifacts=artifacts,
        optimizer_starts=0,native_predictions=0)
    (output/'report-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    return payload


if __name__=='__main__':
    build()
    print('Saved solver diagnosis published; zero optimizer starts or native predictions.')
