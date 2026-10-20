# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite exact-oracle common-clock controls, without native integration."""
import argparse
from fractions import Fraction as F
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
from lll.ilvis0_correlated_clock import PrefixClock

NAME='ilvis0-correlated-clock-controls-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-correlated-clock-controls'
TASKS=[dict(identity=f'clock-{family}-{i}',kind=family,variant=i,packets=(16,64,128,400)[i%4])
    for family in ('dyadic','rounded','variable') for i in range(8)]
LIMITS=dict(base.LIMITS,maximum_identities=24,maximum_native_evaluations=0,maximum_packet_visits=0,
    maximum_prefix_appends=9600,maximum_oracle_points=24000,maximum_oracle_terms=9600000,maximum_wall_s=120)
SOURCE_NAMES=base.SOURCE_NAMES+['analysis/lll/ilvis0_correlated_clock.py','analysis/tests/test_ilvis0_correlated_clock.py',
    'analysis/tests/ilvis0_correlated_clock_worker.py','analysis/tests/test_ilvis0_correlated_clock_worker.py',
    'docs/ilvis0-correlated-clock-controls/PLAN.md','docs/ilvis0-clock-correlation/PLAN.md']


def evaluate(task,directory,charge):
    n=task['packets'];variant=task['variant'];family=task['kind'];started=time.monotonic()
    base.write(DATA/'reservations'/(task['identity']+'.json'),dict(identity=task['identity'],prefix_appends=400,
        oracle_points=1000,oracle_terms=400000,maximum_bits=8192,maximum_seconds=10))
    durations=[(1/256 if variant<4 else 1/128) if family=='dyadic' else
        (.005 if variant<4 else 1/300) if family=='rounded' else (.003,.005,.0075)[j%3] for j in range(n)]
    physical=sum((F(dt) for dt in durations),F(0));mode=variant%4
    center,lower,upper=((physical/2,physical/4,physical*3/4),(F(0),F(0),physical/4),
        (physical,physical*3/4,physical),(physical,physical*3/4,physical*5/4))[mode]
    upstream=F(1,1000000) if variant%2 else F(0)
    model=PrefixClock(center,lower,upper,time_remainder=upstream,maximum_packets=n,maximum_bits=8192,maximum_seconds=5)
    packets=[];elapsed=0.;snapshots=[]
    for i,duration in enumerate(durations):
        packets.append((F(elapsed),F(duration)));elapsed+=duration;result=model.append(duration)
        if i+1 in (1,n//2,n):snapshots.append((packets.copy(),result))
    count=0;maximum_error=F(0)
    for prefix,result in snapshots:
        f=lambda t:sum((min(max(t-s,F(0)),dt) for s,dt in prefix),F(0))
        points={lower,center,upper};points.update(lower+(upper-lower)*F(k,16) for k in range(17))
        points.update(t for s,dt in prefix for t in (s,s+dt) if lower<=t<=upper)
        selected=sum(int(s<center<=s+dt or s==center==0) for s,dt in prefix)
        if (result.center!=f(center) or result.lower!=f(lower) or result.upper!=f(upper) or result.slope!=selected):
            raise ValueError('exact prefix center/endpoints/slope differ from independent oracle')
        for point in sorted(points):
            count+=1
            if count>1000 or time.monotonic()-started>=10:raise ValueError('finite oracle allowance exhausted')
            value=f(point);error=abs(value-result.center-selected*(point-center));maximum_error=max(maximum_error,error)
            if not result.lower<=value<=result.upper or error+abs(selected)*upstream>result.remainder:
                raise ValueError('independent exact clock point escaped its bound')
    result=snapshots[-1][1]
    if upper<=physical and family=='dyadic' and result.slope==1 and result.remainder!=upstream:
        raise ValueError('exact dyadic clock retained a spurious independent kink remainder')
    if lower>0 and upper<physical and result.slope==1 and result.remainder>2*result.clock_defect+upstream:
        raise ValueError('interior clock did not retain correlated defect bound')
    return dict(identity=task['identity'],kind=family,passed=True,packets=n,oracle_points=count,
        center=str(center),lower=str(lower),upper=str(upper),upstream_time_remainder_s=float(upstream),
        correlated_remainder_s=float(result.remainder),independent_remainder_s=float(result.independent_remainder),
        clock_defect_s=float(result.clock_defect),maximum_exact_oracle_error_s=float(maximum_error),
        exact_correlated_remainder=str(result.remainder),elapsed_s=time.monotonic()-started,
        original_reads=0,native_evaluations=0,optimizer_starts=0,whole_program_roundoff_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


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
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-correlated-clock-controls/PLAN.md',PUBLIC/'PLAN.md')
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    lines=['# Correlated packet-clock controls','',f"{sum(r['passed'] for r in rows)}/{len(manifest['tasks'])} generated controls pass; state: {summary['state']}.",'',
        '| Family | Completed | Passed | Exact oracle points |','|---|---:|---:|---:|']
    for family in ('dyadic','rounded','variable'):
        selected=[r for r in rows if r['kind']==family]
        lines.append(f"| {family} | {len(selected)} | {sum(r['passed'] for r in selected)} | {sum(r.get('oracle_points',0) for r in selected)} |")
    lines+=['','One common offset is retained across all packets, including selected one-sided boundary slopes. '
        'Exact oracle checks include every relevant knot of the inspected prefixes. '
        'The supplied upstream time-map remainder remains part of the bound.','',
        'This qualifies the mathematical clipped-period map, not an actual instrument clock or whole-program floating-point behavior. '
        'No native integration, original files or observed model fitting is performed. '
        'Regrouped native propagation needs a separate qualification.','',
        '[Frozen controls](PLAN.md) · [Mathematical method and native next gate](../ilvis0-clock-correlation/PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:base.prepare();print('Frozen 24 exact common-clock controls.')
    elif args.run:base.run();print('Common-clock qualification finished.')
    elif args.package_only:publish();print('Published saved clock controls.')
    else:base.verify();print('Verified common-clock freeze/results.')


if __name__=='__main__':main()
