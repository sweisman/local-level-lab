# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated full-history bounds and packet-boundary qualification."""
import argparse
import ctypes
import fcntl
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
import ilvis0_geographic_worker as base
from ilvis0_channel_envelope_worker import sha,load,write,environment

NAME='ilvis0-history-bounds-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-history-bounds'
SEED=2026101924
TASKS=[dict(identity=f'{model}-{packets}-{profile}-{timing}',model=model,packets=packets,profile=profile,
    timing=timing,probes=16,maximum_c_calls=17,maximum_tangent_calls=1,maximum_reference_calls=44)
    for model in base.MODELS for packets in (3,9,33) for profile in (False,True)
    for timing in ('interior','boundary','multiple')]
LIMITS=dict(maximum_identities=54,maximum_probes=864,maximum_c_calls=918,maximum_tangent_calls=54,
    maximum_reference_calls=2376,maximum_wall_s=300,numerical_threads=4,original_reads=0,
    archive_native_evaluations=0,optimizer_starts=0,retries=0,deadline_policy='cooperative-no-signals')


def case_inputs(task):
    import numpy as np
    setup=dict(model=task['model'],hemisphere='south' if task['profile'] else 'north',
        removal_center='upper' if task['profile'] else 'fixed',width='broad',timing='fixed')
    setup=next(t for t in base.TASKS if all(t[k]==v for k,v in setup.items()))
    case=base.case_inputs(setup);n=task['packets'];k=np.arange(n)
    dt=.005+.00015*np.sin(.4*k);starts=np.r_[0.,np.cumsum(dt)[:-1]]
    case['durations']=dt;case['starts']=starts
    case['raw_theta']=np.column_stack((3e-5+1e-5*np.sin(k),-2e-5+7e-6*np.cos(.3*k),1e-5+1e-5*np.sin(.2*k)))
    case['raw_dv']=np.column_stack((dt*(.03+.01*np.sin(k)),dt*(.04+.01*np.cos(k)),-9.81*dt))
    middle=n//2
    case['base_time']=float(starts[middle]+(.5*dt[middle] if task['timing']!='boundary' else 0.))
    case['limits'][25]=float(min(dt)*dict(interior=.1,boundary=.2,multiple=1.3)[task['timing']])
    case['center'][25]=0.
    case['profile']=task['profile'];case['case_index']=TASKS.index(next(t for t in TASKS if t['identity']==task['identity']))
    case['packets']=n
    return case


def initial_values(case,point):
    import numpy as np
    from scipy.linalg import expm
    p=case['limits']*np.asarray(point)
    c=case['seed_coordinates']+base._rates(case['model'],case['seed_coordinates'],p[6:9],case['radius'])
    v=case['seed_velocity']+p[3:6];r=case['seed_rotation']@expm(base._skew(p[:3]))
    theta=(case['raw_theta']-case['durations'][:,None]*p[9:12])/(1.+p[15:18])
    dv=(case['raw_dv']-case['durations'][:,None]*p[12:15])/(1.+p[18:21])
    return p,c,v,r,theta,dv


def _reference_step(model,c,v,r,theta,dv,period,gravity,radius,removal):
    import numpy as np
    from scipy.linalg import expm
    def context(phi,rates):
        standard=7.2921150e-5*np.array([np.cos(phi),0.,-np.sin(phi)])
        earth=standard if model=='sphere_rotating' else np.zeros(3)
        transport=np.array([0.,0.,-rates[1]]) if model=='flat_still' else np.array([np.cos(phi)*rates[1],-rates[0],-np.sin(phi)*rates[1]])
        return earth,transport,earth+transport-removal*standard
    def local(phi,rates):
        earth,transport,win=context(phi,rates)
        a=(2.*earth+transport)*period/2.;s=base._skew(a)
        middle=expm(base._skew(-win*period/2.))@r@expm(base._skew(theta/2.))
        next_r=expm(base._skew(-win*period))@r@expm(base._skew(theta))
        rhs=(np.eye(3)-s)@v+middle@dv+np.array([0.,0.,gravity*period])
        return next_r,np.linalg.solve(np.eye(3)+s,rhs)
    rates=base._rates(model,c,v,radius);midpoint=c+rates*period/2.
    _,estimate=local(midpoint[0],rates)
    revised=base._rates(model,midpoint,(v+estimate)/2.,radius)
    next_r,next_v=local(midpoint[0],revised)
    return c+revised*period,next_v,next_r


def reference(case,point,book=None):
    if book:book.tick('reference')
    p,c,v,r,theta,dv=initial_values(case,point);t=case['base_time']+p[25];clock=0.
    removal=(p[26]+1.)/2. if case['profile'] else 0.;gravity=9.81+p[24]
    for index,duration in enumerate(case['durations']):
        end=clock+duration;last=t.real<=end
        fraction=(t-clock)/duration if last else 1.
        c,v,r=_reference_step(case['model'],c,v,r,theta[index]*fraction,dv[index]*fraction,
            duration*fraction,gravity,case['radius'],removal)
        if last:break
        clock=end
    else:raise ValueError('reference observation exceeds packet support')
    output=c+base._rates(case['model'],c,r@p[21:24],case['radius'])
    return dict(coordinates=c,velocity=v,attitude=r,observation=output)


class Kernel(base.Kernel):
    def __init__(self,directory):
        super().__init__(directory)
        pointer=ctypes.POINTER(ctypes.c_double);size=ctypes.c_size_t;integer=ctypes.c_int;scalar=ctypes.c_double
        self.predict=self.c_library.ilvis0_predict
        self.predict.argtypes=[size,pointer,pointer,pointer,size,pointer,pointer,pointer,pointer,pointer,
            integer,scalar,scalar,scalar,pointer];self.predict.restype=integer

    def value(self,case,point,book=None):
        import numpy as np
        p,c,v,r,theta,dv=initial_values(case,point)
        arrays=[np.ascontiguousarray(x,dtype=np.float64) for x in (theta,dv,case['durations'],[case['base_time']+p[25]],c,v,r,p[21:24])]
        output=np.empty(3);ptr=ctypes.POINTER(ctypes.c_double);q=lambda x:x.ctypes.data_as(ptr)
        if book:book.tick('c')
        code=self.predict(case['packets'],q(arrays[0]),q(arrays[1]),q(arrays[2]),1,q(arrays[3]),q(arrays[4]),q(arrays[5]),q(arrays[6]),
            q(arrays[7]),base.MODELS.index(case['model']),9.81+p[24],case['radius'],(p[26]+1.)/2. if case['profile'] else 0.,q(output))
        if code or not np.all(np.isfinite(output)):raise ValueError('full native prediction failed: '+str(code))
        return output

    def tangent(self,case,point,book=None):
        import numpy as np
        arrays=[np.ascontiguousarray(x,dtype=np.float64) for x in (case['raw_theta'],case['raw_dv'],case['durations'],[case['base_time']],
            case['seed_coordinates'],case['seed_velocity'],case['seed_rotation'],case['limits'],point)]
        output=np.empty(3);jac=np.empty((3,27));warning=ctypes.c_int();ptr=ctypes.POINTER(ctypes.c_double);q=lambda x:x.ctypes.data_as(ptr)
        if book:book.tick('tangent')
        code=self.cpp(case['packets'],q(arrays[0]),q(arrays[1]),q(arrays[2]),1,q(arrays[3]),q(arrays[4]),q(arrays[5]),q(arrays[6]),
            q(arrays[7]),q(arrays[8]),base.MODELS.index(case['model']),int(case['profile']),9.81,case['radius'],q(output),q(jac),ctypes.byref(warning))
        if code or not np.all(np.isfinite(output)) or not np.all(np.isfinite(jac)):raise ValueError('full tangent failed: '+str(code))
        return output,jac,warning.value


def enclosure(case):
    import numpy as np
    from scipy.linalg import expm
    from lll import ilvis0_geographic_bounds as geo,ilvis0_history_bounds as history
    from lll.ilvis0_local_step_bounds import Value,Matrix
    from lll.ilvis0_increment_remainders import calibrated_box
    limits=case['limits'];p=limits*case['center'];delta=limits*np.maximum(abs(-1.-case['center']),abs(1.-case['center']))
    vector=lambda s:Value(p[s],float(np.linalg.norm(delta[s])),0.)
    seed=geo.Coordinates(*(geo.Scalar.fixed(v) for v in case['seed_coordinates']))
    displacement=geo.coordinate_map(seed,vector(slice(6,9)),model=case['model'],disc_radius_m=case['radius'])
    position=geo.Coordinates(*(geo.plus(x,y) for x,y in zip((seed.latitude,seed.longitude,seed.height),displacement)))
    dr=float(np.linalg.norm(delta[:3]));rotation=case['seed_rotation']@expm(base._skew(p[:3]))
    state=geo.State(position,Value(case['seed_velocity']+p[3:6],float(np.linalg.norm(delta[3:6])),0.),Matrix(rotation,min(2.,dr),.5*dr*dr,'rotation'))
    def corrected(raw,dt,bias,gain):
        result=calibrated_box(raw,dt,bias_center=p[bias],gain_center=p[gain],bias_lower=-limits[bias],bias_upper=limits[bias],
            gain_lower=-limits[gain],gain_upper=limits[gain])
        return Value(result['center'],result['change_radius'],result['remainder_radius'])
    theta=[corrected(raw,dt,slice(9,12),slice(15,18)) for raw,dt in zip(case['raw_theta'],case['durations'])]
    dv=[corrected(raw,dt,slice(12,15),slice(18,21)) for raw,dt in zip(case['raw_dv'],case['durations'])]
    time_bound=geo.Scalar.interval(case['base_time']+p[25],case['base_time']-limits[25],case['base_time']+limits[25])
    removal=geo.Scalar.interval((p[26]+1.)/2.,0.,1.) if case['profile'] else geo.Scalar.fixed(0.)
    result=history.history(initial=state,theta=theta,dv=dv,durations=case['durations'],starts=case['starts'],time=time_bound,
        removal=removal,gravity=geo.Scalar.interval(9.81+p[24],9.81-limits[24],9.81+limits[24]),lever=vector(slice(21,24)),
        model=case['model'],disc_radius_m=case['radius'])
    state=result.state;antenna=result.observation
    components=lambda c:(c.latitude,c.longitude,c.height)
    return dict(values=dict(coordinates=state.position.center,velocity=state.velocity.center,attitude=state.attitude.center,observation=antenna.center),
        changes=dict(coordinates=np.array([v.value.change for v in components(state.position)]),velocity=state.velocity.change,
            attitude=state.attitude.change,observation=np.array([v.value.change for v in components(antenna)])),
        remainders=dict(coordinates=np.array([v.value.remainder for v in components(state.position)]),velocity=state.velocity.remainder,
            attitude=state.attitude.remainder,observation=np.array([v.value.remainder for v in components(antenna)])),report=result.report())


def evaluate(task,kernel,output=None,deadline=None):
    import numpy as np
    book=base.Calls(task['maximum_c_calls'],task['maximum_tangent_calls'],task['maximum_reference_calls'],deadline)
    case=case_inputs(task);context=dict(task=task,inputs=case,records=[]);keys=('coordinates','velocity','attitude','observation')
    try:
        bound=enclosure(case);context['analytic_bound']=bound;nominal=reference(case,case['center'],book)
        native=kernel.value(case,case['center'],book);cpp,jac,warning=kernel.tangent(case,case['center'],book)
        columns={key:[] for key in keys}
        for j in range(27):
            actual=reference(case,case['center']+1e-25j*np.eye(27)[j],book)
            for key in keys:columns[key].append(actual[key].imag/1e-25)
        columns={key:np.stack(values,axis=-1) for key,values in columns.items()};context['reference_jacobians']=columns
        metre=case['metre_scale'];jac_error=float(np.max(abs((jac-columns['observation'])*metre[:,None])))
        native_error=float(np.max(abs((native-nominal['observation'])*metre)))
        passed=jac_error<=2e-5 and native_error<=1e-6 and float(np.max(abs((cpp-nominal['observation'])*metre)))<=1e-6
        passed=passed and bool(warning>0 if task['timing']=='boundary' else warning==0)
        discrepancy=lambda key,delta:np.abs(delta)*metre if key in ('coordinates','observation') else np.linalg.norm(delta,ord=2) if key=='attitude' else np.linalg.norm(delta)
        tolerance=lambda key:1e-6 if key in ('coordinates','observation') else 2e-10 if key=='attitude' else 2e-8
        for key in keys:passed=passed and bool(np.all(discrepancy(key,bound['values'][key]-nominal[key])<=tolerance(key)))
        ratio=0.;limited=0
        for i in range(task['probes']):
            rng=np.random.default_rng(np.random.SeedSequence([SEED,case['case_index'],i]))
            z=np.full(27,-1.) if i==0 else np.ones(27) if i==1 else case['center'].copy() if i in (2,3) else rng.uniform(-1.,1.,27)
            if i==3:z[25]=-1.
            record=dict(probe=i,parameters=z);context['records'].append(record)
            actual=reference(case,z,book);native=kernel.value(case,z,book);checks={}
            for key in keys:
                linear=np.tensordot(columns[key],z-case['center'],axes=1)
                error=discrepancy(key,actual[key]-nominal[key]-linear);change=discrepancy(key,actual[key]-nominal[key])
                multiplier=metre if key in ('coordinates','observation') else 1.
                radius=bound['remainders'][key]*multiplier;delta=bound['changes'][key]*multiplier
                tol=tolerance(key)+2e-12*discrepancy(key,linear)
                ok=bool(np.all(error<=radius+tol) and np.all(change<=delta+tol));passed=passed and ok
                relevant=np.asarray(radius)>np.asarray(tol);limited+=int(np.size(relevant)-np.count_nonzero(relevant))
                if np.any(relevant):ratio=max(ratio,float(np.max(np.asarray(error)[relevant]/np.asarray(radius)[relevant])))
                checks[key]=dict(remainder_error=error,remainder_radius=radius,change=change,change_radius=delta,tolerance=tol,passed=ok)
            this_native=float(np.max(abs((native-actual['observation'])*metre)));native_error=max(native_error,this_native)
            passed=passed and this_native<=1e-6;record.update(checks=checks,native_error_m=this_native)
        return dict(passed=passed,calls=book.counts,columns=27,native_boundary_warning=warning,
            boundary_crossings=bound['report']['boundary_crossings'],maximum_native_jacobian_error_m=jac_error,
            maximum_native_error_m=native_error,maximum_resolved_remainder_bound_ratio=ratio,roundoff_limited_checks=limited,
            observation_change_m=bound['changes']['observation']*metre,observation_remainder_m=bound['remainders']['observation']*metre,
            original_reads=0,optimizer_starts=0,scientific_decision='abstain')
    finally:
        context['calls']=book.counts
        if output is not None:write(output,context)


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import ilvis0_history_bounds,ilvis0_increment_remainders
    sources={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    sources.update('analysis/tests/'+n for n in ('ilvis0_history_worker.py','test_ilvis0_history_worker.py','test_ilvis0_history_bounds.py',
        'ilvis0_geographic_worker.py','ilvis0_geographic_bound_harness.c','ilvis0_channel_envelope_worker.py','run_numerical.py'))
    sources.update(['analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','docs/ilvis0-history-bounds/PLAN.md'])
    hashes={name:sha(ROOT/name) for name in sorted(sources)}
    for name in hashes:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    build=base.compile_kernels(DATA)
    write(DATA/'manifest.json',dict(version='native-history-bounds-v1',sources=hashes,environment=environment(),build=build,limits=LIMITS,
        tasks=TASKS,seed=SEED,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS));return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['tasks']!=TASKS:raise ValueError('frozen history scope/environment changed')
    if manifest['build']['compilers']!=base.compilers():raise ValueError('history compiler configuration changed')
    for name,digest in manifest['build']['binaries'].items():
        if sha(DATA/name)!=digest:raise ValueError('history native binary changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('history authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('history frozen source changed: '+name)
    return manifest


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged history controls cannot restart')
        verify();kernel=Kernel(DATA);started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s']
        rows=[];charged=dict(c=0,tangent=0,reference=0);terminal=None
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        try:
            for task in TASKS:
                base.check_time(deadline);identity=task['identity']
                for kind in charged:
                    if charged[kind]+task['maximum_'+kind+'_calls']>LIMITS['maximum_'+kind+'_calls']:raise ValueError('history allowance exhausted')
                write(DATA/'charges'/(identity+'.json'),dict(task,manifest_sha256=sha(DATA/'manifest.json')))
                for kind in charged:charged[kind]+=task['maximum_'+kind+'_calls']
                write(DATA/'status.json',dict(state='running',identity=identity,total=54,numerical_threads=4,pid=os.getpid()),replace=True)
                generated='generated/'+identity+'.json.gz'
                try:result=evaluate(task,kernel,DATA/generated,deadline)
                except base.AllowanceExhausted as error:result=dict(passed=False,error=str(error));terminal=str(error)
                except Exception as error:result=dict(passed=False,error=type(error).__name__+': '+str(error))
                if not (DATA/generated).exists():write(DATA/generated,dict(task=task,error=result.get('error','missing generated evidence')))
                artifact='results/'+identity+'.json';write(DATA/artifact,dict(task,**result,generated_artifact=generated,generated_sha256=sha(DATA/generated)))
                rows.append(dict(task,passed=result['passed'],artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)),replace=True)
                if terminal:break
        except base.AllowanceExhausted as error:terminal=str(error)
        state='terminal' if terminal else 'complete';elapsed=time.time()-started
        write(DATA/'summary.json',dict(state=state,passed=len(rows)==54 and all(r['passed'] for r in rows) and not terminal,results=rows,
            elapsed_s=elapsed,wall_overrun_s=max(0.,elapsed-LIMITS['maximum_wall_s']),terminal_reason=terminal,charged_calls=charged,
            optimizer_starts=0,native_evaluations=0,archive_native_evaluations=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=54,numerical_threads=0),replace=True)
    publish()


def publish():
    manifest=load(DATA/'manifest.json');summary=load(DATA/'summary.json');completion=load(DATA/'completion.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('history completion changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('history result changed')
        result=load(DATA/row['artifact']);results.append(result)
        if sha(DATA/result['generated_artifact'])!=result['generated_sha256']:raise ValueError('history generated evidence changed')
        names.extend([row['artifact'],result['generated_artifact'],'charges/'+row['identity']+'.json'])
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Repeated-history and boundary-timing bounds','',f"**{sum(r['passed'] for r in results)}/54 identities passed** in {summary['elapsed_s']:.2f} seconds. "
        'All inputs are generated; no original reads or archival fits.','',
        '| Packets | Passed | Largest derivative discrepancy | Largest observation remainder bound |','|---|---:|---:|---:|']
    for n in (3,9,33):
        rows=[r for r in results if r['packets']==n]
        jac=max((r.get('maximum_native_jacobian_error_m',0.) for r in rows),default=0.)
        radius=max((max(r.get('observation_remainder_m',[0.])) for r in rows),default=0.)
        lines.append(f"| {n} | {sum(r['passed'] for r in rows)}/{len(rows)} | {jac:.3g} m / normalized parameter | {radius:.6g} m |")
    lines+=['','Complete parameter regions and common timing are retained, including intervals crossing multiple packet boundaries. '
        'A wide bound is not aircraft prediction precision. Long-record arithmetic and observational error assessment remain open.',
        '', '[Frozen question and allowance](PLAN.md) · [Geographic controls](../ilvis0-geographic-step-bounds/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names+=['README.md','PLAN.md']+['source-freeze/'+n for n in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen 54 generated history identities; no execution.')
    elif args.run:run();print('Finite history qualification finished; inspect saved results.')
    else:publish();print('Published saved history results; no prediction calls.')


if __name__=='__main__':main()
