# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite exact shared-scale software qualification, generated observations only."""
import argparse
from fractions import Fraction as F
import math
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_streaming_worker as base
from lll import ilvis0_exact_scale as exact

NAME='ilvis0-exact-scale-qualification-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-exact-scale-qualification'
TASKS=[dict(identity=f'dense-{i}',kind='dense',variant=i,epochs=5) for i in range(8)]
TASKS += [dict(identity=f'prefix-{tau}-{n}',kind='prefix',tau=tau,epochs=n) for tau in (10,300) for n in (32,64,128,292)]
LIMITS=dict(base.LIMITS,maximum_identities=16,maximum_native_evaluations=0,maximum_packet_visits=0,
    maximum_innovation_epochs=1072,maximum_bits=131072,maximum_seconds_per_identity=10,maximum_wall_s=120)
SOURCE_NAMES=base.SOURCE_NAMES+['analysis/lll/ilvis0_exact_scale.py','analysis/tests/test_ilvis0_exact_scale.py',
    'analysis/tests/ilvis0_exact_scale_worker.py','analysis/tests/test_ilvis0_exact_scale_worker.py',
    'docs/ilvis0-exact-scale-qualification/PLAN.md','docs/ilvis0-shared-training-error/PLAN.md']


def dense_quadratic(values,law):
    n=len(values);t=[F(i,n-1) for i in range(n)]
    a=[[law.correlated*law.rho**abs(i-j)+law.offset+law.drift*t[i]*t[j]+(law.white if i==j else 0)
        for j in range(n)]+[values[i]] for i in range(n)]
    for j in range(n):
        pivot=a[j][j];a[j]=[v/pivot for v in a[j]]
        for i in range(n):
            if i!=j:
                factor=a[i][j];a[i]=[x-factor*y for x,y in zip(a[i],a[j])]
    return sum((v*a[i][-1] for i,v in enumerate(values)),F(0))


def evaluate(task,directory,charge):
    n=task['epochs'];started=time.monotonic()
    base.write(DATA/'reservations'/(task['identity']+'.json'),dict(identity=task['identity'],innovation_epochs=n,
        maximum_bits=LIMITS['maximum_bits'],maximum_seconds=LIMITS['maximum_seconds_per_identity']))
    if task['kind']=='dense':
        v=task['variant'];rho=(F(0),F(3,4),F(1),F(7,8))[v%4]
        law=exact.Covariance(rho,F(1,4),F(3,2),F(v%2),F((v//2)%2))
    else:
        rho=F(round(math.exp(-1/task['tau'])*2**24),2**24)
        law=exact.Covariance(rho,F(9,100),F(1),F(1),F(1))
    values=[F((i*7)%17-8,13)+F(i,n-1)**3 for i in range(n)]
    residuals=exact.polynomial_residuals(values,[F(j-3,11) for j in range(8)])
    budget=exact.Budget(maximum_steps=n,maximum_bits=LIMITS['maximum_bits'],maximum_seconds=10)
    q=exact.residual_quadratic(residuals,law,budget=budget)
    dense_match=q==dense_quadratic(residuals,law) if task['kind']=='dense' else None
    # The tiny dense cases use an auxiliary 20-dimensional tail certificate;
    # they do not claim a five-epoch degree-seven fit has residual degrees.
    report=exact.scale_upper(q,observations=max(20,n),reference_columns=8,alpha=F(1,100))
    certificate=report['quantile'];passed=(q>=0 and dense_match is not False and certificate['tail_bound']<=F(1,100)
        and F(report['upper'])**2*certificate['q']>=q and time.monotonic()-started<10)
    return dict(identity=task['identity'],kind=task['kind'],passed=bool(passed),epochs=n,
        rho=str(law.rho),quadratic=str(q),quadratic_numerator_bits=q.numerator.bit_length(),
        quadratic_denominator_bits=q.denominator.bit_length(),dense_exact_match=dense_match,
        scale_upper=report['upper'],quantile_floor=str(certificate['q']),moment=certificate['k'],
        exact_tail_bound=str(certificate['tail_bound']),elapsed_s=time.monotonic()-started,
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
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-exact-scale-qualification/PLAN.md',PUBLIC/'PLAN.md')
    lines=['# Exact shared-error arithmetic','',f"{sum(r['passed'] for r in summary['results'])}/{len(manifest['tasks'])} controls pass; state: {summary['state']}.",'',
        '| Identity | Epochs | Passed | Runtime | Rational numerator bits |','|---|---:|---|---:|---:|']
    for record in summary['results']:
        r=base.load(DATA/record['artifact']);lines.append(f"| {r['identity']} | {r.get('epochs','—')} | {r['passed']} | {r.get('elapsed_s',0):.3f} s | {r.get('quadratic_numerator_bits','—')} |")
    lines+=['','The supplied Gaussian covariance law remains an assumption. Exact arithmetic checks its calculation, not actual receiver accuracy. '
        'No original IMU files, Earth-model fits or protected ESA observations are read. Broad nonlinear prediction ranges remain a separate block.','',
        '[Frozen allowance](PLAN.md) · [Source assessment plan](../ilvis0-shared-training-error/PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:base.prepare();print('Frozen sixteen exact-arithmetic software identities.')
    elif args.run:base.run();print('Exact-arithmetic qualification finished.')
    elif args.package_only:publish();print('Published saved exact-arithmetic controls.')
    else:base.verify();print('Verified exact-arithmetic source freeze and results.')


if __name__=='__main__':main()
