# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite original-rate compensation controls; publication performs no fits."""
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

from lll import ilvis0_compensation as candidate, ilvis0_geographic_controls as controls
from lll import ilvis0_exploratory as explore, ilvis0_shape as shape

HERE=Path(__file__).resolve().parent
REFERENCE=HERE.parent/'ilvis0-geographic-controls-20261011'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,payload):
    temporary=path.with_suffix(path.suffix+'.partial')
    with temporary.open('w') as stream:
        json.dump(payload,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def identities():return [f'{model}::{mode}' for model in explore.MODELS for mode in ('coning','sculling','combined')]


def verify_reference():
    receipt=json.loads((REFERENCE/'report-receipt.json').read_text())
    for name,expected in receipt['sources'].items():
        if sha(name)!=expected:raise ValueError('frozen reference source changed')
    for name,expected in receipt['artifacts'].items():
        if sha(REFERENCE/name)!=expected:raise ValueError('frozen reference artifact changed')
    return receipt


def run_fit(model,mode,kernel):
    f=controls.fixture(model,'nominal')
    p=candidate.problem(f,kernel,mode,convention='ordinary_rate_integrals')
    counted=controls.CountedProblem(p)
    fit=shape.fit_shape_candidate(counted,model,start=np.zeros(len(p.bounds.active)),maximum_evaluations=200)
    point=np.array(fit['normalized_parameters']);truth=controls.truth_point(f,p)
    predicted=counted.predict(point,model);reference=counted.predict(truth,model)
    residual=p.whiten(reference-p.gps);error=controls.position_error(f,predicted)
    reference_error=controls.position_error(f,reference)
    return dict(identity=f'{model}::{mode}',model=model,mode=mode,fit=fit,truth=f['truth'],reused=False,
        gyro_bias_z_error_dph=(fit['parameters']['gyro_bias_z']-f['truth']['gyro_bias_z'])*648000/math.pi,
        gyro_gain_z_error=fit['parameters']['gyro_gain_z']-f['truth']['gyro_gain_z'],
        maximum_position_error_m=error,truth_maximum_position_error_m=reference_error,
        truth_objective=float(residual@residual),actual_tangent_sweeps=counted.tangents,
        actual_value_sweeps=counted.values,observed_fit_starts=0,
        passed=bool(fit['converged'] and error<.002 and reference_error<.002 and
            fit['residual_sum_squares']<=float(residual@residual)+.01))


def run():
    HERE.mkdir(parents=True,exist_ok=True)
    with (HERE/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (HERE/'completion.json').exists():raise ValueError('completed controls frozen; use --package-only')
        reference=verify_reference();kernel,build=candidate.load_kernel(HERE/'kernel')
        sources=dict(reference['sources'])
        for path in (Path(__file__),HERE/'PLAN.md',Path(candidate.__file__),
            Path(candidate.__file__).with_suffix('.cpp'),
            HERE.parents[1]/'analysis/tests/test_ilvis0_compensation.py'):
            sources[str(path.resolve())]=sha(path)
        manifest=dict(version=candidate.VERSION,sources=sources,
            inputs={str((REFERENCE/n).resolve()):sha(REFERENCE/n) for n in ('summary.json','manifest.json','report-receipt.json')},
            environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                matplotlib=matplotlib.__version__,threads={k:os.environ.get(k) for k in
                    ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}),
            native_build=build,identities=identities(),maximum_starts=9,maximum_sweeps=1815,
            increment_convention='ordinary_rate_integrals',observed_fit_starts=0)
        if (HERE/'manifest.json').exists():
            if json.loads((HERE/'manifest.json').read_text())!=manifest:raise ValueError('incompatible continuation')
        else:save(HERE/'manifest.json',manifest)
        digest=sha(HERE/'manifest.json');journal=HERE/'starts.jsonl'
        records=[json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
        if (len({r['identity'] for r in records})!=len(records) or
            any(r['start']!=i+1 or r['manifest_sha256']!=digest or r['identity'] not in identities()
                for i,r in enumerate(records))):raise ValueError('invalid starts journal')
        charged={r['identity'] for r in records};checks=[]
        for model in explore.MODELS:
            f=controls.fixture(model,'nominal')
            for mode in candidate.MODES:
                path=HERE/f'check-{model}-{mode}.json'
                if path.exists():check=json.loads(path.read_text())
                else:
                    p=candidate.problem(f,kernel,mode,convention='ordinary_rate_integrals')
                    r,j,b=p.residual_tangent(controls.truth_point(f,p),model)
                    _,singular,right=np.linalg.svd(j,full_matrices=False)
                    error=float(np.max(np.linalg.norm((p.cholesky@r).reshape(-1,3)*f['metric'],axis=1)))
                    check=dict(model=model,mode=mode,maximum_truth_position_error_m=error,
                        truth_objective=float(r@r),condition_number=float(singular[0]/singular[-1]),
                        weak_direction=dict(zip(p.bounds.active,right[-1].tolist())),
                        singular_values=singular.tolist(),receiver_epochs_at_boundaries=b,native_sweeps=1)
                    save(path,check)
                checks.append(check)
        original=json.loads((REFERENCE/'summary.json').read_text());rows=[]
        for model in explore.MODELS:
            match=[r for r in original['results'] if r['identity']==f'{model}::nominal::original::zero']
            if len(match)!=1:raise ValueError('unique baseline required')
            r=match[0];parameters=r['fit']['parameters']
            rows.append(dict(r,model=model,mode='baseline',reused=True,
                gyro_bias_z_error_dph=(parameters['gyro_bias_z']-r['truth']['gyro_bias_z'])*648000/math.pi,
                gyro_gain_z_error=parameters['gyro_gain_z']-r['truth']['gyro_gain_z']))
        for identity in identities():
            model,mode=identity.split('::');path=HERE/(identity.replace('::','-')+'.json')
            if path.exists():row=json.loads(path.read_text())
            elif identity in charged:
                row=dict(identity=identity,model=model,mode=mode,reused=False,passed=False,
                    error='interrupted charged start; no retry',observed_fit_starts=0);save(path,row)
            else:
                for source,expected in {**manifest['sources'],**manifest['inputs']}.items():
                    if sha(source)!=expected:raise ValueError('source/input changed')
                record=dict(start=len(records)+1,identity=identity,manifest_sha256=digest,maximum_sweeps=200)
                with journal.open('a') as stream:
                    stream.write(json.dumps(record,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
                records.append(record);charged.add(identity)
                try:row=run_fit(model,mode,kernel)
                except Exception as error:
                    row=dict(identity=identity,model=model,mode=mode,reused=False,passed=False,
                        error=f'{type(error).__name__}: {error}',observed_fit_starts=0)
                save(path,row)
            rows.append(row)
            print(json.dumps(dict(identity=identity,passed=row['passed'],offset_error_dph=row.get('gyro_bias_z_error_dph'),
                sweeps=row.get('actual_tangent_sweeps'))),flush=True)
        payload=dict(version=candidate.VERSION,results=rows,checks=checks,manifest_sha256=digest,
            observed_fit_starts=0,archival_promotion=False)
        save(HERE/'summary.json',payload)
        save(HERE/'completion.json',dict(manifest_sha256=digest,summary_sha256=sha(HERE/'summary.json'),
            charged_starts=len(records),new_fits_passed=sum(r['passed'] for r in rows if not r['reused'])))
    return package()


def package():
    completion=json.loads((HERE/'completion.json').read_text())
    if completion['summary_sha256']!=sha(HERE/'summary.json') or completion['manifest_sha256']!=sha(HERE/'manifest.json'):
        raise ValueError('completed report hash mismatch')
    payload=json.loads((HERE/'summary.json').read_text());rows=payload['results'];checks=payload['checks']
    new=[r for r in rows if not r['reused']];passed=sum(r['passed'] for r in new)
    table=[];data=[]
    for row in rows:
        fit=row.get('fit',{})
        line=dict(model=row['model'],mode=row['mode'],reused=row['reused'],passed=row['passed'],
            offset_error_dph=row.get('gyro_bias_z_error_dph'),gain_error=row.get('gyro_gain_z_error'),
            maximum_position_error_m=row.get('maximum_position_error_m'),
            objective=fit.get('residual_sum_squares'),truth_objective=row.get('truth_objective'),
            tangent_sweeps=row.get('actual_tangent_sweeps'),active_bounds=';'.join(fit.get('active_bounds',[])),
            error=row.get('error',''))
        data.append(line)
        table.append(f"| {row['model']} | {row['mode']} | {'reused' if row['reused'] else row['passed']} | {row.get('gyro_bias_z_error_dph','unavailable')} | {row.get('maximum_position_error_m','unavailable')} |")
    with (HERE/'comparisons.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(data[0]),lineterminator='\n');writer.writeheader();writer.writerows(data)
    with (HERE/'known-calibration.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=('model','mode','maximum_truth_position_error_m','truth_objective','condition_number'),lineterminator='\n')
        writer.writeheader();writer.writerows({k:r[k] for k in writer.fieldnames} for r in checks)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    modes=('baseline','coning','sculling','combined')
    for model in explore.MODELS:
        group=[next((r for r in rows if r['model']==model and r['mode']==mode and 'fit' in r),None) for mode in modes]
        ax.semilogy([i for i,r in enumerate(group) if r],
            [max(abs(r['gyro_bias_z_error_dph']),1e-12) for r in group if r],marker='o',label=model)
    ax.set(xticks=range(4),xticklabels=['Original','Coning','Rotating force','Both'],
        ylabel='Absolute Z gyro-offset error (degrees/hour)',title='Same 200 Hz increments, receiver data and calibration')
    ax.grid(alpha=.25,which='both');ax.legend(fontsize=8)
    with matplotlib.rc_context({'svg.hashsalt':candidate.VERSION}):fig.savefig(HERE/'offset-errors.svg',metadata={'Date':None})
    plt.close(fig)
    actual=sum(r.get('actual_tangent_sweeps',0)+r.get('actual_value_sweeps',0) for r in new)+sum(r['native_sweeps'] for r in checks)
    known_table='\n'.join(f"| {r['model']} | {r['mode']} | {r['maximum_truth_position_error_m']:.6g} |" for r in checks)
    text=f'''# Coning/sculling controls at the original 200 Hz

**{passed}/9 new fits passed the predefined prediction/convergence checks.** Three
original fits were reused without refitting. The same synthetic increments, receiver
timestamps and injected calibration are used throughout. There are no NASA input
files, no observed-data starts and no change to the frozen archival integrator.
See the [predefined plan](PLAN.md).

An **IMU (inertial measurement unit)** measures turning and acceleration. Ordinary
integrals of those rates are not automatically equivalent to a finite rotation or
a velocity change expressed in a single fixed frame when the instrument moves.
Coning accounts for changing rotation axes; sculling/rotation compensation accounts
for rotating specific force. [Brouk and DeMars](https://ntrs.nasa.gov/citations/14626669150663)
discuss these effects and their uncertainty propagation. This candidate's particular
series is independently derived and tested here, not a claimed Applanix algorithm.

## What changed

Each control is the existing 12-second, 220 m/s equatorial track at 1,000 m altitude,
with known pitch/yaw, 24 receiver epochs and +0.25°/hour Z gyro offset. No samples
are inserted or discarded. A new forward model estimates linear rate variation from
three adjacent calibrated packet averages. Full integrals are preserved; partial
packet predictions include that variation rather than scaling the entire packet
uniformly. Calibration and latency derivatives include these corrections.

Five known-calibration modes separate the original predictor, linear partials,
coning, rotating-force compensation, and both. Coning/sculling fits use the original
solver from zero, with the same six nuisance bounds and synthetic 1 cm position
scale. Nonzero approximation errors are retained. Independent continuous differential
equations check constant-rate, single-axis and changing-axis packet behavior.
Disabled corrections reproduce the old values and derivatives exactly.

## Calibration fits

| True model | Method | Prediction check | Z offset error (°/hour) | Largest position error (m) |
|---|---|---|---:|---:|
{chr(10).join(table)}

![Offset recovery with the same original-rate increments](offset-errors.svg)

The plot shows absolute offset error with a 10⁻¹²°/hour display floor only. Signed
errors, gains, objectives, active limits and failures are retained in
[comparisons.csv](comparisons.csv) and complete saved diagnostics. A small position
error or successful stop alone does not establish correct calibration.

## Predictions at the injected calibration

| True model | Method | Largest position error (m) |
|---|---|---:|
{known_table}

These predictions use the known calibration, with no fitting. The linear-only row
isolates changed within-packet receiver timing from the higher-order corrections.
Each mode is used equally under all three true model identities; this is numerical
qualification, not choosing an Earth model from real observations.

## Scope and next decision

The candidate assumes ordinary integrated rates and truncated within-packet series.
It explicitly refuses enabled corrections for already-compensated input. The tests
do not establish which convention Applanix logged or whether all required onboard
corrections were applied. Frame rotation, Coriolis, position integration and gravity
retain the original geographic midpoint treatment. Noise, longer records, full
nuisance freedom and installation transfer remain separate qualifications.

Do not apply this candidate to NASA records merely because it improves these known
synthetic controls. First assess recovered calibration and remaining errors, then
qualify increment conventions and equally specified alternatives. Preserve original
measurements and results. Any observed comparison needs a separate finite allowance.

The completed report charged nine starts, with no retries, and used {actual} new
native sweeps within its 1,815-sweep ceiling. Baseline work was reused. Packaging
reads saved results and starts no fits:

```sh
env PYTHONPATH=analysis MPLCONFIGDIR=/tmp/lll-compensation-matplotlib ~/venv/bin/python docs/ilvis0-compensation-controls-20261011/build_report.py --package-only
```
'''
    (HERE/'README.md').write_text(text)
    manifest=json.loads((HERE/'manifest.json').read_text())
    save(HERE/'report-receipt.json',dict(version=candidate.VERSION,sources=manifest['sources'],inputs=manifest['inputs'],
        environment=manifest['environment'],artifacts={n:sha(HERE/n) for n in
            ('README.md','PLAN.md','comparisons.csv','known-calibration.csv','offset-errors.svg','summary.json','manifest.json','completion.json')},
        observed_fit_starts=0,archival_promotion=False))
    return dict(new_fits_passed=passed,new_fits=9,new_native_sweeps=actual,observed_fit_starts=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run',action='store_true');group.add_argument('--package-only',action='store_true')
    args=parser.parse_args();print(json.dumps(run() if args.run else package(),sort_keys=True))
