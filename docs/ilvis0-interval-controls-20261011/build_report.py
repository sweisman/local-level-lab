# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite interval controls and saved-only publication; no NASA inputs."""
import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
import platform
from pathlib import Path

import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from lll import ilvis0_interval_controls as controls
from lll import ilvis0_geographic_controls as original
from lll import ilvis0_exploratory as explore, ilvis0_shape as shape

HERE=Path(__file__).resolve().parent
REFERENCE=HERE.parent/'ilvis0-geographic-controls-20261011'


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,payload):
    temporary=path.with_suffix(path.suffix+'.partial')
    with temporary.open('w') as stream:
        json.dump(payload,stream,sort_keys=True,indent=2,allow_nan=False); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


def cases():
    return [(model,factor,geometry) for model in explore.MODELS
        for factor,geometry in ((2,'original'),(4,'original'),(4,'roll'))]


def task_id(case): return f'{case[0]}::r{case[1]}::{case[2]}'


def verify_reference():
    receipt=json.loads((REFERENCE/'report-receipt.json').read_text())
    for path,expected in receipt['sources'].items():
        if sha(path)!=expected: raise ValueError('frozen geographic source changed')
    for name,expected in receipt['artifacts'].items():
        if sha(REFERENCE/name)!=expected: raise ValueError('frozen geographic artifact changed')
    return receipt


def baseline():
    payload=json.loads((REFERENCE/'summary.json').read_text())
    rows=[]
    for model in explore.MODELS:
        matches=[r for r in payload['results'] if r['identity']==f'{model}::nominal::original::zero']
        if len(matches)!=1: raise ValueError('unique original interior/zero control required')
        r=matches[0]; p=r['fit']['parameters']; truth=r['truth']
        rows.append(dict(r,model=model,refinement_factor=1,geometry='original',sample_count=2400,
            nominal_increment_interval_s=.005,duration_s=12.,reused=True,
            gyro_bias_z_error_dph=(p['gyro_bias_z']-truth['gyro_bias_z'])*648000/math.pi,
            gyro_gain_z_error=p['gyro_gain_z']-truth['gyro_gain_z']))
    return rows


def run():
    HERE.mkdir(parents=True,exist_ok=True)
    with (HERE/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (HERE/'completion.json').exists(): raise ValueError('completed study is frozen; use --package-only')
        reference=verify_reference()
        kernel,kernel_build=explore.load_kernel(HERE/'kernel')
        tangent,tangent_build=shape.load_tangent(HERE/'kernel')
        if kernel_build!=json.loads((REFERENCE/'manifest.json').read_text())['value_kernel'] or tangent_build!=json.loads((REFERENCE/'manifest.json').read_text())['tangent_kernel']:
            raise ValueError('native builds differ from saved baseline')
        sources=dict(reference['sources'])
        for path in (Path(__file__),HERE/'PLAN.md',Path(controls.__file__),
            HERE.parents[1]/'analysis/tests/test_ilvis0_interval_controls.py'):
            sources[str(path.resolve())]=sha(path)
        manifest=dict(version=controls.VERSION,sources=sources,
            inputs={str((REFERENCE/n).resolve()):sha(REFERENCE/n) for n in
                ('summary.json','manifest.json','report-receipt.json','completion.json')},
            environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                matplotlib=matplotlib.__version__,threads={k:os.environ.get(k) for k in
                    ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}),
            value_kernel=kernel_build,tangent_kernel=tangent_build,identities=[task_id(c) for c in cases()],
            maximum_new_starts=9,maximum_new_sweeps=1809,observed_fit_starts=0)
        if (HERE/'manifest.json').exists():
            if json.loads((HERE/'manifest.json').read_text())!=manifest: raise ValueError('incompatible continuation')
        else: save(HERE/'manifest.json',manifest)
        digest=sha(HERE/'manifest.json'); journal=HERE/'starts.jsonl'
        records=[json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
        if (any(r['manifest_sha256']!=digest or r['start']!=i+1 for i,r in enumerate(records))
            or len({r['identity'] for r in records})!=len(records)
            or any(r['identity'] not in manifest['identities'] for r in records)):
            raise ValueError('invalid start journal')
        charged={r['identity'] for r in records}; rows=baseline()
        for case in cases():
            model,factor,geometry=case; task=task_id(case); target=HERE/(task.replace('::','-')+'.json')
            if target.exists(): row=json.loads(target.read_text())
            elif task in charged:
                row=dict(identity=task,model=model,refinement_factor=factor,geometry=geometry,reused=False,
                    passed=False,error='interrupted charged start; no retry',observed_fit_starts=0)
                save(target,row)
            else:
                for path,expected in {**manifest['sources'],**manifest['inputs']}.items():
                    if sha(path)!=expected: raise ValueError('source or input changed during study')
                record=dict(start=len(records)+1,identity=task,manifest_sha256=digest,maximum_fit_sweeps=200,
                    maximum_fixture_sweeps=1)
                with journal.open('a') as stream:
                    stream.write(json.dumps(record,sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
                records.append(record); charged.add(task)
                try:
                    f=controls.fixture(model,factor,geometry); p=original.problem(f,kernel,tangent)
                    r,j,boundaries=p.residual_tangent(original.truth_point(f,p),model)
                    _,singular,right=np.linalg.svd(j,full_matrices=False)
                    reference_error=float(np.max(np.linalg.norm((p.cholesky@r).reshape(-1,3)*f['metric'],axis=1)))
                    check=dict(native_sweeps=1,maximum_truth_position_error_m=reference_error,
                        truth_objective=float(r@r),receiver_epochs_at_boundaries=boundaries,
                        singular_values=singular.tolist(),weak_direction=dict(zip(p.bounds.active,right[-1].tolist())),
                        condition_number=float(singular[0]/singular[-1]))
                    if reference_error>=.002 or boundaries:
                        raise ValueError('independent fixture prediction failed; no fit executed')
                    row=controls.run_fit(model,factor,geometry,kernel,tangent)
                    row.update(model=model,reused=False,fixture_check=check)
                except Exception as error:
                    row=dict(identity=task,model=model,refinement_factor=factor,geometry=geometry,reused=False,
                        passed=False,error=f'{type(error).__name__}: {error}',observed_fit_starts=0)
                save(target,row)
            rows.append(row)
            print(json.dumps(dict(identity=task,passed=row['passed'],
                offset_error_dph=row.get('gyro_bias_z_error_dph'),sweeps=row.get('actual_tangent_sweeps'))),flush=True)
        payload=dict(version=controls.VERSION,manifest_sha256=digest,results=rows,
            observed_fit_starts=0,full_archival_solver_qualified=False)
        save(HERE/'summary.json',payload)
        save(HERE/'completion.json',dict(manifest_sha256=digest,summary_sha256=sha(HERE/'summary.json'),
            charged_starts=len(records),new_fit_count=9,passed=sum(r['passed'] for r in rows if not r['reused'])))
    return package()


def package():
    completion=json.loads((HERE/'completion.json').read_text())
    if completion['summary_sha256']!=sha(HERE/'summary.json') or completion['manifest_sha256']!=sha(HERE/'manifest.json'):
        raise ValueError('completed result hash mismatch')
    payload=json.loads((HERE/'summary.json').read_text()); rows=payload['results']
    new=[r for r in rows if not r['reused']]
    passed=sum(r['passed'] for r in new)
    table=[]; csv_rows=[]
    for r in rows:
        fit=r.get('fit',{})
        line=dict(model=r['model'],geometry=r['geometry'],factor=r['refinement_factor'],reused=r['reused'],
            passed=r['passed'],offset_error_dph=r.get('gyro_bias_z_error_dph'),gain_error=r.get('gyro_gain_z_error'),
            objective=fit.get('residual_sum_squares'),maximum_position_error_m=r.get('maximum_position_error_m'),
            truth_maximum_position_error_m=r.get('truth_maximum_position_error_m'),
            tangent_sweeps=r.get('actual_tangent_sweeps'),active_bounds=';'.join(fit.get('active_bounds',[])),
            error=r.get('error',''))
        csv_rows.append(line)
        interval=5/r['refinement_factor']
        table.append(f"| {r['model']} | {r['geometry']} | {interval:g} | {'reused' if r['reused'] else str(r['passed'])} | {r.get('gyro_bias_z_error_dph','unavailable')} | {r.get('maximum_position_error_m','unavailable')} |")
    with (HERE/'comparisons.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(csv_rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(csv_rows)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    trends=[]
    for model in explore.MODELS:
        group=[r for r in rows if r['model']==model and 'fit' in r]
        weak=sorted([r for r in group if r['geometry']=='original'],key=lambda r:r['refinement_factor'])
        roll=[r for r in group if r['geometry']=='roll']
        color=ax.loglog([5/r['refinement_factor'] for r in weak],
            [max(abs(r['gyro_bias_z_error_dph']),1e-12) for r in weak],marker='o',label=model)[0].get_color()
        for r in roll: ax.loglog(5/r['refinement_factor'],max(abs(r['gyro_bias_z_error_dph']),1e-12),
            marker='x',markersize=9,color=color)
        if len(weak)==3 and len(roll)==1:
            errors=[abs(r['gyro_bias_z_error_dph']) for r in weak]
            trends.append(dict(model=model,half_interval_error_ratio=errors[1]/errors[0],
                quarter_interval_error_ratio=errors[2]/errors[0],
                roll_error_ratio_at_quarter_interval=abs(roll[0]['gyro_bias_z_error_dph'])/errors[2]))
    ax.set(xlabel='Increment interval (ms)',ylabel='Absolute Z gyro-offset error (degrees/hour)',
        title='Fixed trajectory and calibration: interval and roll controls')
    ax.grid(alpha=.25,which='both'); ax.legend(fontsize=8)
    ax.text(.02,.03,'Circles: original motion; crosses: added roll',transform=ax.transAxes,fontsize=8)
    with matplotlib.rc_context({'svg.hashsalt':controls.VERSION}):
        fig.savefig(HERE/'offset-errors.svg',metadata={'Date':None})
    plt.close(fig)
    actual=sum(r.get('actual_tangent_sweeps',0)+r.get('actual_value_sweeps',0)+
        r.get('fixture_check',{}).get('native_sweeps',0) for r in new)
    save(HERE/'trends.json',dict(trends=trends,new_native_sweeps=actual,observed_fit_starts=0))
    trend_table='\n'.join(f"| {r['model']} | {r['half_interval_error_ratio']:.4g} | {r['quarter_interval_error_ratio']:.4g} | {r['roll_error_ratio_at_quarter_interval']:.4g} |" for r in trends)
    text=f'''# Integration interval and calibration geometry controls

**{passed}/9 new fits passed the predefined prediction/convergence checks.** Three
coarse results were reused without refitting. This study asks why the earlier
synthetic controls recovered positions accurately while recovering Z gyro offset
poorly. It adds no NASA findings or observed-data fits. See the [frozen plan](PLAN.md).

An **IMU (inertial measurement unit)** records turning and acceleration. These
controls reintegrate known continuous angular rate and specific force at 5, 2.5 and
1.25 ms intervals. The trajectory, 24 independently time-tagged receiver observations,
latency, calibration and initial state stay fixed. The three tracks are equatorial,
eastward at 220 m/s and 1,000 m altitude, for 12 seconds. True Z offset is +0.25°/hour.
All three geographic models have their own correctly generated control.

Finer samples are newly generated analytic integrals. No archival increments are
split, interpolated or altered. Variable-rate/near-boundary controls from the earlier
study are not refitted. The original six-parameter solver, bounds and common synthetic
covariance are retained; only interval or prescribed body roll changes.

The additional roll control is 0.35 sin(2πt/5.1) radians, about ±20°. Pitch and yaw
stay unchanged. It uses the same fine interval and receiver path. This informative
software motion tests conditioning and does not imply that archival flights contain
such a pattern. It is not a participant reversal protocol.

## Saved comparisons

| True model | Body motion | Interval (ms) | Prediction check | Z offset error (°/hour) | Largest position error (m) |
|---|---|---:|---|---:|---:|
{chr(10).join(table)}

The original 5 ms rows come from the completed
[geographic controls](../ilvis0-geographic-controls-20261011/README.md). The original
[calibration audit](../ilvis0-geographic-controls-20261011/CALIBRATION.md) stays frozen.
Full fit/gradient/conditioning diagnostics and failures are retained. A passing
prediction check does not imply exact calibration recovery.

![Offset errors versus interval](offset-errors.svg)

| True model | Error at half interval / coarse error | Error at quarter interval / coarse error | Roll / original error at quarter interval |
|---|---:|---:|---:|
{trend_table}

Ratios compare absolute errors from matched known truth. They describe these controls;
they are not uncertainty intervals, significance levels or measured NASA performance.
The figure uses a 10⁻¹²°/hour display floor only. Results retain signed errors.

## Interpretation and limits

A reduction of offset error as the interval shrinks supports finite-interval
approximation being amplified by weak calibration geometry in these synthetic
controls. The matched fine-interval roll comparison tests geometry separately.
The measured ratios determine how strong that evidence is; no particular ratio is
required to declare the experiment complete. Good track reconstruction alone cannot
establish correctly recovered nuisance parameters.

These short controls have known continuous increments, no noise, no upstream rate
removal and six free parameters. They do not replicate unknown coning/sculling or
instrument preprocessing in the NASA recordings. They do not select its actual
integration clock, explain its boundary saturation or qualify all 27 nuisance
parameters. Refining actual logged packets without a physical basis is not justified.
Further integration/geometry controls need a separate source/configuration identity;
observed profiles require their own finite allowance.

The report charged nine starts with no retries and used {actual} new native sweeps,
within the 1,809-sweep ceiling. Baseline sweeps belong to the original completed study
and were not repeated. Source/input/environment hashes and append-only starts are
preserved. Rebuild this report without starting fits:

```sh
env PYTHONPATH=analysis MPLCONFIGDIR=/tmp/lll-interval-matplotlib ~/venv/bin/python docs/ilvis0-interval-controls-20261011/build_report.py --package-only
```
'''
    (HERE/'README.md').write_text(text)
    manifest=json.loads((HERE/'manifest.json').read_text())
    save(HERE/'report-receipt.json',dict(version=controls.VERSION,sources=manifest['sources'],
        inputs=manifest['inputs'],environment=manifest['environment'],
        artifacts={n:sha(HERE/n) for n in ('README.md','PLAN.md','comparisons.csv','offset-errors.svg',
            'trends.json','summary.json','manifest.json','completion.json')},observed_fit_starts=0))
    return dict(new_fits_passed=passed,new_fit_count=len(new),new_native_sweeps=actual,trends=trends,observed_fit_starts=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run',action='store_true'); group.add_argument('--package-only',action='store_true')
    args=parser.parse_args(); print(json.dumps(run() if args.run else package(),sort_keys=True))
