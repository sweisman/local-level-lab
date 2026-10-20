# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated recording-scale bound-growth feasibility study."""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
import ilvis0_history_worker as history
from ilvis0_channel_envelope_worker import sha,load,write,environment

NAME='ilvis0-recording-scale-bounds-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-recording-scale-bounds'
CHECKPOINTS=(100,1000,10000,48000);SEED=2026101925
TASKS=[dict(identity=f'{model}-{box}',model=model,box=box,maximum_bound_steps=48000,
    maximum_c_calls=16,maximum_tangent_calls=4) for model in history.base.MODELS for box in ('broad','narrow')]
LIMITS=dict(maximum_identities=6,maximum_bound_steps=288000,maximum_c_calls=96,maximum_tangent_calls=24,
    maximum_probes=96,maximum_wall_s=900,numerical_threads=4,original_reads=0,archive_native_evaluations=0,
    optimizer_starts=0,retries=0,deadline_policy='cooperative-no-signals')


def case_inputs(task):
    import numpy as np
    template=next(t for t in history.TASKS if t['model']==task['model'] and t['packets']==3 and t['profile'] and t['timing']=='interior')
    case=history.case_inputs(template);n=48000;t=np.arange(n)*.005
    case['durations']=np.full(n,.005);case['starts']=np.r_[0.,np.cumsum(case['durations'])[:-1]]
    case['raw_theta']=.005*np.column_stack((2e-5+3e-4*np.sin(.03*t),-3e-5+2e-4*np.cos(.02*t),
        1e-5+5e-4*np.sin(.01*t)))
    case['raw_dv']=.005*np.column_stack((.02*np.sin(.05*t),.02*np.cos(.04*t),-9.81+.01*np.sin(.03*t)))
    case['packets']=n;case['center']=np.zeros(27);case['limits'][25]=0.;case['base_time']=float(np.cumsum(case['durations'])[-1])
    case['case_index']=TASKS.index(task);case['profile']=True
    if task['box']=='narrow':
        case['limits'][:3]=np.deg2rad([1.,1.,1.]);case['limits'][3:6]=[1.,1.,.5];case['limits'][6:9]=10.
        case['limits'][9:12]=np.deg2rad(.1)/3600.;case['limits'][12:15]=.05
        case['limits'][15:18]=.001;case['limits'][18:21]=.01;case['limits'][21:24]=.2;case['limits'][24]=.01
    return case


def initial_bounds(case):
    import numpy as np
    from scipy.linalg import expm
    from lll import ilvis0_geographic_bounds as geo
    from lll.ilvis0_local_step_bounds import Value,Matrix
    limits=case['limits'];p=limits*case['center'];delta=limits*np.maximum(abs(-1.-case['center']),abs(1.-case['center']))
    vector=lambda s:Value(p[s],float(np.linalg.norm(delta[s])),0.)
    seed=geo.Coordinates(*(geo.Scalar.fixed(v) for v in case['seed_coordinates']))
    displacement=geo.coordinate_map(seed,vector(slice(6,9)),model=case['model'],disc_radius_m=case['radius'])
    position=geo.Coordinates(*(geo.plus(a,b) for a,b in zip((seed.latitude,seed.longitude,seed.height),displacement)))
    rotation=case['seed_rotation']@expm(history.base._skew(p[:3]));dr=float(np.linalg.norm(delta[:3]))
    state=geo.State(position,Value(case['seed_velocity']+p[3:6],float(np.linalg.norm(delta[3:6])),0.),Matrix(rotation,min(2.,dr),.5*dr*dr,'rotation'))
    removal=geo.Scalar.interval((p[26]+1.)/2.,0.,1.);gravity=geo.Scalar.interval(9.81+p[24],9.81-limits[24],9.81+limits[24])
    return state,removal,gravity,vector(slice(21,24))


def evaluate(task,kernel,*,checkpoints=CHECKPOINTS,case=None,output=None,deadline=None):
    import numpy as np
    from lll import ilvis0_geographic_bounds as geo
    from lll.ilvis0_increment_remainders import calibrated_box
    from lll.ilvis0_local_step_bounds import Value
    if (not checkpoints or any(type(x) is not int or x<=0 for x in checkpoints)
            or tuple(sorted(set(checkpoints)))!=tuple(checkpoints) or checkpoints[-1]>task['maximum_bound_steps']):
        raise ValueError('ordered unique finite checkpoints required')
    case=case_inputs(task) if case is None else case
    book=history.base.Calls(task['maximum_c_calls'],task['maximum_tangent_calls'],1,deadline)
    rows=[];steps=0;attempted=0;unsupported=None;checks_passed=True;context=dict(identity=task['identity'],checkpoints=rows)
    limits=case['limits'];p=limits*case['center'];metre=case['metre_scale']
    def corrected(raw,dt,bias,gain):
        value=calibrated_box(raw,dt,bias_center=p[bias],gain_center=p[gain],bias_lower=-limits[bias],bias_upper=limits[bias],
            gain_lower=-limits[gain],gain_upper=limits[gain])
        return Value(value['center'],value['change_radius'],value['remainder_radius'])
    try:
        try:state,removal,gravity,lever=initial_bounds(case)
        except (ValueError,OverflowError,FloatingPointError) as error:unsupported=dict(packet=0,reason=str(error))
        if unsupported is None:
            with np.errstate(over='raise',invalid='raise',divide='raise'):
                for index in range(checkpoints[-1]):
                    if deadline is not None:history.base.check_time(deadline)
                    attempted+=1;duration=case['durations'][index]
                    try:
                        theta=corrected(case['raw_theta'][index],duration,slice(9,12),slice(15,18))
                        dv=corrected(case['raw_dv'][index],duration,slice(12,15),slice(18,21))
                        state=geo.step(state,theta,dv,period=geo.Scalar.fixed(duration),removal=removal,gravity=gravity,
                            model=case['model'],disc_radius_m=case['radius'])
                    except (ValueError,OverflowError,FloatingPointError) as error:
                        unsupported=dict(packet=index+1,reason=str(error));break
                    steps+=1
                    if steps not in checkpoints:continue
                    try:observation=geo.observation(state,lever,model=case['model'],disc_radius_m=case['radius'])
                    except (ValueError,OverflowError,FloatingPointError) as error:
                        unsupported=dict(packet=steps,reason='antenna domain: '+str(error));break
                    current=dict(case,base_time=float(case['starts'][index]+duration))
                    cpp,jac,warning=kernel.tangent(current,case['center'],book)
                    nominal=observation.center;nominal_error=float(np.max(abs((nominal-cpp)*metre)))
                    remainder=np.array([v.value.remainder for v in (observation.latitude,observation.longitude,observation.height)])*metre
                    change=np.array([v.value.change for v in (observation.latitude,observation.longitude,observation.height)])*metre
                    okay=nominal_error<=.001;probes=[]
                    for probe in range(4):
                        rng=np.random.default_rng(np.random.SeedSequence([SEED,case['case_index'],steps]))
                        point=case['center'].copy() if probe==0 else np.full(27,-1.) if probe==1 else np.ones(27) if probe==2 else rng.uniform(-1.,1.,27)
                        actual=kernel.value(current,point,book);linear=(jac@(point-case['center']))*metre
                        error=abs((actual-cpp)*metre-linear);actual_change=abs((actual-nominal)*metre)
                        tolerance=.001+2e-12*abs(linear)
                        passed=bool(np.all(error<=remainder+tolerance) and np.all(actual_change<=change+tolerance))
                        okay=okay and passed;probes.append(dict(parameters=point,error_m=error,change_m=actual_change,passed=passed))
                    rows.append(dict(packets=steps,elapsed_s=current['base_time'],center_discrepancy_m=nominal_error,
                        change_m=change,remainder_m=remainder,native_boundary_warning=warning,checks_passed=okay,probes=probes,
                        bounded_state=state.report(),bounded_observation=observation.report()))
                    checks_passed=checks_passed and okay
        return dict(passed=checks_passed,checks_passed=checks_passed,support_status='unsupported' if unsupported else 'supported',
            unsupported=unsupported,executed_bound_steps=steps,attempted_bound_steps=attempted,supported_through_s=float(sum(case['durations'][:steps])),
            checkpoints=rows,calls={key:book.counts[key] for key in ('c','tangent')},native_rounding_certificate=False,
            numerical_allowance_status='declared_1mm_empirical_comparison_not_global_proof',observational_coverage_qualified=False,
            original_reads=0,optimizer_starts=0,scientific_decision='abstain')
    finally:
        context.update(calls=book.counts,attempted_bound_steps=attempted)
        if output is not None:write(output,context)


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import ilvis0_geographic_bounds,ilvis0_increment_remainders
    sources={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    sources.update('analysis/tests/'+n for n in ('ilvis0_recording_bound_worker.py','test_ilvis0_recording_bound_worker.py',
        'ilvis0_history_worker.py','ilvis0_geographic_worker.py','ilvis0_geographic_bound_harness.c','ilvis0_channel_envelope_worker.py','run_numerical.py'))
    sources.update(['analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','docs/ilvis0-recording-scale-bounds/PLAN.md'])
    hashes={name:sha(ROOT/name) for name in sorted(sources)}
    for name in hashes:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    inputs={}
    for task in TASKS:
        name='inputs/'+task['identity']+'.json.gz';write(DATA/name,case_inputs(task));inputs[task['identity']]=dict(path=name,sha256=sha(DATA/name))
    build=history.base.compile_kernels(DATA)
    write(DATA/'manifest.json',dict(version='recording-scale-bounds-v1',sources=hashes,inputs=inputs,environment=environment(),build=build,
        limits=LIMITS,tasks=TASKS,checkpoints=CHECKPOINTS,seed=SEED,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS));return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['tasks']!=TASKS:raise ValueError('recording-scale scope/environment changed')
    if manifest['build']['compilers']!=history.base.compilers():raise ValueError('recording-scale compiler changed')
    for name,digest in manifest['build']['binaries'].items():
        if sha(DATA/name)!=digest:raise ValueError('recording-scale binary changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('recording-scale authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('recording-scale source changed: '+name)
    for item in manifest['inputs'].values():
        if sha(DATA/item['path'])!=item['sha256']:raise ValueError('generated recording input changed')
    return manifest


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged recording-scale study cannot restart')
        manifest=verify();kernel=history.Kernel(DATA);started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s'];rows=[];terminal=None
        charged=dict(bound_steps=0,c_calls=0,tangent_calls=0)
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        try:
            for task in TASKS:
                history.base.check_time(deadline);identity=task['identity']
                write(DATA/'charges'/(identity+'.json'),dict(task,manifest_sha256=sha(DATA/'manifest.json')))
                for key in charged:charged[key]+=task['maximum_'+key]
                write(DATA/'status.json',dict(state='running',identity=identity,total=6,numerical_threads=4,pid=os.getpid()),replace=True)
                generated='generated/'+identity+'.json.gz'
                try:result=evaluate(task,kernel,output=DATA/generated,deadline=deadline)
                except history.base.AllowanceExhausted as error:result=dict(passed=False,error=str(error));terminal=str(error)
                except Exception as error:result=dict(passed=False,error=type(error).__name__+': '+str(error))
                if not (DATA/generated).exists():write(DATA/generated,dict(task=task,error=result.get('error','missing evidence')))
                artifact='results/'+identity+'.json';write(DATA/artifact,dict(task,**result,generated_artifact=generated,generated_sha256=sha(DATA/generated)))
                rows.append(dict(task,passed=result['passed'],artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)),replace=True)
                if terminal:break
        except history.base.AllowanceExhausted as error:terminal=str(error)
        state='terminal' if terminal else 'complete';elapsed=time.time()-started
        write(DATA/'summary.json',dict(state=state,passed=len(rows)==6 and all(r['passed'] for r in rows) and not terminal,results=rows,
            elapsed_s=elapsed,terminal_reason=terminal,charged=charged,optimizer_starts=0,native_evaluations=0,
            archive_native_evaluations=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=6,numerical_threads=0),replace=True)
    publish()


def publish():
    manifest=load(DATA/'manifest.json');summary=load(DATA/'summary.json');completion=load(DATA/'completion.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('recording completion changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('recording result changed')
        result=load(DATA/row['artifact']);results.append(result)
        if sha(DATA/result['generated_artifact'])!=result['generated_sha256']:raise ValueError('recording generated evidence changed')
        names.extend([row['artifact'],result['generated_artifact'],'charges/'+row['identity']+'.json'])
    for item in manifest['inputs'].values():
        if sha(DATA/item['path'])!=item['sha256']:raise ValueError('recording input changed')
        names.append(item['path'])
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Recording-scale global-bound growth','',f"Completed {len(results)}/6 generated histories in {summary['elapsed_s']:.2f} seconds. "
        'No archive measurements or fitted outcomes were used.','',
        '| Candidate | Box | Supported through | Full history supported | Last largest remainder | Numerical checks |',
        '|---|---|---:|---|---:|---|']
    for row in results:
        points=row.get('checkpoints',[]);last=max(points[-1]['remainder_m']) if points else None
        lines.append(f"| {row['model']} | {row['box']} | {row.get('supported_through_s',0.):.3f} s | {row.get('support_status','error')} | "
            f"{last if last is not None else 'unavailable'} m | {row.get('checks_passed',False)} |")
    lines+=['','Supported means the declared mathematical outer region stayed inside its coordinate domain. '
        'It does not establish useful prediction width. Numerical comparisons use a declared 1 mm allowance; '
        'they are not a formal global rounding certificate or observational coverage calibration.',
        '', '[Frozen scope and criteria](PLAN.md) · [Short-history evidence](../ilvis0-history-bounds/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names+=['README.md','PLAN.md']+['source-freeze/'+n for n in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen six generated four-minute histories; no execution.')
    elif args.run:run();print('Finite recording-scale feasibility study finished; inspect saved outcomes.')
    else:publish();print('Published saved recording-scale results; no integration calls.')


if __name__=='__main__':main()
