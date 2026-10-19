# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen local calibration controls; zero observed fits or original reads."""
import argparse
import csv
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from lll.ilvis0_receipt_journal import durable_write,encoded

NAME='ilvis0-scalar-calibration-controls-20261019'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
MODELS=('sphere_rotating','sphere_still','flat_still')
PROFILES=('stationary','eastbound','changing_direction','climbing')
LIMITS=dict(identities=72,reference_evaluations=8712,candidate_force_evaluations=8712,
    svds=72,observed_starts=0,native_evaluations=0,original_reads=0,retries=0,
    numerical_threads=4,maximum_wall_s=60)
CALIBRATION_LIMITS=[.15,.15,.15,.25,.25,.25,.05]
RCOND=1e-10


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_bytes())
def write(path,value):durable_write(path,encoded(value),replace=True)


def environment():
    return dict(python=sys.version,executable=sys.executable,platform=platform.platform(),
        packages={name:importlib.metadata.version(name) for name in ('numpy','scipy','pytest')})


def tasks():
    return [dict(identity='--'.join((profile,model,candidate,str(attitude))),
        profile=profile,model=model,candidate=candidate,attitude=attitude)
        for profile in PROFILES for model in MODELS for candidate in MODELS for attitude in (0,1)]


def require_unstarted():
    if (DATA/'start.json').exists() or (DATA/'completion.json').exists():
        raise ValueError('charged or completed calibration controls cannot restart')


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    names=['analysis/lll/ilvis0_scalar_calibration.py','analysis/lll/ilvis0_receiver_force.py',
        'analysis/lll/ilvis0_channel_controls.py','analysis/lll/models.py',
        'analysis/lll/compute_budget.py','analysis/lll/ilvis0_receipt_journal.py',
        'analysis/tests/run_numerical.py','analysis/tests/ilvis0_channel_reference.py',
        'analysis/tests/ilvis0_scalar_calibration_worker.py',
        'analysis/tests/test_ilvis0_scalar_calibration.py',
        'analysis/tests/test_ilvis0_scalar_calibration_worker.py','docs/'+NAME+'/PLAN.md']
    sources={name:sha(ROOT/name) for name in names}
    for name in names:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version='scalar-calibration-projection-v1',sources=sources,
        environment=environment(),tasks=tasks(),limits=LIMITS,epoch_times_s=list(range(0,601,5)),
        calibration_limits=CALIBRATION_LIMITS,relative_rank_tolerance=RCOND,
        scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if (manifest['environment']!=environment() or manifest['tasks']!=tasks()
            or manifest['limits']!=LIMITS or manifest['calibration_limits']!=CALIBRATION_LIMITS
            or manifest['relative_rank_tolerance']!=RCOND):
        raise ValueError('frozen environment, tasks or limits changed')
    if load(DATA/'authorization.json')['manifest_sha256']!=sha(DATA/'manifest.json'):
        raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:
            raise ValueError('frozen source changed: '+name)
    return manifest


def evaluate(task):
    import numpy as np
    from ilvis0_channel_reference import reference,PROFILES as profiles,BACKGROUND,GRAVITY,RADIUS
    from lll.ilvis0_receiver_force import evaluate as required_force
    from lll.ilvis0_scalar_calibration import analyze
    body=[];force=[]
    for t in range(0,601,5):
        truth=reference(task['model'],profiles[task['profile']],float(t))
        body.append(truth['body_forces'][task['attitude']])
        result=required_force(truth['coordinates'],truth['rate'],truth['second'],
            model=task['candidate'],background_rate_rads=BACKGROUND if task['candidate']=='sphere_rotating' else 0.,
            gravity_mps2=GRAVITY,disc_radius_m=RADIUS)
        force.append(result['specific_force_ned_mps2'])
    result=analyze(body,force,CALIBRATION_LIMITS,rcond=RCOND)
    j=result['scaled_jacobian'];r=result['projected_residual']
    error=float(np.linalg.norm(j.T@r))
    limit=1e-9*max(1.,float(np.linalg.norm(j)*np.linalg.norm(r)))
    passed=(error<=limit and result['projected_rms_mps2']<=result['uncorrected_rms_mps2']+1e-12)
    if task['model']==task['candidate']:passed=passed and result['uncorrected_rms_mps2']<=1e-9
    result={key:value.tolist() if isinstance(value,np.ndarray) else value for key,value in result.items()}
    return dict(task,analysis=result,body_force_mps2=np.asarray(body).tolist(),
        required_force_ned_mps2=np.asarray(force).tolist(),orthogonality_error=error,
        orthogonality_limit=limit,passed=bool(passed),scientific_decision='abstain')


def publish():
    summary=load(DATA/'summary.json');complete=load(DATA/'completion.json')
    if (complete['manifest_sha256']!=sha(DATA/'manifest.json')
            or complete['summary_sha256']!=sha(DATA/'summary.json')):
        raise ValueError('completed evidence changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('sealed result changed')
        names.extend((row['artifact'],row['charge']));results.append(load(DATA/row['artifact']))
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    fields=['identity','profile','model','candidate','attitude','rank','uncorrected_rms_mps2',
        'projected_rms_mps2','linear_step_within_bounds','nonlinear_rms_at_linear_step_mps2','passed']
    with (PUBLIC/'controls.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in results:
            writer.writerow({key:row[key] if key in row else row['analysis'][key] for key in fields})
    lines=['# Scalar calibration projection controls','',
        f"**{sum(r['passed'] for r in results)}/72 software controls passed** in {summary['elapsed_s']:.2f} seconds. No original recordings, observed fits or native integrations were used.",'',
        'The matrix compares stationary, eastbound, changing-direction and climbing reference motion under three truth models, all three candidates and two body-orientation histories. All seven calibration columns remain in the rank calculation.','',
        '[All 72 outcomes](controls.csv) include ranks, local projection, feasibility and actual nonlinear residual at feasible linear corrections. These are mathematical controls, not measured device errors or calibrated evidence.','',
        '| Motion | Cases | Rank range | Largest uncorrected RMS | Largest projected RMS | Feasible linear steps |',
        '|---|---:|---|---:|---:|---:|']
    for profile in PROFILES:
        group=[r['analysis'] for r in results if r['profile']==profile]
        ranks=[r['rank'] for r in group]
        lines.append(f"| {profile.replace('_',' ')} | {len(group)} | {min(ranks)}–{max(ranks)} | "+
            f"{max(r['uncorrected_rms_mps2'] for r in group):.7g} | {max(r['projected_rms_mps2'] for r in group):.7g} | "+
            str(sum(r['linear_step_within_bounds'] for r in group))+' |')
    lines+=['','RMS values are in m/s². Maxima can belong to different cases; compare individual rows for matched changes.','',
        'A local projection is unbounded and first order. Its removed difference need not be attainable with feasible nonlinear calibration; its remaining difference does not rule out other nonlinear solutions. No model verdict follows.','',
        'The main 53-stretch results and unresolved horizontal-only sensitivity outcome are unchanged.','',
        '[Frozen plan and limits](PLAN.md) · [Calibration ambiguity](../ilvis0-measurement-contribution/CALIBRATION.md) · [Measurement contributions](../ilvis0-measurement-contribution/README.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name)
        for name in names+['README.md','PLAN.md','controls.csv']}))


def run():
    manifest=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);require_unstarted()
        write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        started=time.monotonic();rows=[]
        def timeout(*_):raise TimeoutError('finite sixty-second allowance exhausted')
        previous=signal.signal(signal.SIGALRM,timeout);signal.alarm(60)
        try:
            for i,task in enumerate(manifest['tasks'],1):
                verify();charge=f'charges/{i:03d}.json';(DATA/'charges').mkdir(exist_ok=True)
                durable_write(DATA/charge,encoded(dict(task,manifest_sha256=sha(DATA/'manifest.json'),
                    reference_allowance=121,candidate_force_allowance=121,svd_allowance=1)))
                write(DATA/'status.json',dict(state='software_controls',pid=os.getpid(),
                    allocated_numerical_threads=4,total=72,completed=len(rows),identity=task['identity']))
                result=evaluate(task);name=task['identity']+'.json';durable_write(DATA/name,encoded(result))
                rows.append(dict(task,passed=result['passed'],artifact=name,artifact_sha256=sha(DATA/name),charge=charge))
            verify()
            write(DATA/'summary.json',dict(state='complete',results=rows,elapsed_s=time.monotonic()-started,
                passed=all(r['passed'] for r in rows),reference_evaluations=8712,candidate_force_evaluations=8712,
                svds=72,observed_starts=0,native_evaluations=0,original_reads=0,
                scientific_decision='abstain',main_findings_changed=False))
            write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),
                summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',total=72,completed=72,allocated_numerical_threads=0))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=type(error).__name__+': '+str(error),completed=len(rows)))
            raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print(f"Completed {len(rows)} calibration controls; {sum(r['passed'] for r in rows)} passed; zero observed fits.")


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true')
    args=parser.parse_args()
    if args.package_only:publish()
    elif args.prepare_only:prepare()
    else:
        from lll.compute_budget import environment as budget_environment
        os.environ.update(budget_environment(workers=1,threads=4,reserved=0));run()
