# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved synthetic fits only; never import a worker or run an optimizer."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def audit(payload,limits):
    parameters=[]; fits=[]; dominant=Counter()
    for row in payload['results']:
        fit=row.get('fit')
        if not fit:
            fits.append(dict(identity=row['identity'],completed=False,error=row.get('error','missing fit')))
            continue
        for name,truth in row['truth'].items():
            value=fit['parameters'].get(name); limit=limits.get(name)
            if value is None or limit is None or not all(math.isfinite(x) for x in (value,truth,limit)) or limit<=0:
                raise ValueError('complete finite truth, fitted calibration and bounds required')
            parameters.append(dict(identity=row['identity'],parameter=name,truth=truth,fitted=value,
                error=value-truth,error_bound_units=(value-truth)/limit,
                at_bound=name in fit['active_bounds']))
        singular=fit['singular_values']
        if not singular or not all(math.isfinite(x) and x>0 for x in singular):
            raise ValueError('positive saved singular values required for this control audit')
        weak=fit.get('right_singular_vectors')
        direction=dict(zip(fit['active_parameters'],weak[-1])) if weak else {}
        leader=max(direction,key=lambda name:abs(direction[name])) if direction else None
        if leader: dominant[leader]+=1
        fits.append(dict(identity=row['identity'],completed=fit['converged'],
            numerical_rank=sum(x>singular[0]*1e-7 for x in singular),
            parameter_count=len(singular),condition_number=singular[0]/singular[-1],
            weak_direction=direction,weak_direction_dominant=leader,
            active_bounds=fit['active_bounds'],prediction_passed=row['passed'],
            maximum_position_error_m=row['maximum_position_error_m']))
    return dict(parameter_rows=parameters,fit_rows=fits,
        largest_normalized_parameter_error=max(abs(p['error_bound_units']) for p in parameters),
        weak_direction_dominant_counts=dict(dominant),native_sweeps=0,observed_fit_starts=0,
        numerical_rank_cutoff_relative=1e-7,full_archival_calibration_qualified=False)


def build():
    # Use the original source hash to justify reading its explicit bound constants.
    from lll import ilvis0_geographic_controls as controls
    receipt=json.loads((HERE/'report-receipt.json').read_text())
    for name,expected in receipt['artifacts'].items():
        if sha(HERE/name)!=expected: raise ValueError('original report artifact changed')
    source=Path(controls.__file__).resolve()
    if receipt['sources'][str(source)]!=sha(source): raise ValueError('original control bounds changed')
    payload=json.loads((HERE/'summary.json').read_text()); result=audit(payload,controls.LIMITS)
    (HERE/'calibration-audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    with (HERE/'calibration-errors.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(result['parameter_rows'][0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(result['parameter_rows'])
    table=[]
    for model in ('sphere_rotating','sphere_still','flat_still'):
        for clock in ('nominal','variable'):
            prefix=model+'::'+clock+'::'
            rows=[p for p in result['parameter_rows'] if p['identity'].startswith(prefix) and p['parameter']=='gyro_bias_z']
            fits=[f for f in result['fit_rows'] if f['identity'].startswith(prefix)]
            truth=rows[0]['truth']*648000/math.pi
            values=[p['fitted']*648000/math.pi for p in rows]
            at_bound=sum(p['at_bound'] for p in rows)
            table.append(f"| {model} | {clock} | {truth:.3f} | {min(values):.6f}–{max(values):.6f} | {at_bound}/4 | {min(f['condition_number'] for f in fits):.3g} |")
    verified=[f for f in result['fit_rows'] if f['weak_direction']]
    minimum_bias=min(abs(f['weak_direction']['gyro_bias_z']) for f in verified)
    boundary=sum(p['at_bound'] for p in result['parameter_rows'] if p['parameter']=='gyro_bias_z')
    text=f'''# Calibration audit of the geographic controls

**All 24 fits reconstruct the known tracks, but they do not accurately recover every
calibration parameter.** Z gyro offset is the main weak direction. This saved-result
audit adds no fits or navigation predictions and leaves the original controls frozen.
See the [prediction and convergence results](README.md).

| True model | Construction | True Z offset (°/hour) | Fitted Z offset range (°/hour) | Fits at offset bound | Smallest fit condition number |
|---|---|---:|---:|---:|---:|
{chr(10).join(table)}

The interior controls inject +0.25°/hour Z offset. Their fitted offsets differ by up
to **{result['largest_normalized_parameter_error']:.6g}°/hour**, despite track errors below
6 micrometres. The near-boundary controls inject +0.99°/hour; **{boundary}/24 fits** reach
the permitted +1°/hour limit. Values are known software injections and allowances,
not manufacturer performance or measurements of NASA calibration.

The six-parameter tangents have condition numbers around ten million. At the saved
reference points, five of six fixtures have numerical rank five under the declared
relative 10⁻⁷ cutoff; one has rank six. All singular values remain nonzero. This is a
cutoff-dependent conditioning diagnostic, not proof of an exact algebraic degeneracy.

All 12 verified-solver fits preserve their weakest right singular vector. Each is
dominated by Z gyro offset, whose absolute normalized component is at least
{minimum_bias:.6f}. A much smaller change in gyro gain accompanies it. These vectors
use parameter-bound units; they are not physical correlations or uncertainty intervals.
The original solver's saved records do not include these vectors, so none are invented.

## Implication

Numerical convergence and accurate predictions are insufficient to establish unique
calibration. In these short, straight equatorial tracks, offset is weakly constrained;
small finite-interval integration errors can move its best-fitting value substantially.
Both solvers return closely agreeing predictions and offsets. This is not evidence
that the NASA instrument drifts by this amount, nor does it identify the cause of its
Z-axis boundaries. The controls use known continuous increments and a midpoint
navigation approximation, rather than reproducing all instrument coning/sculling details.

The next useful control is a predefined integration-resolution and gyro-offset/gain
study: hold the analytic trajectory, receiver epochs and physical calibration fixed,
reduce the increment interval, and compare offset recovery and objective valleys.
Also test longer, more informative geometry and independently fitted initialization.
Preserve this 24-fit result; use a new source/configuration identity and finite allowance
for further numerical controls. Observed gain–bias profiles remain a separate budget.

Reproduce this metadata-only audit:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-geographic-controls-20261011/audit_calibration.py
```
'''
    (HERE/'CALIBRATION.md').write_text(text)
    inputs={n:sha(HERE/n) for n in ('summary.json','manifest.json','report-receipt.json')}
    sources=[Path(__file__),source,HERE.parents[1]/'analysis/tests/test_ilvis0_geographic_calibration_audit.py']
    derived=dict(inputs=inputs,sources={str(p.resolve()):sha(p) for p in sources},
        artifacts={n:sha(HERE/n) for n in ('CALIBRATION.md','calibration-errors.csv','calibration-audit.json')},
        observed_fit_starts=0,native_sweeps=0)
    (HERE/'calibration-receipt.json').write_text(json.dumps(derived,sort_keys=True,indent=2)+'\n')
    return dict(audited_fits=len(result['fit_rows']),offset_boundary_count=boundary,
        worst_offset_error_dph=result['largest_normalized_parameter_error'],native_sweeps=0,observed_fit_starts=0)


if __name__=='__main__': print(json.dumps(build(),sort_keys=True))
