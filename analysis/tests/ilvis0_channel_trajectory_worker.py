# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite exact-trajectory software diagnostic; no original reads or optimizers."""
import argparse
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

NAME='ilvis0-channel-trajectory-controls-20261019'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
MODELS=('sphere_rotating','sphere_still','flat_still')
PROFILES=('stationary','slow','eastbound','northbound','changing_direction','climbing')
LIMITS=dict(diagnostic_identities=18,epochs_per_identity=21,receiver_force_evaluations=1134,
    magnitude_comparisons=2268,optimizer_starts=0,native_evaluations=0,original_reads=0,
    numerical_threads=4,maximum_wall_s=60,retries=0)
TOLERANCES=dict(velocity=1e-8,acceleration=1e-9,transport=1e-12,force=1e-9,
                magnitude=1e-9,attitude_invariance=1e-9)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_bytes())
def write(path,value):durable_write(path,encoded(value),replace=True)


def environment():
    return dict(python=sys.version,executable=sys.executable,platform=platform.platform(),
        packages={name:importlib.metadata.version(name) for name in ('numpy','scipy','pytest')})


def tasks():
    return [dict(identity=model+'::'+profile,model=model,profile=profile)
            for model in MODELS for profile in PROFILES]


def require_unstarted():
    if (DATA/'start.json').exists() or (DATA/'completion.json').exists():
        raise ValueError('charged or completed software batch cannot restart')


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    names=['analysis/lll/ilvis0_receiver_force.py','analysis/lll/ilvis0_channel_controls.py',
        'analysis/lll/models.py','analysis/lll/compute_budget.py','analysis/lll/ilvis0_receipt_journal.py',
        'analysis/tests/ilvis0_channel_reference.py','analysis/tests/ilvis0_channel_trajectory_worker.py',
        'analysis/tests/test_ilvis0_receiver_force.py','analysis/tests/test_ilvis0_channel_controls.py',
        'analysis/tests/test_ilvis0_channel_trajectory_worker.py','analysis/tests/run_numerical.py',
        'docs/'+NAME+'/PLAN.md']
    sources={name:sha(ROOT/name) for name in names}
    for name in names:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version='independent-channel-trajectory-v1',sources=sources,
        environment=environment(),tasks=tasks(),limits=LIMITS,tolerances=TOLERANCES,
        epoch_times_s=list(range(21)),scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if (manifest['environment']!=environment() or manifest['limits']!=LIMITS
            or manifest['tasks']!=tasks() or manifest['tolerances']!=TOLERANCES):
        raise ValueError('frozen environment, task list or allowance changed')
    if load(DATA/'authorization.json')['manifest_sha256']!=sha(DATA/'manifest.json'):
        raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:
            raise ValueError('frozen source changed: '+name)
    return manifest


def evaluate(task):
    import numpy as np
    from ilvis0_channel_reference import reference,PROFILES as profiles,BACKGROUND,GRAVITY,RADIUS
    from lll import ilvis0_receiver_force as adapter
    from lll.ilvis0_channel_controls import acceleration_magnitude_residual
    errors={name:0. for name in TOLERANCES};epochs=[]
    for t in range(21):
        truth=reference(task['model'],profiles[task['profile']],float(t));candidates={}
        for candidate in MODELS:
            result=adapter.evaluate(truth['coordinates'],truth['rate'],truth['second'],model=candidate,
                background_rate_rads=BACKGROUND if candidate=='sphere_rotating' else 0.,
                gravity_mps2=GRAVITY,disc_radius_m=RADIUS)
            residual=[acceleration_magnitude_residual(body,result['specific_force_ned_mps2'])
                      for body in truth['body_forces']]
            errors['attitude_invariance']=max(errors['attitude_invariance'],abs(residual[0]-residual[1]))
            if candidate==task['model']:
                for actual,expected in (('velocity_ned_mps','velocity'),('acceleration_ned_mps2','acceleration'),
                        ('transport_ned_rads','transport'),('specific_force_ned_mps2','force')):
                    errors[expected]=max(errors[expected],float(np.max(abs(result[actual]-truth[expected]))))
                errors['magnitude']=max(errors['magnitude'],max(abs(v) for v in residual))
            candidates[candidate]=dict(required_force_ned_mps2=result['specific_force_ned_mps2'].tolist(),
                                       magnitude_residuals_mps2=residual)
        epochs.append(dict(time_s=t,coordinates=truth['coordinates'].tolist(),
            coordinate_rate=truth['rate'].tolist(),coordinate_acceleration=truth['second'].tolist(),
            reference_force_ned_mps2=truth['force'].tolist(),body_forces=[f.tolist() for f in truth['body_forces']],
            candidates=candidates))
    scores={candidate:float(np.sqrt(np.mean([r*r for epoch in epochs
        for r in epoch['candidates'][candidate]['magnitude_residuals_mps2']]))) for candidate in MODELS}
    ambiguous=task['profile']=='stationary'
    passed=all(errors[name]<=limit for name,limit in TOLERANCES.items())
    if ambiguous:passed=passed and max(scores.values())<=TOLERANCES['magnitude']
    return dict(task,maximum_component_errors=errors,magnitude_rms_mps2=scores,epochs=epochs,
        stationary_indistinguishability_expected=ambiguous,passed=bool(passed),
        receiver_force_evaluations=63,magnitude_comparisons=126,scientific_decision='abstain')


def publish():
    complete=load(DATA/'completion.json');summary=load(DATA/'summary.json')
    if (complete['manifest_sha256']!=sha(DATA/'manifest.json')
            or complete['summary_sha256']!=sha(DATA/'summary.json')):
        raise ValueError('completed evidence changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('result changed')
        names.extend((row['artifact'],row['charge']))
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Independent trajectory-force diagnostic','',
        f"**{sum(r['passed'] for r in summary['results'])}/18 controls passed.** The batch used {summary['receiver_force_evaluations']} force evaluations and {summary['magnitude_comparisons']} scalar comparisons in {summary['elapsed_s']:.2f} seconds. It read no recordings and performed no fits or native integrations.",'',
        'This checks a new calculation, not instrument accuracy or flight evidence. The reference uses independent Cartesian geometry and derivatives; the adapter uses local coordinate metrics. Two changing attitudes are checked at every epoch.','',
        '| Reference model | Motion | Specified-field globe RMS | Zero-field globe RMS | Flat RMS | Software check |',
        '|---|---|---:|---:|---:|---|']
    for row in summary['results']:
        scores=row['magnitude_rms_mps2']
        lines.append('| '+row['model']+' | '+row['profile'].replace('_',' ')+' | '+
            ' | '.join(f'{scores[m]:.7g}' for m in MODELS)+' | '+('pass' if row['passed'] else 'fail')+' |')
    lines+=['','RMS values are acceleration-magnitude mismatches in m/s² with exact generated trajectories and known calibration. They are not whitened costs, confidence levels, model detections or measured device errors. Stationary controls correctly have no magnitude separation. Incorrect-model outcomes are preserved without requiring discrimination.','',
        'Passing qualifies only this exact-trajectory calculation. Receiver differentiation, its temporal uncertainty, averaging and synchronization, calibration assumptions and recorded-data selection still need qualification. The main 53-stretch findings are unchanged.','',
        '[Frozen scope and limits](PLAN.md) · [Channel-removal requirements](../ilvis0-measurement-contribution/CHANNEL_CONTROLS.md) · [Next step](NEXT_PLAN.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names+['README.md','PLAN.md']}))


def run():
    manifest=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);require_unstarted()
        write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        started=time.monotonic();rows=[]
        def timeout(*_):raise TimeoutError('finite sixty-second software allowance exhausted')
        previous=signal.signal(signal.SIGALRM,timeout);signal.alarm(60)
        try:
            for i,task in enumerate(manifest['tasks'],1):
                verify();identity=task['identity'];charge=f'charges/{i:03d}.json'
                (DATA/'charges').mkdir(exist_ok=True)
                durable_write(DATA/charge,encoded(dict(task,manifest_sha256=sha(DATA/'manifest.json'),
                    receiver_force_allowance=63,magnitude_comparison_allowance=126)))
                write(DATA/'status.json',dict(state='software_controls',pid=os.getpid(),
                    allocated_numerical_threads=4,total=18,completed=len(rows),identity=identity))
                result=evaluate(task);name=identity.replace('::','--')+'.json'
                durable_write(DATA/name,encoded(result))
                rows.append(dict(identity=identity,model=task['model'],profile=task['profile'],
                    passed=result['passed'],maximum_component_errors=result['maximum_component_errors'],
                    magnitude_rms_mps2=result['magnitude_rms_mps2'],artifact=name,artifact_sha256=sha(DATA/name),charge=charge))
            verify()
            summary=dict(state='complete',results=rows,passed=all(r['passed'] for r in rows),
                elapsed_s=time.monotonic()-started,receiver_force_evaluations=18*63,
                magnitude_comparisons=18*126,native_evaluations=0,observed_starts=0,
                original_reads=0,scientific_decision='abstain',main_findings_changed=False)
            write(DATA/'summary.json',summary)
            write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',total=18,completed=18,allocated_numerical_threads=0))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=type(error).__name__+': '+str(error),completed=len(rows)))
            raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print(f"Completed {len(rows)} software controls; {sum(r['passed'] for r in rows)} passed; zero observed fits.")


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true')
    args=parser.parse_args()
    if args.package_only:publish()
    elif args.prepare_only:prepare()
    else:
        from lll.compute_budget import environment as budget_environment
        os.environ.update(budget_environment(workers=1,threads=4,reserved=0));run()
