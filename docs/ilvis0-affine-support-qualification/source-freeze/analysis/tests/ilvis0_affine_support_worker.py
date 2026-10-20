# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite exact-oracle joint affine support controls; no native predictions."""
import argparse
from fractions import Fraction as F
from itertools import combinations
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_streaming_worker as base
from lll import ilvis0_affine_support as support

NAME='ilvis0-affine-support-qualification-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-affine-support-qualification'
TASKS=[dict(identity=f'support-{i:02d}',kind=kind,variant=i) for i,kind in enumerate(['polygon']*12+['correlated']*8+['fallback']*4)]
LIMITS=dict(base.LIMITS,maximum_identities=24,maximum_native_evaluations=0,maximum_packet_visits=0,
    maximum_certificates=144,maximum_lp_proposals=48,maximum_wall_s=60)
SOURCE_NAMES=base.SOURCE_NAMES+['analysis/lll/ilvis0_affine_support.py','analysis/tests/test_ilvis0_affine_support.py',
    'analysis/tests/ilvis0_affine_support_worker.py','analysis/tests/test_ilvis0_affine_support_worker.py',
    'docs/ilvis0-affine-support-qualification/PLAN.md','docs/ilvis0-native-training-contraction/JOINT_PLAN.md']


def vertices(design,bound):
    """Independent two-dimensional exact vertex enumeration on [-1,1]^2."""
    a=[[F(float(v)) for v in row] for row in design]+[[F(1),F(0)],[-F(1),F(0)],[F(0),F(1)],[F(0),-F(1)]]
    b=[F(float(v)) for v in bound]+[F(1)]*4;points=set()
    for i,j in combinations(range(len(a)),2):
        determinant=a[i][0]*a[j][1]-a[i][1]*a[j][0]
        if not determinant:continue
        point=((b[i]*a[j][1]-a[i][1]*b[j])/determinant,(a[i][0]*b[j]-b[i]*a[j][0])/determinant)
        if all(sum(x*y for x,y in zip(row,point))<=value for row,value in zip(a,b)):points.add(point)
    return sorted(points)


def evaluate(task,directory,charge):
    import numpy as np
    base.write(DATA/'reservations'/(task['identity']+'.json'),dict(identity=task['identity'],certificates=6,lp_proposals=2))
    rng=np.random.default_rng(9321+task['variant']);kind=task['kind'];oracle_points=0
    if kind=='polygon':
        a=rng.integers(-4,5,size=(6,2))/4.;b=rng.integers(1,5,size=6)/4.;c=rng.integers(-8,9,size=2)/4.
        points=vertices(a,b);oracle_points=len(points)
        if not points:raise ValueError('declared feasible polygon unexpectedly empty')
        projections=[sum(F(float(x))*y for x,y in zip(c,point)) for point in points]
        exact_lower,exact_upper=min(projections),max(projections);n=2
    elif kind=='correlated':
        n=27;a=np.zeros((2,n));a[0,:2]=[1.,-1.];a[1,:2]=[-1.,1.];b=np.zeros(2)
        c=rng.integers(-4,5,size=n)/4.;c[:2]=[1.,-1.]
        exact_upper=sum((abs(F(float(v))) for v in c[2:]),F(0));exact_lower=-exact_upper
    else:
        n=27;a=np.zeros((1,n));b=np.ones(1);c=rng.integers(-4,5,size=n)/4.
        exact_upper=sum((abs(F(float(v))) for v in c),F(0));exact_lower=-exact_upper
    lo=-np.ones(n);hi=np.ones(n)
    if kind=='fallback':
        high=support.upper(lo,hi,a,b,c,np.zeros(len(b)))
        low=support.upper(lo,hi,a,b,-c,np.zeros(len(b)))
    else:
        high=support.propose(lo,hi,a,b,c);low=support.propose(lo,hi,a,b,-c)
    poor=support.upper(lo,hi,a,b,c,rng.integers(0,4,size=len(b))/4.)
    passed=(high['exact_upper']>=exact_upper and low['exact_upper']>=-exact_lower
        and F(high['upper'])>=exact_upper and F(-low['upper'])<=exact_lower and poor['exact_upper']>=exact_upper)
    # Rational dyadic examples should attain their exact support (up to endpoint
    # rounding); loose proposals are tested separately, never accepted as optima.
    if kind in ('correlated','fallback'):passed=passed and high['exact_upper']==exact_upper and low['exact_upper']==-exact_lower
    return dict(identity=task['identity'],kind=kind,passed=bool(passed),parameter_count=n,
        exact_oracle_lower=str(exact_lower),exact_oracle_upper=str(exact_upper),exact_vertices=oracle_points,
        certified_lower=-low['upper'],certified_upper=high['upper'],poor_proposal_upper=poor['upper'],
        certificate_high=str(high['exact_upper']),certificate_low_negated=str(low['exact_upper']),
        design=a,bound=b,objective=c,upper_multipliers=high['multipliers'],lower_multipliers=low['multipliers'],
        original_reads=0,native_evaluations=0,optimizer_starts=0,observational_coverage_qualified=False,scientific_decision='abstain')


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def publish():
    manifest=base.verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    charged=manifest['tasks'][:summary['charged']['identities']]
    names += ['starts/'+t['identity']+'.json' for t in charged]+['reservations/'+t['identity']+'.json' for t in charged]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-affine-support-qualification/PLAN.md',PUBLIC/'PLAN.md')
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    lines=['# Joint affine support certificates','',f"{sum(r['passed'] for r in rows)}/{len(manifest['tasks'])} identities pass; state: {summary['state']}.",'',
        '| Family | Completed | Passed | Exact polygon vertices checked |','|---|---:|---:|---:|']
    for kind in ('polygon','correlated','fallback'):
        selected=[r for r in rows if r['kind']==kind]
        lines.append(f"| {kind} | {len(selected)} | {sum(r['passed'] for r in selected)} | {sum(r.get('exact_vertices',0) for r in selected)} |")
    lines+=['','Certificates use exact arithmetic after a numerical LP proposes nonnegative multipliers. '
        'An unsuccessful or invalid proposal falls back to a full-box certificate. '
        'Twenty-five unidentified coordinates remain in the correlated controls; none is deleted.','',
        'This tests supplied linear inequalities, not actual aircraft calibration regions. '
        'Nonlinear remainder width, numerical error and observational assumptions remain separate gates. '
        'Zero native evaluations, archive reads or Earth-model fits.','',
        '[Frozen controls](PLAN.md) · [Joint calibration method and next gate](../ilvis0-native-training-contraction/JOINT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:base.prepare();print('Frozen 24 exact joint-support identities.')
    elif args.run:base.run();print('Joint-support qualification finished.')
    elif args.package_only:publish();print('Published saved support certificates.')
    else:base.verify();print('Verified joint-support source freeze/results.')


if __name__=='__main__':main()
