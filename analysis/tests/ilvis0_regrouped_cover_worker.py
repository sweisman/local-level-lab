# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate generated orientation cover using qualified regrouped native bounds."""
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
from lll import ilvis0_sector_experiment as experiment

NAME='ilvis0-regrouped-cover-20261020';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-regrouped-cover'
TASKS=[dict(t,identity='regrouped-'+t['identity']) for t in predecessor.TASKS]
LIMITS=dict(predecessor.LIMITS,maximum_wall_s=900)
SOURCE_NAMES=predecessor.SOURCE_NAMES+['analysis/lll/ilvis0_sector_experiment.py','analysis/lll/ilvis0_regrouped_history.py',
    'analysis/lll/ilvis0_correlated_clock.py','analysis/tests/test_ilvis0_sector_experiment.py',
    'analysis/tests/ilvis0_regrouped_cover_worker.py','analysis/tests/test_ilvis0_regrouped_cover_worker.py',
    'docs/ilvis0-regrouped-cover/PLAN.md','docs/ilvis0-regrouped-controls/manifest.json',
    'docs/ilvis0-regrouped-controls/summary.json','docs/ilvis0-regrouped-controls/completion.json',
    'docs/ilvis0-orientation-cover/case-unions.json','docs/ilvis0-orientation-cover/summary.json']


def configure():
    predecessor.NAME=NAME;predecessor.DATA=DATA;predecessor.PUBLIC=PUBLIC;predecessor.TASKS=TASKS
    predecessor.LIMITS=LIMITS;predecessor.SOURCE_NAMES=SOURCE_NAMES
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    from lll import ilvis0_regrouped_history
    qualification=ROOT/'docs/ilvis0-regrouped-controls';old=ROOT/'docs/ilvis0-orientation-cover'
    for directory in (qualification,old):
        for name,digest in base.load(directory/'evidence-receipt.json')['artifacts'].items():
            if base.sha(directory/name)!=digest:raise ValueError('prerequisite publication artifact changed')
        if not base.load(directory/'summary.json')['passed']:raise ValueError('prerequisite failed')
    q=base.load(qualification/'manifest.json')
    for name in ('analysis/lll/ilvis0_regrouped_history.py','analysis/lll/ilvis0_correlated_clock.py'):
        if base.sha(ROOT/name)!=q['sources'][name]:raise ValueError('qualified regrouped component changed')
    if base.environment()!=q['environment']:raise ValueError('regrouped qualification environment mismatch')
    predecessor.prepare()
    manifest=verify();previous=base.load(old/'manifest.json')
    for task in TASKS:
        if task['packets']==400:
            key=predecessor.case_key(task)
            if manifest['inputs'][key]['sha256']!=previous['inputs'][key]['sha256']:
                raise ValueError('original orientation-cover input changed')


def verify(current=False):
    manifest=predecessor.verify(current)
    if (DATA/'completion.json').exists():
        for row in base.load(DATA/'summary.json')['results']:
            for name,digest in base.load(DATA/row['artifact']).get('extra_artifacts',{}).items():
                if base.sha(DATA/name)!=digest:raise ValueError('regrouped side artifact changed')
    return manifest


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_regrouped_history import enclose
    manifest=verify();case=base.load(DATA/manifest['inputs'][predecessor.case_key(task)]['path'])
    config=case['configuration'];config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    case=dict(case,configuration=config);theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt'])
    n=len(dt)
    if n!=task['packets'] or config['model']!=task['model'] or config['profile']!=task['profile']:
        raise ValueError('full generated candidate/input identity mismatch')
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.]);kernel,kernel_identity=load_tangent(directory)
    native_count=0;bound_count=0;maximum_difference=0.;extra={}
    def save(name,value):base.write(DATA/name,value);extra[name]=base.sha(DATA/name)
    def native(times,point):
        nonlocal native_count
        if native_count>=4:raise ValueError('per-sector native allowance exhausted')
        times=np.ascontiguousarray(times,dtype=float);out=np.empty((len(times),3));jac=np.empty((len(times)*3,27));warning=ctypes.c_int()
        charge(native_calls=1,packet_visits=n);native_count+=1
        code=kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native regrouped query outside supported record')
        save('native/'+task['identity']+f'-{native_count:02d}.json.gz',dict(times=times,point=point,prediction=out,
            jacobian=jac,warning=warning.value))
        return out,jac.reshape(len(times),3,27)
    def bound(time,lo,hi,center,position):
        nonlocal bound_count,maximum_difference
        if bound_count>=8:raise ValueError('per-sector bound allowance exhausted')
        bound_count+=1;suffix=task['identity']+f'-{bound_count:02d}'
        base.write(DATA/'bound-reservations'/(suffix+'.json'),dict(identity=suffix,time_s=float(time),maximum_packet_steps=n))
        report=enclose(config,theta,dv,dt,time=float(time),lower=lo,upper=hi,center=center)
        error=float(np.max(abs((report['center']-position)*scale)));maximum_difference=max(maximum_difference,error)
        base.write(DATA/'bounds'/(suffix+'.json.gz'),dict(report,native_center_difference_m=error))
        return report['remainder']*scale
    def emit(label,value):
        if label not in ('training','future'):raise ValueError('unexpected evidence identity')
        save('evidence/'+task['identity']+'-'+label+'.json.gz',value)
    result=experiment.evaluate(task,case,native=native,bound=bound,emit=emit)
    return dict(result,passed=result['passed'] and maximum_difference<=1e-6,kernel=kernel_identity,
        maximum_center_difference_m=maximum_difference,bound_evaluations=bound_count,native_evaluations=native_count,
        reserved_bound_steps=bound_count*n,extra_artifacts=extra)


def publish():
    import numpy as np
    verify();predecessor.publish();manifest=verify();summary=base.load(DATA/'summary.json')
    receipt=base.load(PUBLIC/'evidence-receipt.json')
    for row in summary['results']:
        for name in base.load(DATA/row['artifact']).get('extra_artifacts',{}):
            target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
            receipt['artifacts'][name]=base.sha(target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-regrouped-cover/PLAN.md',PUBLIC/'PLAN.md')
    previous=base.load(DATA/'source-freeze/docs/ilvis0-orientation-cover/case-unions.json')
    current=base.load(DATA/'case-unions.json');comparisons=[]
    for case in current['cases']:
        old=next((r for r in previous['cases'] if r['case_key']==case['case_key']),None)
        if old and 'union_width_m' in case:
            comparisons.append(dict(case_key=case['case_key'],complete=case['completed'],
                previous_orientation_width_m=old['union_width_m'],regrouped_width_m=case['union_width_m'],
                ratio_to_previous=np.array(case['union_width_m'])/np.array(old['union_width_m'])))
    comparison=dict(cases=comparisons,all_cases_complete=current['all_cases_complete'],
        tenfold_vs_original=len(current['cases'])==6 and current['all_cases_complete'] and
            all(c.get('tenfold_width_improvement',False) for c in current['cases']),scientific_decision='abstain')
    base.write(DATA/'case-comparison.json',comparison,replace=True);shutil.copyfile(DATA/'case-comparison.json',PUBLIC/'case-comparison.json')
    text=(PUBLIC/'README.md').read_text().replace('# Complete orientation-cover feasibility','# Regrouped orientation-cover feasibility',1)
    text+='\n| Case | Ratio to previous orientation-cover widths N / E / height |\n|---|---:|\n'
    for row in comparisons:text+=f"| {row['case_key']} | "+', '.join(f'{v:.3f}' for v in row['ratio_to_previous'])+' |\n'
    text+='\nAll original sectors, inputs and physical bounds are retained. Native outputs, full Jacobians and training/future support inputs are saved for diagnosis without new evaluations.\n'
    (PUBLIC/'README.md').write_text(text)
    for name in ('PLAN.md','README.md','case-comparison.json'):receipt['artifacts'][name]=base.sha(PUBLIC/name)
    base.write(PUBLIC/'evidence-receipt.json',receipt,replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 separately identified regrouped sectors.')
    elif args.run:verify(True);base.run();print('Regrouped orientation comparison finished.')
    elif args.package_only:publish();print('Published saved regrouped sectors without evaluations.')
    else:
        verify()
        for name,digest in base.load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if base.sha(PUBLIC/name)!=digest:raise ValueError('public regrouped artifact changed')
        print('Verified regrouped sector freeze, results and all side artifacts.')


if __name__=='__main__':main()
