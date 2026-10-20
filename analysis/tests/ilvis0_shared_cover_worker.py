# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite complete orientation cover with a single shared error block."""
import argparse
import ctypes
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_orientation_cover_worker as predecessor
base=predecessor.base
from lll import ilvis0_shared_sector_experiment as experiment,ilvis0_shared_native as shared
from lll import ilvis0_shared_envelope

NAME='ilvis0-shared-cover-20261020';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-shared-cover'
TASKS=[dict(t,identity='shared-'+t['identity']) for t in predecessor.TASKS]
LIMITS=dict(predecessor.LIMITS,maximum_native_evaluations=144,maximum_packet_visits=57600,maximum_wall_s=900)
SOURCE_NAMES=predecessor.SOURCE_NAMES+['analysis/lll/'+n for n in (
    'ilvis0_shared_sector_experiment.py','ilvis0_shared_envelope.py','ilvis0_shared_native.py',
    'ilvis0_shared_reference_terms.py','ilvis0_correlated_clock.py','ilvis0_regrouped_history.py')]
SOURCE_NAMES+=['analysis/tests/test_ilvis0_shared_sector_experiment.py','analysis/tests/test_ilvis0_shared_envelope.py',
    'analysis/tests/ilvis0_shared_cover_worker.py','analysis/tests/test_ilvis0_shared_cover_worker.py',
    'docs/ilvis0-shared-cover/PLAN.md','docs/ilvis0-regrouped-cover/case-unions.json']
for q in ('ilvis0-shared-native-controls','ilvis0-shared-envelope-controls'):
    SOURCE_NAMES += ['docs/'+q+'/'+n for n in ('manifest.json','summary.json','completion.json')]


def configure():
    predecessor.NAME=NAME;predecessor.DATA=DATA;predecessor.PUBLIC=PUBLIC;predecessor.TASKS=TASKS
    predecessor.LIMITS=LIMITS;predecessor.SOURCE_NAMES=SOURCE_NAMES
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    for q in ('ilvis0-shared-native-controls','ilvis0-shared-envelope-controls'):
        directory=ROOT/'docs'/q;manifest=base.load(directory/'manifest.json')
        for name,digest in base.load(directory/'evidence-receipt.json')['artifacts'].items():
            if base.sha(directory/name)!=digest:raise ValueError('prerequisite artifact changed')
        if not base.load(directory/'summary.json')['passed'] or base.environment()!=manifest['environment']:
            raise ValueError('prerequisite failed or environment changed')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/') and base.sha(ROOT/name)!=digest:
                raise ValueError('qualified component changed: '+name)
    predecessor.prepare();manifest=verify();old=base.load(ROOT/'docs/ilvis0-regrouped-cover/manifest.json')
    for task in TASKS:
        if task['packets']==400:
            key=predecessor.case_key(task)
            if manifest['inputs'][key]['sha256']!=old['inputs'][key]['sha256']:
                raise ValueError('matched generated input changed')


def verify(current=False):
    manifest=predecessor.verify(current)
    if (DATA/'completion.json').exists():
        for row in base.load(DATA/'summary.json')['results']:
            for name,digest in base.load(DATA/row['artifact']).get('extra_artifacts',{}).items():
                if base.sha(DATA/name)!=digest:raise ValueError('shared side artifact changed')
    return manifest


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_orientation_cover import sector
    manifest=verify();case=base.load(DATA/manifest['inputs'][predecessor.case_key(task)]['path']);config=case['configuration']
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    case=dict(case,configuration=config);theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt'])
    n=len(dt)
    if n!=task['packets'] or config['model']!=task['model'] or config['profile']!=task['profile']:
        raise ValueError('generated candidate/input identity mismatch')
    box=sector(task['sector']);reference=shared.make_reference(config,theta,dv,dt,
        lower=box['lower'],upper=box['upper'],center=box['center'])
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.]);kernel,kernel_identity=load_tangent(directory)
    calls=0;bounds=0;maximum=0.;extra={}
    def save(name,value):base.write(DATA/name,value);extra[name]=base.sha(DATA/name)
    def native(times,point):
        nonlocal calls
        if calls>=3:raise ValueError('per-sector native allowance exhausted')
        times=np.ascontiguousarray(times,dtype=float);out=np.empty((len(times),3));jac=np.empty((len(times)*3,27));warning=ctypes.c_int()
        charge(native_calls=1,packet_visits=n);calls+=1
        code=kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native shared query outside support')
        save('native/'+task['identity']+f'-{calls:02d}.json.gz',dict(times=times,point=point,prediction=out,jacobian=jac,warning=warning.value))
        return out,jac.reshape(len(times),3,27)
    def bound(time,lo,hi,position):
        nonlocal bounds,maximum
        if bounds>=8:raise ValueError('per-sector bound allowance exhausted')
        bounds+=1;suffix=task['identity']+f'-{bounds:02d}'
        base.write(DATA/'bound-reservations'/(suffix+'.json'),dict(identity=suffix,time_s=float(time),maximum_packet_steps=n))
        report=shared.enclose(config,theta,dv,dt,time=float(time),lower=lo,upper=hi,reference=reference)
        error=float(np.max(abs((report.center-position)*scale)));maximum=max(maximum,error)
        base.write(DATA/'bounds'/(suffix+'.json.gz'),dict(report.report(),reference=reference.report(),native_center_difference_m=error))
        return report
    def emit(label,value):
        if label not in ('training','future'):raise ValueError('unexpected evidence identity')
        save('evidence/'+task['identity']+'-'+label+'.json.gz',value)
    result=experiment.evaluate(task,case,reference=reference,native=native,bound=bound,emit=emit)
    return dict(result,passed=result['passed'] and maximum<=1e-6,kernel=kernel_identity,
        maximum_center_difference_m=maximum,bound_evaluations=bounds,native_evaluations=calls,
        reserved_bound_steps=bounds*n,extra_artifacts=extra)


def publish():
    import numpy as np
    verify();predecessor.publish();summary=base.load(DATA/'summary.json');receipt=base.load(PUBLIC/'evidence-receipt.json')
    for row in summary['results']:
        for name in base.load(DATA/row['artifact']).get('extra_artifacts',{}):
            target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
            receipt['artifacts'][name]=base.sha(target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-shared-cover/PLAN.md',PUBLIC/'PLAN.md')
    previous=base.load(DATA/'source-freeze/docs/ilvis0-regrouped-cover/case-unions.json')
    current=base.load(DATA/'case-unions.json');comparisons=[]
    for case in current['cases']:
        old=next((r for r in previous['cases'] if r['case_key']==case['case_key']),None)
        if old and 'union_width_m' in case:
            comparisons.append(dict(case_key=case['case_key'],complete=case['completed'],
                previous_width_m=old['union_width_m'],shared_width_m=case['union_width_m'],
                ratio_to_previous=np.array(case['union_width_m'])/np.array(old['union_width_m'])))
    comparison=dict(cases=comparisons,all_cases_complete=current['all_cases_complete'],
        tenfold_vs_original=len(current['cases'])==6 and current['all_cases_complete'] and
            all(c.get('tenfold_width_improvement',False) for c in current['cases']),scientific_decision='abstain')
    base.write(DATA/'case-comparison.json',comparison,replace=True);shutil.copyfile(DATA/'case-comparison.json',PUBLIC/'case-comparison.json')
    text=(PUBLIC/'README.md').read_text().replace('# Complete orientation-cover feasibility','# Shared-reference orientation-cover feasibility',1)
    text+='\nAll 27 physical and six common-error columns remain. One common block is used across training and future epochs; original inputs, physical bounds and acceptance limits are preserved.\n'
    text+='\n| Case | Ratio to regrouped widths N / E / height |\n|---|---:|\n'
    for row in comparisons:text+=f"| {row['case_key']} | "+', '.join(f'{v:.3f}' for v in row['ratio_to_previous'])+' |\n'
    (PUBLIC/'README.md').write_text(text)
    for name in ('README.md','PLAN.md','case-comparison.json'):receipt['artifacts'][name]=base.sha(PUBLIC/name)
    base.write(PUBLIC/'evidence-receipt.json',receipt,replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 shared-reference sectors.')
    elif args.run:verify(True);base.run();print('Shared-reference cover finished.')
    elif args.package_only:publish();print('Published saved shared-reference cover.')
    else:
        verify()
        for name,digest in base.load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if base.sha(PUBLIC/name)!=digest:raise ValueError('public shared artifact changed')
        print('Verified shared-cover freeze, results and side artifacts.')


if __name__=='__main__':main()
