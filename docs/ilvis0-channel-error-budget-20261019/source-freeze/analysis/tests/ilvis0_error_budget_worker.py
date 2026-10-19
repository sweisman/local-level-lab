# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite deterministic channel error-budget matrix; never reads archive data."""
import argparse
import csv
import fcntl
import os
from pathlib import Path
import shutil
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_channel_trajectory_worker import environment,sha,load,write
from lll.ilvis0_receipt_journal import durable_write,encoded

NAME='ilvis0-channel-error-budget-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
MODELS=('sphere_rotating','sphere_still','flat_still')
LIMITS=dict(maximum_diagnostic_identities=46,maximum_force_evaluations=6048,
    maximum_constructed_increments=1200,maximum_quadrature_evaluations=3416,
    maximum_observed_starts=0,maximum_native_evaluations=0,maximum_original_reads=0,
    numerical_threads=4,maximum_wall_s=120,retries=0)


def tasks():
    result=[]
    for model in MODELS:
        for degree in (2,4):
            for width in (4,8,16):
                for noise in (1.,50.):
                    result.append(dict(identity=f'trajectory::{model}::p{degree}::w{width}::n{noise:g}',
                        kind='trajectory',model=model,degree=degree,half_window_s=width,noise_multiplier=noise))
    result.extend(dict(identity=f'rotation::{a:g}',kind='rotation',angle_deg=a) for a in (0.,.1,1.,5.,20.,90.))
    result.extend(dict(identity=f'noise::{s:g}',kind='noise',sigma=s) for s in (.001,.01,.1,.5))
    return result


def require_unstarted():
    if (DATA/'start.json').exists() or (DATA/'completion.json').exists():
        raise ValueError('charged or completed diagnostic cannot restart')


def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    if (DATA/'manifest.json').exists():return verify()
    names=['analysis/tests/ilvis0_error_budget_worker.py','analysis/tests/ilvis0_error_budget_controls.py',
        'analysis/tests/ilvis0_channel_reference.py','analysis/tests/ilvis0_channel_trajectory_worker.py',
        'analysis/tests/test_ilvis0_error_budget.py','analysis/tests/test_ilvis0_error_budget_worker.py',
        'analysis/tests/test_ilvis0_receiver_derivatives.py','analysis/tests/test_ilvis0_nonlinear_response.py',
        'analysis/tests/run_numerical.py','analysis/lll/compute_budget.py','analysis/lll/models.py',
        'analysis/lll/ilvis0_receiver_derivatives.py','analysis/lll/ilvis0_receiver_force.py',
        'analysis/lll/ilvis0_channel_controls.py','analysis/lll/ilvis0_nonlinear_response.py',
        'analysis/lll/ilvis0_receipt_journal.py','docs/'+NAME+'/PLAN.md']
    sources={name:sha(ROOT/name) for name in names}
    for name in names:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version='channel-error-budget-v1',sources=sources,
        environment=environment(),tasks=tasks(),limits=LIMITS,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS))
    return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['tasks']!=tasks() or manifest['limits']!=LIMITS:
        raise ValueError('frozen environment, tasks or allowance changed')
    if load(DATA/'authorization.json')['manifest_sha256']!=sha(DATA/'manifest.json'):
        raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:
            raise ValueError('frozen source changed: '+name)
    return manifest


def publish():
    summary=load(DATA/'summary.json');complete=load(DATA/'completion.json')
    if (complete['manifest_sha256']!=sha(DATA/'manifest.json')
            or complete['summary_sha256']!=sha(DATA/'summary.json')):
        raise ValueError('sealed completion changed')
    names=['manifest.json','authorization.json','summary.json','completion.json','start.json']
    full=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('sealed result changed')
        names.extend((row['artifact'],row['charge']));full.append(load(DATA/row['artifact']))
    for name in names:
        destination=PUBLIC/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,destination)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    header=['identity','reference_model','degree','half_window_s','noise_multiplier','candidate',
        'trajectory_bias_mps2','linear_sigma','cubature_sigma','mean_shift','relative_gradient_disagreement',
        'relative_sigma_difference','mean_shift_over_linear_sigma','truncation_over_linear_sigma',
        'linear_screen_passed','truncation_screen_passed','screen_passed']
    with (PUBLIC/'trajectory-candidates.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=header);writer.writeheader()
        for row in full:
            if row['kind']!='trajectory':continue
            for model,response in row['candidates'].items():
                writer.writerow(dict(identity=row['identity'],reference_model=row['model'],degree=row['degree'],
                    half_window_s=row['half_window_s'],noise_multiplier=row['noise_multiplier'],candidate=model,
                    **{name:response[name] for name in header[6:]}))
    trajectories=[r for r in full if r['kind']=='trajectory']
    responses=[v for r in trajectories for v in r['candidates'].values()]
    lines=['# Channel error-budget diagnostic','',
        f"Completed **46/46 diagnostic identities** in {summary['elapsed_s']:.2f} seconds. Implementation checks passed for {sum(r['passed'] for r in summary['results'])}/46. No original measurements, native integrations or observed fits were used.",'',
        f"Of 108 candidate/trajectory checks, {sum(r['linear_screen_passed'] for r in responses)} pass the local-linearity screen and {sum(r['truncation_screen_passed'] for r in responses)} pass the trajectory-truncation screen; {sum(r['screen_passed'] for r in responses)} pass both. These are assumed-error development screens, not scientific detections or calibrated coverage.",'',
        '[All candidate results](trajectory-candidates.csv) retain every model and window. Noise levels are declared control assumptions, not measured receiver performance. No window is selected from these results.','',
        '## Acceleration averaging','',
        '| Rotation in one second (degrees) | Mean-packet loss (m/s²) | Summed-vector loss (m/s²) |',
        '|---:|---:|---:|']
    for row in full:
        if row['kind']=='rotation':lines.append(f"| {row['angle_deg']:g} | {row['packet_integration_loss_mps2']:.8g} | {row['uncorrected_vector_average_loss_mps2']:.8g} |")
    lines+=['','These exact rotating-force integrals show that averaging body vectors and averaging their magnitudes are different operations. Neither becomes an exact instantaneous force without a timing/averaging model.','',
        '## Noise bias in magnitudes','',
        '| Assumed isotropic noise σ (m/s²) | Magnitude bias (m/s²) | Small-noise prediction (m/s²) |',
        '|---:|---:|---:|']
    for row in full:
        if row['kind']=='noise':lines.append(f"| {row['sigma_mps2']:g} | {row['bias_order9_mps2']:.8g} | {row['small_noise_prediction_mps2']:.8g} |")
    lines+=['','Averaging more magnitudes does not remove this nonlinear mean shift. Actual noise, calibration, quantization and correlation still need an observational model.','',
        'The main 53-stretch findings and the earlier unresolved height-removal sensitivity result are unchanged. These controls do not qualify a new recorded-data likelihood.','',
        '[Frozen matrix and limits](PLAN.md) · [Next gate](NEXT_PLAN.md) · [Measurement contributions](../ilvis0-measurement-contribution/README.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name)
        for name in names+['README.md','PLAN.md','trajectory-candidates.csv']}))


def run():
    manifest=prepare()
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);require_unstarted()
        write(DATA/'start.json',dict(manifest_sha256=sha(DATA/'manifest.json')))
        from ilvis0_error_budget_controls import trajectory_control,rotation_control,noise_control
        begun=time.monotonic();rows=[];counts=dict(force_evaluations=0,constructed_increments=0,quadrature_evaluations=0)
        def timeout(*_):raise TimeoutError('finite 120-second allowance exhausted')
        previous=signal.signal(signal.SIGALRM,timeout);signal.alarm(120)
        try:
            for i,task in enumerate(manifest['tasks'],1):
                verify();kind=task['kind'];charge=f'charges/{i:03d}.json';(DATA/'charges').mkdir(exist_ok=True)
                allowance=dict(force_evaluations=168 if kind=='trajectory' else 0,
                    constructed_increments=200 if kind=='rotation' else 0,
                    quadrature_evaluations=854 if kind=='noise' else 0)
                durable_write(DATA/charge,encoded(dict(task,manifest_sha256=sha(DATA/'manifest.json'),allowance=allowance)))
                write(DATA/'status.json',dict(state='software_controls',pid=os.getpid(),total=46,completed=len(rows),
                    allocated_numerical_threads=4,identity=task['identity']))
                if kind=='trajectory':result=trajectory_control(task)
                elif kind=='rotation':result=dict(task,**rotation_control(task['angle_deg']))
                else:result=dict(task,**noise_control(task['sigma']))
                for name,limit in allowance.items():
                    actual=result.get(name,0)
                    if actual!=limit:raise ValueError('formula accounting mismatch: '+name)
                    counts[name]+=actual
                filename=task['identity'].replace('::','--')+'.json';durable_write(DATA/filename,encoded(result))
                rows.append(dict(identity=task['identity'],kind=kind,passed=result['passed'],
                    artifact=filename,artifact_sha256=sha(DATA/filename),charge=charge))
            verify();summary=dict(state='complete',results=rows,passed=all(r['passed'] for r in rows),
                elapsed_s=time.monotonic()-begun,native_evaluations=0,observed_starts=0,original_reads=0,
                scientific_decision='abstain',main_findings_changed=False,**counts)
            write(DATA/'summary.json',summary)
            write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
            write(DATA/'status.json',dict(state='complete',total=46,completed=46,allocated_numerical_threads=0))
        except BaseException as error:
            write(DATA/'failure.json',dict(error=type(error).__name__+': '+str(error),completed=len(rows)));raise
        finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
    publish();print(f"Completed {len(rows)} identities; implementation checks passed {sum(r['passed'] for r in rows)}/46; zero observed fits.")


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true')
    args=parser.parse_args()
    if args.package_only:publish()
    elif args.prepare_only:prepare()
    else:
        from lll.compute_budget import environment as budget_environment
        os.environ.update(budget_environment(workers=1,threads=4,reserved=0));run()
