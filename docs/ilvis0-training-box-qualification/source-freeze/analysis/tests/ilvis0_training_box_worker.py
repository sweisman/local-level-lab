# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite rational-oracle qualification of affine necessary constraints."""
import argparse
from fractions import Fraction
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with four threads')
import ilvis0_streaming_worker as base

NAME='ilvis0-training-box-qualification-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-training-box-qualification'
TASKS=[dict(identity=f'box-{i:02d}',kind=kind,variant=i,rows=27,parameters=27,
    reserved_oracle_points=64,maximum_passes=8) for i,kind in enumerate(['exact']*4+['empty']*4+['weak']*4+['coupled']*12)]
LIMITS=dict(base.LIMITS,maximum_identities=24,maximum_native_evaluations=0,maximum_packet_visits=0,
    maximum_contractions=24,maximum_constraint_rows=648,maximum_exact_oracle_points=1536,maximum_passes_per_contraction=8,maximum_wall_s=60)
SOURCE_NAMES=base.SOURCE_NAMES+['analysis/lll/ilvis0_training_box.py','analysis/tests/test_ilvis0_training_box.py',
    'analysis/tests/ilvis0_training_box_worker.py','analysis/tests/test_ilvis0_training_box_worker.py',
    'docs/ilvis0-training-box-qualification/PLAN.md','docs/ilvis0-native-stream-interface/TRAINING_REGION_PLAN.md']


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_training_box import contract
    if task['rows']!=27 or task['parameters']!=27 or task['maximum_passes']!=8 or task['reserved_oracle_points']!=64:
        raise ValueError('frozen mathematical allowance mismatch')
    base.write(DATA/'affine-reservations'/(task['identity']+'.json'),dict(identity=task['identity'],
        contractions=1,constraint_rows=27,exact_oracle_points=64,maximum_passes=8))
    rng=np.random.default_rng(20261019+task['variant']);a=np.zeros((27,27));left=-np.ones(27);right=np.ones(27)
    points=[];kind=task['kind'];v=task['variant']%4
    if kind=='exact':
        coefficient=(1.,-1.,3.,-7.)[v];a[0,0]=coefficient
        left[0],right[0]=sorted((coefficient*.125,coefficient*.375))
        for value in (.125,.375):
            point=np.zeros(27);point[0]=value;points.append(point)
    elif kind=='empty':
        if v==0:left[0],right[0]=.1,.2
        elif v in (1,2):a[0,0]=1. if v==1 else -1.;left[0],right[0]=2.,3.
        else:a[0,:2]=1.;left[0],right[0]=3.,4.
    elif kind=='weak':
        a=rng.integers(-2,3,size=(27,27))/16.;left[:]=-100.;right[:]=100.
        points=[np.zeros(27),np.ones(27)]
    else:
        truth=rng.integers(-7,8,size=27)/8.
        for j in range(20):a[j,j]=(-1.)**j
        a[20:,:20]=rng.integers(-2,3,size=(7,20))/16.
        target=a@truth;left=target-.125;right=target+.125
        points=[truth+rng.integers(-1,2,size=27)/64. for _ in range(64)]
    # Independent exact-rational evaluation precedes the contractor. Every
    # declared point must be feasible; none may be filtered after contraction.
    for point in points:
        for row,lower,upper in zip(a,left,right):
            exact=sum((Fraction(float(c))*Fraction(float(x)) for c,x in zip(row,point) if c),Fraction(0))
            if not Fraction(float(lower))<=exact<=Fraction(float(upper)):
                raise ValueError('generated declared oracle point is not exactly feasible')
    result=contract(-np.ones(27),np.ones(27),a,left,right,maximum_passes=8)
    retained=0
    for point in points:
        if result['empty']:raise ValueError('exact feasible point excluded as empty')
        for axis,value in enumerate(point):
            if not Fraction(float(result['lower'][axis]))<=Fraction(float(value))<=Fraction(float(result['upper'][axis])):
                raise ValueError('exact feasible coordinate lost')
        retained+=1
    passed=result['empty'] if kind=='empty' else not result['empty']
    if kind=='exact':passed=passed and abs(result['lower'][0]-.125)<=1e-14 and abs(result['upper'][0]-.375)<=1e-14
    if kind=='weak':passed=passed and np.array_equal(result['lower'],-np.ones(27)) and np.array_equal(result['upper'],np.ones(27))
    if kind=='coupled':
        passed=passed and np.array_equal(result['lower'][20:],-np.ones(7)) and np.array_equal(result['upper'][20:],np.ones(7))
        passed=passed and bool(np.all(result['upper'][:20]-result['lower'][:20]<.251))
    return dict(identity=task['identity'],kind=kind,passed=bool(passed),input=dict(design=a,target_lower=left,target_upper=right),
        contraction=result,exact_feasible_points_retained=retained,parameter_count=27,
        narrowed_coordinates=int(np.sum(result['upper']-result['lower']<2.)),
        original_reads=0,native_evaluations=0,optimizer_starts=0,scientific_decision='abstain')


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def publish():
    manifest=base.verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-training-box-qualification/PLAN.md',PUBLIC/'PLAN.md')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    names += ['starts/'+t['identity']+'.json' for t in manifest['tasks'][:summary['charged']['identities']]]
    names += ['affine-reservations/'+r['identity']+'.json' for r in summary['results']]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    lines=['# Conservative affine training constraints','',f"{sum(r['passed'] for r in rows)}/{len(manifest['tasks'])} identities pass; state: {summary['state']}.",'',
        '| Family | Completed | Passed | Exact feasible points retained |','|---|---:|---:|---:|']
    for kind in ('exact','empty','weak','coupled'):
        selected=[r for r in rows if r['kind']==kind]
        lines.append(f"| {kind} | {len(selected)} | {sum(r['passed'] for r in selected)} | {sum(r.get('exact_feasible_points_retained',0) for r in selected)} |")
    lines+=['','All 27 coordinates remain present. Coupled controls preserve seven wholly unidentified columns; '
        'weak systems must remain unchanged, and known contradictions must be explicit. '
        'Every declared feasible point is checked with independent rational arithmetic before contraction.','',
        f"Elapsed {summary['elapsed_s']:.2f} seconds. Zero native evaluations, optimizer starts or archive reads.",'',
        'This verifies a mathematical necessary-constraint component, not measurement error, global nonlinear bounds or observational coverage. '
        'No native uncertainty region has been narrowed. All scientific decisions abstain.','',
        '[Frozen limits](PLAN.md) · [Method and next gate](../ilvis0-native-stream-interface/TRAINING_REGION_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:base.prepare();print('Frozen 24 affine qualification identities.')
    elif args.run:base.run();print('Affine qualification finished.')
    elif args.package_only:publish();print('Published saved affine results.')
    else:base.verify();print('Verified affine freeze/results.')


if __name__=='__main__':main()
