# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen receiver-only error-source assessment, no new Earth-model fitting."""
import argparse
import csv
import gzip
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_streaming_worker as base
from lll import ilvis0_receiver_scale as receiver

NAME='ilvis0-receiver-scale-assessment-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-receiver-scale-assessment'
SEGMENT='570b37d23af5e245dd461051';TRAINING_EPOCHS=292
TASKS=[dict(identity=f'receiver-{tau}-degree{degree}',kind='receiver-scale',tau=tau,degree=degree)
    for tau in (10,300) for degree in (3,5,7)]
LIMITS=dict(base.LIMITS,maximum_identities=6,maximum_native_evaluations=0,maximum_packet_visits=0,
    maximum_innovation_epochs=5256,maximum_bits=131072,maximum_seconds_per_axis=10,maximum_seconds_per_identity=30,maximum_wall_s=240)
SOURCE_NAMES=base.SOURCE_NAMES+['analysis/lll/ilvis0_exact_scale.py','analysis/lll/ilvis0_receiver_scale.py',
    'analysis/tests/test_ilvis0_receiver_scale.py','analysis/tests/ilvis0_receiver_scale_worker.py',
    'analysis/tests/test_ilvis0_receiver_scale_worker.py','docs/ilvis0-receiver-scale-assessment/PLAN.md']


def prefix(selected,epochs):
    fixes=selected['segment']['receiver_fixes'][:epochs]
    if len(fixes)!=epochs:raise ValueError('insufficient saved training prefix')
    return dict(filename=selected['filename'],segment_id=selected['segment']['segment_id'],
        fixes=[{k:row[k] for k in ('time_s','latitude_rad','longitude_rad','height_m')} for row in fixes])


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    if DATA.exists():raise ValueError('freeze exists; never overwrite')
    qualification=ROOT/'docs/ilvis0-exact-scale-v2'
    for name,digest in base.load(qualification/'evidence-receipt.json')['artifacts'].items():
        if base.sha(qualification/name)!=digest:raise ValueError('mathematical qualification artifact changed')
    if not base.load(qualification/'summary.json')['passed']:raise ValueError('mathematical qualification did not pass')
    prior=base.load(qualification/'manifest.json')
    if base.sha(ROOT/'analysis/lll/ilvis0_exact_scale.py')!=prior['sources']['analysis/lll/ilvis0_exact_scale.py']:
        raise ValueError('qualified arithmetic changed')
    archive=ROOT/'docs/ilvis0-highspeed-segments-20261008';receipt=base.load(archive/'evidence-receipt.json')['artifacts']
    for name in ('selection.json.gz','eligible-stretches.csv'):
        if base.sha(archive/name)!=receipt[name]:raise ValueError('saved receiver selection changed')
    selection=base.load(archive/'selection.json.gz')
    selected=[r for r in selection['selected'] if r['segment']['segment_id']==SEGMENT]
    if len(selected)!=1:raise ValueError('saved training identity ambiguous')
    training=prefix(selected[0],TRAINING_EPOCHS)
    rows=list(csv.DictReader(io.StringIO((archive/'eligible-stretches.csv').read_text())))
    record=[r for r in rows if r['segment_id']==SEGMENT]
    if len(record)!=1 or record[0]['filename']!=training['filename']:raise ValueError('source metadata mismatch')
    if len(selected[0]['segment']['receiver_fixes'])!=439 or training['fixes'][0]['time_s']!=132350.:
        raise ValueError('training receiver grid identity changed')
    receiver.training_chart(training['fixes'],expected_epochs=TRAINING_EPOCHS)
    provenance=dict(segment_id=SEGMENT,filename=training['filename'],source_sha256=record[0]['source_sha256'],
        parent_selection_sha256=receipt['selection.json.gz'],training_epochs=TRAINING_EPOCHS,
        first_time_s=training['fixes'][0]['time_s'],last_time_s=training['fixes'][-1]['time_s'],
        qualification_manifest_sha256=base.sha(qualification/'manifest.json'),later_positions_in_input=False)
    inputs={}
    for name,value in (('training',training),('provenance',provenance)):
        path='inputs/'+name+'.json';base.write(DATA/path,value);inputs[name]=dict(path=path,sha256=base.sha(DATA/path))
    for name in SOURCE_NAMES:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    base.write(DATA/'manifest.json',dict(version=NAME,tasks=TASKS,limits=LIMITS,inputs=inputs,provenance=provenance,
        environment=base.environment(),numerical_environment=environment(threads=4),sources={n:base.sha(ROOT/n) for n in SOURCE_NAMES},
        compilers={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('cc','c++')}))
    base.write(DATA/'authorization.json',dict(scope='standing V01 receiver-only retrospective source assessment; no Earth-model fits',
        limits=LIMITS,manifest_sha256=base.sha(DATA/'manifest.json')))


def verify(current=False):
    manifest=base.verify(current=current)
    for record in manifest['inputs'].values():
        if base.sha(DATA/record['path'])!=record['sha256']:raise ValueError('frozen training input changed')
    return manifest


def evaluate(task,directory,charge):
    manifest=verify();training=base.load(DATA/manifest['inputs']['training']['path'])
    n=manifest['provenance']['training_epochs']
    base.write(DATA/'reservations'/(task['identity']+'.json'),dict(identity=task['identity'],innovation_epochs=3*n,
        maximum_bits=131072,maximum_seconds=30))
    chart=receiver.training_chart(training['fixes'],expected_epochs=n)
    result=receiver.assess(chart,degree=task['degree'],tau=task['tau'],maximum_seconds=30)
    return dict(result,identity=task['identity'],kind=task['kind'],passed=True,
        original_reads=0,native_evaluations=0,optimizer_starts=0)


def publish():
    manifest=verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    names += [r['path'] for r in manifest['inputs'].values()]
    charged=manifest['tasks'][:summary['charged']['identities']]
    names += ['starts/'+t['identity']+'.json' for t in charged]+['reservations/'+t['identity']+'.json' for t in charged]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-receiver-scale-assessment/PLAN.md',PUBLIC/'PLAN.md')
    results=[base.load(DATA/r['artifact']) for r in summary['results']]
    lines=['# Training-only receiver-reference assessment','',
        f"{sum(r['passed'] for r in results)}/{len(manifest['tasks'])} calculations complete; state: {summary['state']}.",'',
        'Uses only the predeclared training GPS positions of one previously studied recording. '
        'Every scale is an upper bound under its stated Gaussian covariance law, not measured receiver accuracy. '
        'No Earth candidate supplies these residuals, and no later receiver position enters the calculation.','',
        '| Approximate correlation time | Polynomial degree | Common scale upper bound | Reference RMS N / E / height (chart metres) | Runtime |',
        '|---|---:|---:|---:|---:|']
    for r in results:
        rms=' / '.join(f"{a['reference_residual_rms_chart_m']:.3f}" for a in r.get('axes',[]))
        lines.append(f"| {r.get('tau_approx_s','—')} s | {r.get('degree','—')} | {r.get('scale_upper',float('nan')):.3f} | {rms} | {r.get('elapsed_s',0):.2f} s |")
    lines+=['','The scale multiplies all declared standard deviations together. A poorly approximated aircraft path may inflate it. '
        'The fixed chart and two discrete covariance shapes differ from the older geographic residual objective; these bounds cannot '
        'be inserted into that objective automatically. Each calculation uses a 1% assumed-law failure probability; '
        'simultaneous observational coverage and the Gaussian law itself remain unestablished.','',
        'No new IMU (inertial measurement unit) observations, native predictions, Earth-model fits or protected ESA outcomes are read. '
        'Broad nonlinear propagation bounds still block new qualified prediction fits. All scientific decisions abstain.','',
        '[Frozen scope and source identity](PLAN.md) · [Mathematics](../ilvis0-exact-scale-v2/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six training-only receiver-source assessments.')
    elif args.run:verify(True);base.run();print('Training-only receiver-source assessment finished.')
    elif args.package_only:publish();print('Published saved assessments without recalculation.')
    else:verify();print('Verified training-only receiver-source freeze and results.')


if __name__=='__main__':main()
