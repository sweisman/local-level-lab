# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated duration-growth screen; no training fits or original data."""
import argparse
import ctypes
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
import ilvis0_shared_cover_worker as prerequisite
import ilvis0_native_training_worker as generator
base=prerequisite.base
from lll import ilvis0_shared_native as shared

NAME='ilvis0-shared-duration-growth-20261020';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-shared-duration-growth'
TASKS=[dict(identity=f'growth-{m}-{int(p)}-{s}',kind='duration-growth',model=m,profile=p,sector=s,
    prefixes=[400,800,1600],times_s=[1.8,3.6,7.2]) for m in range(3) for p in (False,True) for s in range(8)]
LIMITS=dict(base.LIMITS,maximum_identities=48,maximum_native_evaluations=576,maximum_packet_visits=537600,
    maximum_bound_evaluations=144,maximum_bound_steps=134400,maximum_wall_s=900)
SOURCE_NAMES=prerequisite.SOURCE_NAMES+['analysis/tests/ilvis0_shared_duration_worker.py',
    'analysis/tests/test_ilvis0_shared_duration_worker.py','docs/ilvis0-shared-duration-growth/PLAN.md']
SOURCE_NAMES+=['docs/ilvis0-shared-cover/'+n for n in ('manifest.json','summary.json','completion.json','case-comparison.json')]


def key(task):return f"case-{task['model']}-{int(task['profile'])}"


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    import numpy as np
    if DATA.exists():raise ValueError('duration freeze exists; never overwrite')
    old=ROOT/'docs/ilvis0-shared-cover';previous=base.load(old/'manifest.json')
    for name,digest in base.load(old/'evidence-receipt.json')['artifacts'].items():
        if base.sha(old/name)!=digest:raise ValueError('short comparison artifact changed')
    if (not base.load(old/'summary.json')['passed'] or not base.load(old/'case-comparison.json')['tenfold_vs_original']
            or base.environment()!=previous['environment']):raise ValueError('short comparison gate or environment mismatch')
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/') and base.sha(ROOT/name)!=digest:raise ValueError('qualified component changed')
    inputs={}
    for task in TASKS:
        name=key(task)
        if name in inputs:continue
        n=max(task['prefixes']);case=generator.case_inputs(dict(task,packets=n));path='inputs/'+name+'.json.gz'
        if n>=400:
            prior=base.load(old/previous['inputs'][name+'-400']['path'])
            for field in ('theta','dv','dt'):
                if not np.array_equal(np.asarray(case[field])[:400],prior[field]):raise ValueError('original input prefix changed')
            if any(not np.array_equal(case['configuration'][f],prior['configuration'][f]) for f in case['configuration']):
                raise ValueError('original physical configuration changed')
            if not np.array_equal(case['truth'],prior['truth']):raise ValueError('original truth changed')
        base.write(DATA/path,case);inputs[name]=dict(path=path,sha256=base.sha(DATA/path))
    paths=set(SOURCE_NAMES)
    paths.update(str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT))
    for name in paths:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    base.write(DATA/'manifest.json',dict(version=NAME,tasks=TASKS,limits=LIMITS,inputs=inputs,
        environment=base.environment(),numerical_environment=environment(threads=4),sources={n:base.sha(ROOT/n) for n in sorted(paths)},
        compilers={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('cc','c++')}))
    base.write(DATA/'authorization.json',dict(scope='standing V01 generated duration diagnosis; no observed fits',
        limits=LIMITS,manifest_sha256=base.sha(DATA/'manifest.json')))


def verify(current=False):
    manifest=base.verify(current=current)
    for record in manifest['inputs'].values():
        if base.sha(DATA/record['path'])!=record['sha256']:raise ValueError('generated duration input changed')
    return manifest


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_orientation_cover import sector
    manifest=verify();case=base.load(DATA/manifest['inputs'][key(task)]['path']);config=case['configuration']
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    box=sector(task['sector']);lo=box['lower'];hi=box['upper'];center=box['center']
    if len(task['prefixes'])!=len(task['times_s']) or len(task['prefixes'])>3:raise ValueError('frozen prefix/query count mismatch')
    kernel,kernel_id=load_tangent(directory);scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.])
    rows=[];calls=0;steps=0;passed=True
    for number,(n,time) in enumerate(zip(task['prefixes'],task['times_s']),1):
        if type(n) is not int or not 1<=n<=1600:raise ValueError('unsupported prefix allocation')
        theta=np.ascontiguousarray(case['theta'][:n]);dv=np.ascontiguousarray(case['dv'][:n]);dt=np.ascontiguousarray(case['dt'][:n])
        if len(dt)!=n:raise ValueError('incomplete generated prefix')
        reference=shared.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
        native_rows=[]
        def native(point):
            nonlocal calls
            if len(native_rows)>=4 or calls>=12:raise ValueError('per-prefix native allowance exhausted')
            charge(native_calls=1,packet_visits=n);calls+=1
            out=np.empty((1,3));jac=np.empty((3,27));warning=ctypes.c_int()
            code=kernel(n,theta,dv,dt,1,np.array([time]),config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
                np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
            if code:raise ValueError('generated duration query outside native support')
            native_rows.append(dict(point=point,prediction=out[0],jacobian=jac,warning=warning.value))
            return out[0],jac
        nominal,jac=native(center)
        suffix=task['identity']+f'-{number:02d}'
        base.write(DATA/'bound-reservations'/(suffix+'.json'),dict(identity=suffix,time_s=time,maximum_packet_steps=n))
        report=shared.enclose(config,theta,dv,dt,time=time,lower=lo,upper=hi,reference=reference)
        steps+=n;center_error=float(np.max(abs((report.center-nominal)*scale)));probes=[]
        for point in (lo,hi,center+.7*(hi-center)):
            value,_=native(point);gamma=reference.normalized_values_at(point)
            error=abs((value-nominal-jac@(point-center)-report.coefficients.matrix@gamma)*scale)
            contained=bool(np.all(error<=report.unshared_remainder*scale+1e-5) and np.all(abs(gamma)<=1+1e-12))
            probes.append(dict(point=point,shared_error=gamma,factored_error_m=error,contained=contained))
            passed=passed and contained
        passed=passed and center_error<=1e-6
        rows.append(dict(packets=n,time_s=time,source_id=reference.source_id,reference=reference.report(),bound=report.report(),
            native=native_rows,probes=probes,maximum_center_error_m=center_error,
            unshared_width_contribution_m=2*report.unshared_remainder*scale,
            position_remainder_m=np.array(report.metadata['position_unshared_remainder'])*scale,
            lever_remainder_m=np.array(report.metadata['lever_unshared_remainder'])*scale))
    return dict(identity=task['identity'],kind=task['kind'],passed=bool(passed),task=task,prefixes=rows,kernel=kernel_id,
        native_evaluations=calls,bound_evaluations=len(rows),reserved_bound_steps=steps,
        physical_parameter_count=27,enclosure_parameter_count=33,original_reads=0,optimizer_starts=0,
        floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def publish():
    import numpy as np
    manifest=verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    names += [r['path'] for r in manifest['inputs'].values()]
    charged=manifest['tasks'][:summary['charged']['identities']]
    names += ['starts/'+t['identity']+'.json' for t in charged]
    names += [f'charges/call-{i:05d}.json' for i in range(1,summary['charged']['native_calls']+1)]
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    for row in rows:
        names += ['bound-reservations/'+row['identity']+f'-{i:02d}.json' for i in range(1,len(row.get('prefixes',[]))+1)]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-shared-duration-growth/PLAN.md',PUBLIC/'PLAN.md')
    lines=['# Shared-reference duration growth','',f"{sum(r['passed'] for r in rows)}/{len(manifest['tasks'])} identities pass; state: {summary['state']}.",'',
        'All original sectors and physical bounds remain. These are the unshared allowance contributions, '
        'not complete prediction widths, measured sensor errors or calibrated intervals.','',
        '| Time | Complete prefix controls | Maximum unshared width contribution N / E / height (m) |',
        '|---|---:|---:|']
    times=sorted({p['time_s'] for row in rows for p in row.get('prefixes',[])})
    for time in times:
        selected=[p for row in rows for p in row.get('prefixes',[]) if p['time_s']==time]
        maximum=np.max([p['unshared_width_contribution_m'] for p in selected],axis=0)
        lines.append(f"| {time:g} s | {len(selected)} | "+', '.join(f'{v:.3f}' for v in maximum)+' |')
    lines+=['',f"Charged {summary['charged']['native_calls']} native calls in {summary['elapsed_s']:.2f} seconds. "
        'No training-feasible region, observed fit or protected ESA outcome is computed. '
        'Passing probe checks is not a long-record usefulness or coverage claim.','',
        '[Frozen scope](PLAN.md) · [Short comparison](../ilvis0-shared-cover/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 duration-growth identities.')
    elif args.run:verify(True);base.run();print('Duration-growth screen finished.')
    elif args.package_only:publish();print('Published saved duration growth.')
    else:
        verify()
        for name,digest in base.load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if base.sha(PUBLIC/name)!=digest:raise ValueError('public duration artifact changed')
        print('Verified duration-growth freeze/results.')


if __name__=='__main__':main()
