# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite independent controls; package-only never starts an optimizer."""
import argparse
import csv
import fcntl
import hashlib
import json
import os
import platform
from pathlib import Path

import numpy as np
import scipy

from lll import ilvis0_geographic_controls as controls
from lll import ilvis0_estimator as estimator, ilvis0_exploratory as explore
from lll import ilvis0_forward as forward, ilvis0_shape as shape
from lll import ilvis0_solver_verified_stop as verified, ilvis0_solver_refinement as refinement

HERE=Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,payload):
    temporary=path.with_suffix(path.suffix+'.partial')
    with temporary.open('w') as stream:
        json.dump(payload,stream,sort_keys=True,indent=2,allow_nan=False); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


def identities():
    return [(model,clock,strategy,start) for model in explore.MODELS
        for clock in ('nominal','variable') for strategy in ('original','verified')
        for start in ('zero','opposed')]


def identity(parts): return '::'.join(parts)


def check_fixture(f,kernel,tangent):
    p=controls.problem(f,kernel,tangent); point=controls.truth_point(f,p)
    predicted,jac,boundaries=p.prediction_tangent(point,f['model'])
    value=p.predict(point,f['model'])
    difference=float(np.max(abs((value-predicted)*f['metric'])))
    error=controls.position_error(f,predicted); derivative=0.
    for k in range(len(point)):
        step=np.eye(len(point))[k]*1e-3
        # Near-boundary truths still have sufficient support for both differences.
        fd=(p.predict(point+step,f['model'])-p.predict(point-step,f['model'])).ravel()/2e-3
        derivative=max(derivative,float(np.max(abs((fd-jac[:,k]).reshape(-1,3)*f['metric']))))
    _,white,_=p.residual_tangent(point,f['model'])
    singular=np.linalg.svd(white,compute_uv=False)
    return dict(identity=f"{f['model']}::{f['clock']}",native_sweeps=15,
        maximum_truth_position_error_m=error,maximum_value_tangent_difference_m=difference,
        maximum_derivative_difference_m_per_bound_unit=derivative,
        singular_values=singular.tolist(),relative_1e_7_rank=int(np.sum(singular>singular[0]*1e-7)),
        condition_number=float(singular[0]/singular[-1]),receiver_epochs_at_boundaries=boundaries,
        passed=bool(error<.002 and difference<1e-6 and derivative<2e-5 and boundaries==0))


def run():
    HERE.mkdir(parents=True,exist_ok=True)
    with (HERE/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (HERE/'completion.json').exists(): raise ValueError('completed controls are frozen; use --package-only')
        kernel,build=explore.load_kernel(HERE/'kernel')
        tangent,tangent_build=shape.load_tangent(HERE/'kernel')
        sources=[Path(__file__),HERE/'PLAN.md',Path(controls.__file__),Path(estimator.__file__),
            Path(explore.__file__),Path(shape.__file__),Path(forward.__file__),
            Path(verified.__file__),Path(refinement.__file__),
            Path(explore.__file__).with_name('ilvis0_native.c'),
            Path(shape.__file__).with_name('ilvis0_tangent.cpp'),
            HERE.parents[1]/'analysis/tests/test_ilvis0_geographic_controls.py']
        manifest=dict(version=controls.VERSION,environment=dict(python=platform.python_version(),
            numpy=np.__version__,scipy=scipy.__version__,threads={k:os.environ.get(k) for k in
                ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}),
            sources={str(p.resolve()):sha(p) for p in sources},value_kernel=build,tangent_kernel=tangent_build,
            identities=[identity(x) for x in identities()],maximum_fit_sweeps=4800,
            maximum_fixture_sweeps=90,observed_fit_starts=0)
        if (HERE/'manifest.json').exists():
            if json.loads((HERE/'manifest.json').read_text())!=manifest:
                raise ValueError('control source/configuration/environment changed; cannot resume')
        else: save(HERE/'manifest.json',manifest)
        digest=sha(HERE/'manifest.json')
        journal=HERE/'starts.jsonl'
        records=[json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
        if (any(r['manifest_sha256']!=digest or r['start']!=i+1 for i,r in enumerate(records))
            or len({r['identity'] for r in records})!=len(records)
            or any(r['identity'] not in manifest['identities'] for r in records)):
            raise ValueError('invalid start journal')
        charged={r['identity'] for r in records}
        checks=[]
        for model in explore.MODELS:
            for clock in ('nominal','variable'):
                target=HERE/f'check-{model}-{clock}.json'
                if target.exists(): row=json.loads(target.read_text())
                else:
                    row=check_fixture(controls.fixture(model,clock),kernel,tangent); save(target,row)
                checks.append(row)
        if not all(r['passed'] for r in checks): raise ValueError('independent fixture validation failed; no fits started')
        rows=[]
        for parts in identities():
            model,clock,strategy,start=parts; task=identity(parts)
            target=HERE/(task.replace('::','-')+'.json')
            if target.exists(): row=json.loads(target.read_text())
            elif task in charged:
                row=dict(identity=task,passed=False,error='interrupted charged start; no retry',observed_fit_starts=0)
                save(target,row)
            else:
                if any(sha(path)!=expected for path,expected in manifest['sources'].items()):
                    raise ValueError('source changed during controls')
                record=dict(start=len(records)+1,identity=task,manifest_sha256=digest,maximum_sweeps=200)
                with journal.open('a') as stream:
                    stream.write(json.dumps(record,sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
                records.append(record); charged.add(task)
                try: row=controls.run_fit(controls.fixture(model,clock),kernel,tangent,strategy=strategy,start_id=start)
                except Exception as error:
                    row=dict(identity=task,passed=False,error=f'{type(error).__name__}: {error}',observed_fit_starts=0)
                save(target,row)
            rows.append(row)
            print(json.dumps(dict(identity=task,passed=row['passed'],
                sweeps=row.get('actual_tangent_sweeps'),position_error_m=row.get('maximum_position_error_m'))),flush=True)
        payload=dict(version=controls.VERSION,manifest_sha256=digest,fixture_checks=checks,results=rows,
            observed_fit_starts=0,full_archival_solver_qualified=False)
        save(HERE/'summary.json',payload)
        save(HERE/'completion.json',dict(manifest_sha256=digest,summary_sha256=sha(HERE/'summary.json'),
            charged_starts=len(records),passed=sum(r['passed'] for r in rows),total=len(rows)))
    return package()


def package():
    completion=json.loads((HERE/'completion.json').read_text())
    if completion['summary_sha256']!=sha(HERE/'summary.json') or completion['manifest_sha256']!=sha(HERE/'manifest.json'):
        raise ValueError('completed control hash mismatch')
    payload=json.loads((HERE/'summary.json').read_text()); rows=payload['results']
    table=[]; csv_rows=[]
    for row in rows:
        fit=row.get('fit',{})
        values=dict(identity=row['identity'],passed=row['passed'],converged=fit.get('converged',False),
            objective=fit.get('residual_sum_squares'),truth_objective=row.get('truth_objective'),
            maximum_position_error_m=row.get('maximum_position_error_m'),
            maximum_normalized_parameter_error=row.get('maximum_normalized_parameter_error'),
            tangent_sweeps=row.get('actual_tangent_sweeps'),value_sweeps=row.get('actual_value_sweeps'),
            active_bounds=';'.join(fit.get('active_bounds',[])),error=row.get('error',''))
        csv_rows.append(values)
    with (HERE/'fits.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(csv_rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(csv_rows)
    for model in explore.MODELS:
        for clock in ('nominal','variable'):
            matched=[r for r in rows if r['identity'].startswith(f'{model}::{clock}::')]
            for strategy in ('original','verified'):
                chosen=[r for r in matched if f'::{strategy}::' in r['identity']]
                errors=[r['maximum_position_error_m'] for r in chosen if 'maximum_position_error_m' in r]
                sweeps=sum(r.get('actual_tangent_sweeps',0)+r.get('actual_value_sweeps',0) for r in chosen)
                table.append(f"| {model} | {clock} | {strategy} | {sum(r['passed'] for r in chosen)}/2 | {max(errors) if errors else 'unavailable'} | {sweeps} |")
    checks=payload['fixture_checks']; passed=sum(r['passed'] for r in rows)
    max_error=max(r['maximum_position_error_m'] for r in rows if 'maximum_position_error_m' in r)
    parameter=max(r['maximum_normalized_parameter_error'] for r in rows if 'maximum_normalized_parameter_error' in r)
    sweeps=sum(r.get('actual_tangent_sweeps',0)+r.get('actual_value_sweeps',0) for r in rows)+sum(r['native_sweeps'] for r in checks)
    text=f'''# Independent geographic fitter controls

**{passed}/24 controls passed the predefined numerical checks.** These are synthetic
software controls, not additional NASA findings. They exercise the native geographic
predictor, its automatic derivatives, receiver timing and both nonlinear solvers.
There were zero observed-data fit starts. The failed observed stopping-rule trial
and the 53-stretch first-pass findings remain unchanged.

An **IMU (inertial measurement unit)** measures turning and acceleration. Here its
three-axis increments come from independently specified continuous motion, not the
production predictor. The receiver's positions are separately generated at known
times. The fitter must reconstruct those observations while estimating calibration,
initialization and latency. See the [predefined plan](PLAN.md).

## What was tested

The six physical fixtures cover rotating globe, still globe and stationary disc,
each with a known 12-second equatorial eastward track at 220 m/s and 1,000 m altitude.
Body pitch and yaw vary smoothly. Eight-point Gaussian quadrature integrates the
analytic body angular rate and specific force. Receiver positions follow the appropriate
analytic coordinate metric; neither navigation kernel generates the input data.
Receiver epochs fall between packets, with independently specified latency.

Each model has constant-period/interior and variable-period/near-boundary cases.
Variable periods have a known 50 ppm modulation; this is a different physical clock
construction, not applying two clocks to the same observations. A separate test
deliberately applies an incorrect clock scale and confirms a position discrepancy.
This does not identify the period represented by NASA's logged increments.

Six nuisance parameters are free: initial pitch, initial eastward velocity, Z gyro
offset and gain, gravity correction and receiver latency. Other nuisance parameters
are fixed to their known synthetic values, including no upstream Earth-rate removal.
The same box and observations are used for both solvers. Each fixture is fitted from
zero and an opposed starting point. The common synthetic position scale is 1 cm,
with no random noise. Prediction tolerance is 2 mm; objective tolerance above the
known-parameter reference is 0.01. These are software checks, not significance levels.

## Results

| True model | Construction | Solver | Passed | Largest position error (m) | Native sweeps |
|---|---|---|---:|---:|---:|
{chr(10).join(table)}

The largest returned-track error is **{max_error:.6g} m**. Finite-interval navigation
uses a midpoint approximation, so exact continuous input integration has a small
nonzero reference error. All fitted objectives and reference errors are retained in
[fits.csv](fits.csv), with complete fit diagnostics in the saved report artifacts.

At the known parameters, the largest reference position error is
{max(r['maximum_truth_position_error_m'] for r in checks):.6g} m. The two native
implementations agree to {max(r['maximum_value_tangent_difference_m'] for r in checks):.3g} m.
Automatic derivatives agree with separate central value differences within
{max(r['maximum_derivative_difference_m_per_bound_unit'] for r in checks):.3g} m per normalized
parameter unit. All six fixtures have off-packet receiver epochs. Conditioning and
singular values are saved; a numerical rank cutoff is not scientific identifiability.

The largest parameter difference from the injected reference is {parameter:.6g}
in units of its bound. Calibration recovery must be assessed separately from prediction
recovery: discretization error and weakly constrained parameters can shift the best fit.
No claim of uniquely recovered instrument calibration or global optimality is made.

The report charged exactly 24 starts, with no retries. There were **{sweeps} native
sweeps**, including independent fixture checks and final prediction checks, within
the declared finite allowance. Ordinary unit-test invocations are separate from this
report's ledger. All results, including failures if any, are retained.

## What remains

These short six-parameter equatorial controls do not qualify every nuisance direction
in the 27-parameter archival fit, long-record conditioning, alternative processing or
independent-flight prediction. Nor do they explain the NASA Z gain/offset boundaries.
Next test the difficult calibration directions and full initialization at a finite
software budget before preparing matched observed gain–bias profiles. Those observed
profiles require a separately approved allowance; no corpus rerun is started here.
See the [focused analysis plan](../ILVIS0_DIAGNOSTIC_PLAN.md).

The public first-pass result remains 12 globe preferences, no completed flat preference
and 41 unresolved stretches. A successful software control does not turn those
exploratory comparisons into calibrated scientific detections.

Rebuild documentation without starting fits:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-geographic-controls-20261011/build_report.py --package-only
```
'''
    (HERE/'README.md').write_text(text)
    manifest=json.loads((HERE/'manifest.json').read_text())
    save(HERE/'report-receipt.json',dict(version=controls.VERSION,manifest_sha256=completion['manifest_sha256'],
        environment=manifest['environment'],sources=manifest['sources'],
        artifacts={n:sha(HERE/n) for n in ('README.md','fits.csv','summary.json','PLAN.md','completion.json')},
        observed_fit_starts=0,full_archival_solver_qualified=False))
    return dict(passed=passed,total=len(rows),native_sweeps=sweeps,observed_fit_starts=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true')
    parser.add_argument('--package-only',action='store_true'); args=parser.parse_args()
    if args.run==args.package_only: parser.error('choose --run or --package-only')
    print(json.dumps(run() if args.run else package(),sort_keys=True))
