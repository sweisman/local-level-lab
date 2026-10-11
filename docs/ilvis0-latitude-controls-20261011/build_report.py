# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded latitude/convention controls; packaging reads saved evidence only."""
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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from lll import ilvis0_latitude_controls as controls
from lll import ilvis0_compensation as candidate, ilvis0_geographic_controls as original
from lll import ilvis0_exploratory as explore

HERE=Path(__file__).resolve().parent
REFERENCE=HERE.parent/'ilvis0-compensation-controls-20261011'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,value):
    temporary=path.with_suffix(path.suffix+'.partial')
    with temporary.open('w') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def cases():
    return [(model,degrees,construction,start) for model in explore.MODELS for degrees in (-45.,45.)
        for construction in ('interior','near_roll') for start in ('zero','opposed')]


def journal(path,allowed,digest):
    records=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if ([r['identity'] for r in records]!=allowed[:len(records)] or len(records)>len(allowed)
        or any(r['manifest_sha256']!=digest or r['start']!=i+1 for i,r in enumerate(records))):
        raise ValueError('invalid immutable start journal')
    return records


def charge(path,records,identity,digest,ceiling):
    record=dict(start=len(records)+1,identity=identity,manifest_sha256=digest,maximum_sweeps=ceiling)
    with path.open('a') as stream:
        stream.write(json.dumps(record,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
    records.append(record)


def check_specs():
    return [(model,lat,construction,'ordinary_rate_integrals',mode)
        for model in explore.MODELS for lat in (-45.,45.) for construction in ('interior','near_roll')
        for mode in ('baseline','combined')]+[(model,lat,'interior','already_compensated',mode)
        for model in explore.MODELS for lat in (-45.,45.) for mode in ('baseline','mislabelled_combined')]


def check_identity(spec):return '::'.join(str(x) for x in spec)


def verify_frozen(manifest):
    for name,wanted in {**manifest['sources'],**manifest['inputs']}.items():
        if sha(name)!=wanted:raise ValueError('frozen source/input changed')


def evaluate_check(spec,kernel):
    model,lat,construction,convention,mode=spec
    f=controls.fixture(model,lat,construction,convention=convention)
    mislabelled=mode=='mislabelled_combined'
    p=candidate.problem(f,kernel,'combined' if mislabelled else mode,
        convention='ordinary_rate_integrals' if mislabelled else convention)
    r,j,b=p.residual_tangent(original.truth_point(f,p),model)
    singular=np.linalg.svd(j,compute_uv=False)
    error=float(np.max(np.linalg.norm((p.cholesky@r).reshape(-1,3)*f['metric'],axis=1)))
    return dict(identity=check_identity(spec),model=model,latitude_deg=lat,construction=construction,
        convention=convention,mode=mode,deliberate_mislabel_diagnostic=mislabelled,
        maximum_position_error_m=error,objective=float(r@r),condition_number=float(singular[0]/singular[-1]),
        native_sweeps=1,receiver_epochs_at_boundaries=b)


def run():
    with (HERE/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (HERE/'completion.json').exists():raise ValueError('completed study frozen; package only')
        receipt=json.loads((REFERENCE/'report-receipt.json').read_text())
        for group in ('sources','inputs','artifacts'):
            for name,wanted in receipt[group].items():
                path=Path(name) if Path(name).is_absolute() else REFERENCE/name
                if sha(path)!=wanted:raise ValueError('reference provenance mismatch')
        kernel,build=candidate.load_kernel(HERE/'kernel')
        sources=dict(receipt['sources'])
        for path in (Path(__file__),HERE/'PLAN.md',Path(controls.__file__),
            HERE.parents[1]/'analysis/tests/test_ilvis0_latitude_controls.py'):
            sources[str(path.resolve())]=sha(path)
        env=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,
            threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
        if any(v!='2' for v in env['threads'].values()):raise ValueError('declared two-thread environment required')
        ids=[controls.identity(*case) for case in cases()]; specs=check_specs(); check_ids=[check_identity(x) for x in specs]
        inputs={str((REFERENCE/n).resolve()):sha(REFERENCE/n) for n in ('manifest.json','summary.json','report-receipt.json')}
        manifest=dict(version=controls.VERSION,sources=sources,inputs=inputs,environment=env,native_build=build,
            identities=ids,prediction_identities=check_ids,maximum_starts=24,maximum_sweeps=4836,observed_fit_starts=0)
        if (HERE/'manifest.json').exists():
            if json.loads((HERE/'manifest.json').read_text())!=manifest:raise ValueError('incompatible continuation')
        else:save(HERE/'manifest.json',manifest)
        digest=sha(HERE/'manifest.json'); starts=HERE/'starts.jsonl'; predictions=HERE/'prediction-starts.jsonl'
        records=journal(starts,ids,digest); probes=journal(predictions,check_ids,digest)
        checks=[]
        for i,spec in enumerate(specs):
            path=HERE/f'check-{i:02d}.json';identity=check_ids[i]
            if path.exists():row=json.loads(path.read_text())
            elif any(r['identity']==identity for r in probes):
                row=dict(identity=identity,error='interrupted charged prediction; no retry',native_sweeps=1);save(path,row)
            else:
                verify_frozen(manifest);charge(predictions,probes,identity,digest,1)
                try:row=evaluate_check(spec,kernel)
                except Exception as error:row=dict(identity=identity,error=f'{type(error).__name__}: {error}',native_sweeps=1)
                save(path,row)
            if row['identity']!=identity:raise ValueError('prediction identity mismatch')
            checks.append(row)
        rows=[]
        for i,case in enumerate(cases()):
            identity=ids[i];path=HERE/f'fit-{i:02d}.json'
            if path.exists():row=json.loads(path.read_text())
            elif any(r['identity']==identity for r in records):
                row=dict(identity=identity,passed=False,error='interrupted charged start; no retry',charged_sweeps=200);save(path,row)
            else:
                verify_frozen(manifest);charge(starts,records,identity,digest,200)
                row=controls.run_fit(*case,kernel);save(path,row)
            if row['identity']!=identity:raise ValueError('fit identity mismatch')
            rows.append(row)
            print(json.dumps(dict(identity=identity,passed=row['passed'],bias_error_dph=row.get('gyro_bias_z_error_dph'),
                sweeps=row.get('actual_tangent_sweeps'))),flush=True)
        summary=dict(version=controls.VERSION,results=rows,checks=checks,manifest_sha256=digest,observed_fit_starts=0,
            archival_promotion=False)
        save(HERE/'summary.json',summary)
        save(HERE/'completion.json',dict(manifest_sha256=digest,summary_sha256=sha(HERE/'summary.json'),charged_starts=len(records),
            charged_predictions=len(probes),passed=sum(r['passed'] for r in rows)))
    return package()


def package():
    completion=json.loads((HERE/'completion.json').read_text());manifest=json.loads((HERE/'manifest.json').read_text())
    if completion['manifest_sha256']!=sha(HERE/'manifest.json') or completion['summary_sha256']!=sha(HERE/'summary.json'):
        raise ValueError('completed evidence hash mismatch')
    summary=json.loads((HERE/'summary.json').read_text());rows=summary['results'];checks=summary['checks']
    fields=('identity','passed','gyro_bias_z_error_dph','gyro_gain_z_error','maximum_position_error_m','actual_tangent_sweeps','actual_value_sweeps','error')
    with (HERE/'fits.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader()
        writer.writerows({key:r.get(key,'') for key in fields} for r in rows)
    fields=('identity','maximum_position_error_m','condition_number','deliberate_mislabel_diagnostic','native_sweeps','error')
    with (HERE/'known-calibration.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader()
        writer.writerows({key:r.get(key,'') for key in fields} for r in checks)
    sweeps=sum(r.get('actual_tangent_sweeps',0)+r.get('actual_value_sweeps',0)+r.get('charged_sweeps',0) for r in rows)+sum(r['native_sweeps'] for r in checks)
    if sweeps>manifest['maximum_sweeps']:raise ValueError('native sweep allowance exceeded')
    fit_table='\n'.join(f"| {r['identity']} | {'yes' if r['passed'] else 'no'} | {r.get('gyro_bias_z_error_dph','unavailable')} | {r.get('maximum_position_error_m','unavailable')} |" for r in rows)
    convention_table=[]
    for model in explore.MODELS:
        for lat in (-45.,45.):
            pair=[next(r for r in checks if r['identity']==check_identity((model,lat,'interior','already_compensated',mode))) for mode in ('baseline','mislabelled_combined')]
            convention_table.append(f"| {model} | {lat:+.0f}° | {pair[0].get('maximum_position_error_m','unavailable')} | {pair[1].get('maximum_position_error_m','unavailable')} |")
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    positions=[(lat,c) for lat in (-45.,45.) for c in ('interior','near_roll')]
    for model in explore.MODELS:
        for start,marker in (('zero','o'),('opposed','x')):
            group=[next(r for r in rows if r['identity']==controls.identity(model,lat,c,start)) for lat,c in positions]
            valid=[(i,r) for i,r in enumerate(group) if 'gyro_bias_z_error_dph' in r]
            ax.semilogy([i for i,r in valid],[max(abs(r['gyro_bias_z_error_dph']),1e-12) for i,r in valid],marker=marker,label=f'{model}, {start}')
    ax.set(xticks=range(4),xticklabels=['−45° interior','−45° near/roll','+45° interior','+45° near/roll'],
        ylabel='Absolute Z offset error (degrees/hour)',title='Independent latitude controls at 200 Hz')
    ax.grid(alpha=.25,which='both');ax.legend(fontsize=7,ncol=2)
    with matplotlib.rc_context({'svg.hashsalt':controls.VERSION}):fig.savefig(HERE/'offset-errors.svg',metadata={'Date':None})
    plt.close(fig)
    text=f'''# Latitude and increment-convention controls

**{sum(r['passed'] for r in rows)}/24 software fits passed the predefined numerical checks.**
This extends the [original-rate comparison](../ilvis0-compensation-controls-20261011/FINDINGS.md)
to +45° and −45° latitude. No NASA recordings were refitted. See the [frozen plan](PLAN.md).

An **IMU (inertial measurement unit)** records turning and acceleration. These controls
use independently calculated motion and known calibration to test the software, rather
than infer an Earth model from real measurements. Each model receives observations
generated from its own physical truth. All tracks last 12 seconds at 220 m/s and 1,000 m.

## Calibration recovery

The interior case uses pitch/yaw and regular timing. The near/roll case combines added
roll, unequal timing and calibration close to its limits. Both run from zero and a
deliberately opposed start, with the same original six-parameter bounds and solver.
Pass criteria check convergence and position prediction; calibration error is separately
reported and can expose weakness even when a fit passes. These noise-free short tracks
do not qualify full archival nuisance freedom or uncertainty estimates.

![Offset recovery across latitude and starting point](offset-errors.svg)

| Control identity: model / latitude / construction / start | Numerical pass | Z offset error (°/hour) | Maximum position error (m) |
|---|---|---:|---:|
{fit_table}

## Why the increment convention matters

The additional controls define already-compensated increments from exact attitude
endpoints and an independently integrated force. Receiver observations occur at packet
endpoints. The second column of errors deliberately mislabels these measurements as
ordinary integrated rates, so the candidate applies an inappropriate second correction.
Correctly labelled inputs are rejected by the enabled correction's guard.

| Supplied truth | Latitude | Appropriate original treatment: error (m) | Deliberate double correction: error (m) |
|---|---:|---:|---:|
{chr(10).join(convention_table)}

This mathematical convention is precisely defined for this control. It is not a claim
about Applanix firmware. Partial-packet finite increments need their own convention;
these endpoint checks do not qualify arbitrary interpolation. Neither correction path
can be assigned to the NASA archive solely because one wins on a software control.

## Reproducibility and limits

The run charged {completion['charged_starts']} fit starts and {completion['charged_predictions']}
known-calibration predictions, using {sweeps} native sweeps within the 4,836-sweep ceiling,
with no retries. See [fit details](fits.csv) and [known-calibration checks](known-calibration.csv).
Sources, environment, compiler and native binary are hashed; interrupted starts remain
charged. The archive's scientific evidence gate is unchanged.

Publication reads saved results and starts no fits:

```sh
env PYTHONPATH=analysis MPLCONFIGDIR=/tmp/lll-latitude-matplotlib ~/venv/bin/python docs/ilvis0-latitude-controls-20261011/build_report.py --package-only
```
'''
    (HERE/'README.md').write_text(text)
    artifacts=('PLAN.md','README.md','fits.csv','known-calibration.csv','offset-errors.svg','manifest.json','summary.json','completion.json','starts.jsonl','prediction-starts.jsonl')
    save(HERE/'report-receipt.json',dict(version=controls.VERSION,sources=manifest['sources'],inputs=manifest['inputs'],
        environment=manifest['environment'],artifacts={name:sha(HERE/name) for name in artifacts},observed_fit_starts=0,archival_promotion=False))
    return dict(passed=sum(r['passed'] for r in rows),starts=completion['charged_starts'],native_sweeps=sweeps,observed_fit_starts=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run',action='store_true');group.add_argument('--package-only',action='store_true')
    args=parser.parse_args();print(json.dumps(run() if args.run else package(),sort_keys=True))
