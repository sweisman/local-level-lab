# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated geographic/antenna bound qualification against native kernels."""
import argparse
import ctypes
import fcntl
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_channel_envelope_worker import sha,load,write,environment

NAME='ilvis0-geographic-step-bounds-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-geographic-step-bounds'
MODELS=('sphere_rotating','sphere_still','flat_still');SEED=2026101923
TASKS=[dict(identity=f'{model}-{hemi}-{removal}-{width}-{timing}',model=model,hemisphere=hemi,
    removal_center=removal,width=width,timing=timing,probes=64,maximum_c_calls=65,maximum_tangent_calls=1,maximum_reference_calls=92)
    for model in MODELS for hemi in ('south','north') for removal in ('fixed','lower','upper')
    for width in ('narrow','broad') for timing in ('fixed','interior')]
LIMITS=dict(maximum_identities=72,maximum_probes=4608,maximum_c_calls=4680,maximum_tangent_calls=72,maximum_reference_calls=6624,
    maximum_wall_s=300,numerical_threads=4,original_reads=0,archive_native_evaluations=0,optimizer_starts=0,retries=0,
    deadline_policy='cooperative-no-signals',charges='complete per-identity allowance reserved before execution')
BASE_FLAGS=('-D_DEFAULT_SOURCE','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC')


class AllowanceExhausted(BaseException):pass


def check_time(deadline):
    if time.monotonic()>=deadline:raise AllowanceExhausted('cooperative wall allowance exhausted')


class Calls:
    def __init__(self,c,tangent,reference,deadline=None):
        if any(type(v) is not int or v<1 for v in (c,tangent,reference)):raise ValueError('positive finite call allowances required')
        self.maximum=dict(c=c,tangent=tangent,reference=reference);self.counts=dict(c=0,tangent=0,reference=0);self.deadline=deadline
    def tick(self,kind):
        if self.deadline is not None:check_time(self.deadline)
        if kind not in self.maximum or self.counts[kind]>=self.maximum[kind]:raise ValueError('geographic control allowance exhausted')
        self.counts[kind]+=1


def compilers():
    result={}
    for name,standard in (('cc','-std=c11'),('c++','-std=c++17')):
        found=shutil.which(name)
        if not found:raise ValueError('installed C/C++ compilers required; no downloads')
        path=str(Path(found).resolve());result[name]=dict(executable=path,sha256=sha(Path(path)),
            version=subprocess.check_output([path,'--version'],text=True).splitlines()[0],flags=[standard,*BASE_FLAGS])
    return result


def compile_kernels(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);info=compilers();binaries={}
    for name,source,target in (('cc','analysis/tests/ilvis0_geographic_bound_harness.c','geographic-value.so'),
            ('c++','analysis/lll/ilvis0_tangent.cpp','geographic-tangent.so')):
        item=info[name]
        subprocess.run([item['executable'],*item['flags'],str(ROOT/source),'-o',str(directory/target),'-lm'],
            check=True,capture_output=True,text=True)
        binaries[target]=sha(directory/target)
    return dict(compilers=info,binaries=binaries)


class Kernel:
    def __init__(self,directory):
        pointer=ctypes.POINTER(ctypes.c_double);integer=ctypes.c_int;scalar=ctypes.c_double;size=ctypes.c_size_t
        self.c_library=ctypes.CDLL(str((Path(directory)/'geographic-value.so').resolve()))
        self.c=self.c_library.lll_geographic_bound_value;self.c.argtypes=[integer,pointer,pointer];self.c.restype=None
        self.cpp_library=ctypes.CDLL(str((Path(directory)/'geographic-tangent.so').resolve()))
        self.cpp=self.cpp_library.ilvis0_tangent
        self.cpp.argtypes=[size,pointer,pointer,pointer,size,pointer,pointer,pointer,pointer,pointer,pointer,
            integer,integer,scalar,scalar,pointer,pointer,ctypes.POINTER(integer)];self.cpp.restype=integer
    def value(self,inputs,book=None):
        import numpy as np
        raw=np.concatenate([np.asarray(inputs[k]).ravel() for k in ('coordinates','velocity','attitude','theta','dv','lever')]
            +[np.array([inputs['period'],inputs['gravity'],inputs['radius'],inputs['removal']])])
        if raw.shape!=(28,) or np.iscomplexobj(raw) or not np.all(np.isfinite(raw)):raise ValueError('real finite geographic C inputs required')
        raw=np.ascontiguousarray(raw,dtype=np.float64);out=np.empty(18);pointer=ctypes.POINTER(ctypes.c_double)
        if book:book.tick('c')
        self.c(MODELS.index(inputs['model']),raw.ctypes.data_as(pointer),out.ctypes.data_as(pointer))
        if not np.all(np.isfinite(out)):raise ValueError('nonfinite native geographic output')
        return dict(coordinates=out[:3],velocity=out[3:6],attitude=out[6:15].reshape(3,3),observation=out[15:])
    def tangent(self,case,point,book=None):
        import numpy as np
        arrays=[np.ascontiguousarray(v,dtype=np.float64) for v in
            (case['raw_theta'],case['raw_dv'],[case['packet_dt']],[case['base_time']],case['seed_coordinates'],
             case['seed_velocity'],case['seed_rotation'],case['limits'],point)]
        out=np.empty(3);jac=np.empty((3,27));warning=ctypes.c_int();pointer=ctypes.POINTER(ctypes.c_double)
        p=lambda x:x.ctypes.data_as(pointer)
        if book:book.tick('tangent')
        code=self.cpp(1,p(arrays[0]),p(arrays[1]),p(arrays[2]),1,p(arrays[3]),p(arrays[4]),p(arrays[5]),p(arrays[6]),
            p(arrays[7]),p(arrays[8]),MODELS.index(case['model']),int(case['profile']),9.81,case['radius'],p(out),p(jac),ctypes.byref(warning))
        if code or not np.all(np.isfinite(out)) or not np.all(np.isfinite(jac)):raise ValueError('native tangent failed: '+str(code))
        return out,jac,warning.value


def _skew(v):
    import numpy as np
    x,y,z=v;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def _rates(model,coordinates,vector,radius):
    import numpy as np
    phi,_,height=coordinates
    if model=='flat_still':north=radius;east=radius*(np.pi/2.-phi)
    else:
        d=1.-6.69437999014e-3*np.sin(phi)**2;prime=6378137./np.sqrt(d)
        north=6378137.*(1.-6.69437999014e-3)/(d*np.sqrt(d))+height;east=(prime+height)*np.cos(phi)
    return np.array([vector[0]/north,vector[1]/east,-vector[2]])


def case_inputs(task):
    import numpy as np
    from scipy.linalg import expm
    index=next(i for i,t in enumerate(TASKS) if t['identity']==task['identity']);broad=task['width']=='broad'
    phi=math.radians(-65. if task['hemisphere']=='south' else 65.);packet_dt=.005
    limits=np.zeros(27);limits[:3]=[math.radians(10.),math.radians(10.),math.pi] if broad else [.01,.01,.01]
    limits[3:6]=[15.,15.,5.] if broad else [2.,2.,1.];limits[6:9]=100. if broad else 10.
    limits[9:12]=math.radians(1.)/3600.;limits[12:15]=.25 if broad else .05
    limits[15:18]=.02 if broad else .001;limits[18:21]=.15 if broad else .01
    limits[21:24]=2. if broad else .2;limits[24]=.05 if broad else .01
    limits[25]=.001 if task['timing']=='interior' else 0.;profile=task['removal_center']!='fixed';limits[26]=1. if profile else 0.
    center=.2*np.sin(np.arange(27)*.7+.1);center[25]=-1. if task['hemisphere']=='south' else 1.
    center[26]=-1. if task['removal_center']=='lower' else 1. if profile else 0.
    seed=np.array([phi,math.pi-2e-5,12000.]);radius=6371000.
    unit_n=_rates(task['model'],seed,[1.,0.,0.],radius)[0];unit_e=_rates(task['model'],seed,[0.,1.,0.],radius)[1]
    return dict(case_index=index,model=task['model'],profile=profile,timing=task['timing'],limits=limits,center=center,
        packet_dt=packet_dt,base_time=packet_dt if task['timing']=='fixed' else packet_dt*.5,radius=radius,
        seed_coordinates=seed,seed_velocity=np.array([210.*math.cos(.8),210.*math.sin(.8),-.1]),
        seed_rotation=expm(_skew([.03,-.02,.7])),raw_theta=np.array([3e-5,-2e-5,1e-5]),
        raw_dv=np.array([.0001,-.0002,-9.81*packet_dt]),metre_scale=np.array([1./unit_n,1./unit_e,1.]))


def reference(case,point,book=None):
    import numpy as np
    from scipy.linalg import expm
    if book:book.tick('reference')
    p=case['limits']*np.asarray(point);model=case['model'];radius=case['radius'];dt0=case['packet_dt']
    coordinates=case['seed_coordinates']+_rates(model,case['seed_coordinates'],p[6:9],radius)
    velocity=case['seed_velocity']+p[3:6];attitude=case['seed_rotation']@expm(_skew(p[:3]))
    theta=(case['raw_theta']-p[9:12]*dt0)/(1.+p[15:18]);dv=(case['raw_dv']-p[12:15]*dt0)/(1.+p[18:21])
    period=case['base_time']+p[25];fraction=period/dt0;theta=theta*fraction;dv=dv*fraction
    removal=(p[26]+1.)/2. if case['profile'] else 0.;gravity=9.81+p[24]
    def context(phi,rate):
        standard=7.2921150e-5*np.array([np.cos(phi),0.,-np.sin(phi)])
        earth=standard if model=='sphere_rotating' else np.zeros(3,dtype=standard.dtype)
        transport=np.array([0.,0.,-rate[1]]) if model=='flat_still' else np.array([np.cos(phi)*rate[1],-rate[0],-np.sin(phi)*rate[1]])
        return earth,transport,standard
    def local(phi,rate):
        earth,transport,standard=context(phi,rate);win=earth+transport-removal*standard;a=(2*earth+transport)*period/2.
        middle=expm(_skew(-win*period/2.))@attitude@expm(_skew(theta/2.))
        next_r=expm(_skew(-win*period))@attitude@expm(_skew(theta))
        next_v=np.linalg.solve(np.eye(3)+_skew(a),(np.eye(3)-_skew(a))@velocity+middle@dv+np.array([0.,0.,gravity*period]))
        return next_r,next_v
    old=_rates(model,coordinates,velocity,radius);midpoint=coordinates+old*period/2.
    _,estimate=local(midpoint[0],old);revised=_rates(model,midpoint,(velocity+estimate)/2.,radius)
    final_r,final_v=local(midpoint[0],revised);final_c=coordinates+revised*period
    antenna=final_c+_rates(model,final_c,final_r@p[21:24],radius)
    return dict(coordinates=final_c,velocity=final_v,attitude=final_r,observation=antenna,
        inputs=dict(model=model,coordinates=coordinates,velocity=velocity,attitude=attitude,theta=theta,dv=dv,
            lever=p[21:24],period=period,gravity=gravity,radius=radius,removal=removal))


def enclosure(case):
    import numpy as np
    from lll import ilvis0_geographic_bounds as g
    from lll.ilvis0_local_step_bounds import Value,Matrix
    from lll.ilvis0_forward import exp
    from lll.ilvis0_increment_remainders import calibrated_box
    limits=case['limits'];z0=case['center'];p=limits*z0;delta=limits*np.maximum(abs(-1.-z0),abs(1.-z0))
    def vector(section):return Value(p[section],float(np.linalg.norm(delta[section])))
    seed=g.Coordinates(*(g.Scalar.fixed(v) for v in case['seed_coordinates']))
    initial_offsets=g.coordinate_map(seed,vector(slice(6,9)),model=case['model'],disc_radius_m=case['radius'])
    position=g.Coordinates(*(g.plus(v,o) for v,o in zip((seed.latitude,seed.longitude,seed.height),initial_offsets)))
    attitude_radius=float(np.linalg.norm(delta[:3]));attitude=Matrix(case['seed_rotation']@exp(p[:3]),min(2.,attitude_radius),.5*attitude_radius**2,'rotation')
    state=g.State(position,Value(case['seed_velocity']+p[3:6],float(np.linalg.norm(delta[3:6]))),attitude)
    def corrected(raw,bias_slice,gain_slice):
        b=calibrated_box(raw,case['packet_dt'],bias_center=p[bias_slice],gain_center=p[gain_slice],
            bias_lower=-limits[bias_slice],bias_upper=limits[bias_slice],gain_lower=-limits[gain_slice],gain_upper=limits[gain_slice])
        return Value(b['center'],b['change_radius'],b['remainder_radius'])
    theta=corrected(case['raw_theta'],slice(9,12),slice(15,18));dv=corrected(case['raw_dv'],slice(12,15),slice(18,21))
    fraction=g.Scalar.interval((case['base_time']+p[25])/case['packet_dt'],
        (case['base_time']-limits[25])/case['packet_dt'],(case['base_time']+limits[25])/case['packet_dt'])
    removal=g.Scalar.interval((p[26]+1.)/2.,0.,1.) if case['profile'] else g.Scalar.fixed(0.)
    gravity=g.Scalar.interval(9.81+p[24],9.81-limits[24],9.81+limits[24])
    endpoint=g.partial_packet(state,theta,dv,packet_dt=case['packet_dt'],fraction=fraction,removal=removal,
        gravity=gravity,model=case['model'],disc_radius_m=case['radius'])
    antenna=g.observation(endpoint,vector(slice(21,24)),model=case['model'],disc_radius_m=case['radius'])
    def components(c):return (c.latitude,c.longitude,c.height)
    return dict(values=dict(coordinates=endpoint.position.center,velocity=endpoint.velocity.center,attitude=endpoint.attitude.center,observation=antenna.center),
        changes=dict(coordinates=np.array([v.value.change for v in components(endpoint.position)]),velocity=endpoint.velocity.change,
            attitude=endpoint.attitude.change,observation=np.array([v.value.change for v in components(antenna)])),
        remainders=dict(coordinates=np.array([v.value.remainder for v in components(endpoint.position)]),velocity=endpoint.velocity.remainder,
            attitude=endpoint.attitude.remainder,observation=np.array([v.value.remainder for v in components(antenna)])),
        state_report=endpoint.report(),observation_report=antenna.report())


def evaluate(task,kernel,output=None,deadline=None):
    import numpy as np
    book=Calls(task['maximum_c_calls'],task['maximum_tangent_calls'],task['maximum_reference_calls'],deadline)
    case=case_inputs(task);context=dict(task=task,inputs=case,records=[]);keys=('coordinates','velocity','attitude','observation')
    try:
        bound=enclosure(case);context['analytic_bound']=bound;nominal=reference(case,case['center'],book)
        native_nominal=kernel.value(nominal['inputs'],book);cpp,jac_cpp,boundaries=kernel.tangent(case,case['center'],book)
        derivatives={key:[] for key in keys}
        for column in range(27):
            response=reference(case,case['center']+1e-25j*np.eye(27)[column],book)
            for key in keys:derivatives[key].append(response[key].imag/1e-25)
        derivatives={key:np.stack(value,axis=-1) for key,value in derivatives.items()};context['reference_jacobians']=derivatives
        jac_error=float(np.max(abs((jac_cpp-derivatives['observation'])*case['metre_scale'][:,None])))
        nominal_cpp_error=float(np.max(abs((cpp-nominal['observation'])*case['metre_scale'])))
        passed=jac_error<=1e-6 and nominal_cpp_error<=2e-8 and (task['timing']=='fixed' or boundaries==0)
        maximum_native=nominal_cpp_error;maximum_ratio=0.;roundoff_limited=0
        def discrepancy(key,delta):
            if key in ('coordinates','observation'):return np.abs(delta)*case['metre_scale']
            return np.linalg.norm(delta,ord=2) if key=='attitude' else np.linalg.norm(delta)
        def base_tolerance(key):return 2e-8 if key in ('coordinates','observation') else 2e-12 if key=='attitude' else 2e-10
        for key in keys:
            for value in (native_nominal[key],bound['values'][key]):
                error=discrepancy(key,value-nominal[key]);passed=passed and bool(np.all(error<=base_tolerance(key)))
        for i in range(task['probes']):
            rng=np.random.default_rng(np.random.SeedSequence([SEED,case['case_index'],i]))
            z=np.full(27,-1.) if i==0 else np.ones(27) if i==1 else case['center'].copy() if i==2 else rng.uniform(-1.,1.,27)
            record=dict(probe=i,normalized_parameters=z);context['records'].append(record)
            actual=reference(case,z,book);native=kernel.value(actual['inputs'],book);comparisons={};okay=True
            for key in keys:
                linear=np.tensordot(derivatives[key],z-case['center'],axes=1)
                error=discrepancy(key,actual[key]-nominal[key]-linear);change=discrepancy(key,actual[key]-nominal[key])
                native_error=discrepancy(key,native[key]-actual[key]);multiplier=case['metre_scale'] if key in ('coordinates','observation') else 1.
                radius=bound['remainders'][key]*multiplier;delta_radius=bound['changes'][key]*multiplier
                tolerance=base_tolerance(key)+2e-12*discrepancy(key,linear)
                accepted=bool(np.all(error<=radius+tolerance) and np.all(change<=delta_radius+tolerance) and np.all(native_error<=tolerance))
                relevant=np.asarray(radius)>np.asarray(tolerance);roundoff_limited+=int(np.size(relevant)-np.count_nonzero(relevant))
                if np.any(relevant):maximum_ratio=max(maximum_ratio,float(np.max(np.asarray(error)[relevant]/np.asarray(radius)[relevant])))
                comparisons[key]=dict(actual=actual[key],linear_delta=linear,remainder_error=error,change=change,
                    radius=radius,repository_reference_error=native_error,tolerance=tolerance,passed=accepted)
                maximum_native=max(maximum_native,float(np.max(native_error)));okay=okay and accepted
            record.update(comparisons=comparisons,passed=okay);passed=passed and okay
        return dict(passed=passed,probe_count=len(context['records']),parameter_columns=27,timing_fixed=task['timing']=='fixed',
            native_boundary_warning=boundaries,c_calls=book.counts['c'],tangent_calls=book.counts['tangent'],reference_calls=book.counts['reference'],
            maximum_native_jacobian_error_m=jac_error,maximum_native_value_discrepancy=maximum_native,
            maximum_resolved_remainder_bound_ratio=maximum_ratio,roundoff_limited_component_checks=roundoff_limited,
            packet_boundary_crossing_covered=False,floating_point_enclosure_verified=False,scientific_decision='abstain')
    finally:
        if output is not None:write(output,context)


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import ilvis0_geographic_bounds,ilvis0_increment_remainders
    sources={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    sources.update('analysis/tests/'+name for name in ('ilvis0_geographic_worker.py','ilvis0_geographic_bound_harness.c',
        'ilvis0_channel_envelope_worker.py','run_numerical.py','test_ilvis0_geographic_bounds.py','test_ilvis0_geographic_worker.py'))
    sources.update(['analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','docs/ilvis0-geographic-step-bounds/PLAN.md'])
    hashes={name:sha(ROOT/name) for name in sorted(sources)}
    for name in hashes:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    build=compile_kernels(DATA)
    write(DATA/'manifest.json',dict(version='native-geographic-global-bounds-v1',sources=hashes,environment=environment(),build=build,
        limits=LIMITS,plan=dict(tasks=TASKS,numerical_threads=4),seed=SEED,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS));return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['plan']['tasks']!=TASKS:
        raise ValueError('frozen environment or finite task scope changed')
    if manifest['build']['compilers']!=compilers():raise ValueError('compiler configuration changed')
    for name,digest in manifest['build']['binaries'].items():
        if sha(DATA/name)!=digest:raise ValueError('frozen native binary changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('frozen source changed: '+name)
    return manifest


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged geographic controls cannot restart')
        verify();kernel=Kernel(DATA);started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s']
        rows=[];charged=dict(c=0,tangent=0,reference=0);terminal=None
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        try:
            for task in TASKS:
                check_time(deadline);identity=task['identity']
                for name in charged:
                    if charged[name]+task['maximum_'+name+'_calls']>LIMITS['maximum_'+name+'_calls']:raise ValueError('total allowance exhausted')
                write(DATA/'charges'/(identity+'.json'),dict(task,manifest_sha256=sha(DATA/'manifest.json')))
                for name in charged:charged[name]+=task['maximum_'+name+'_calls']
                write(DATA/'status.json',dict(state='running',identity=identity,total=72,numerical_threads=4,pid=os.getpid()),replace=True)
                generated='generated/'+identity+'.json.gz'
                try:result=evaluate(task,kernel,DATA/generated,deadline)
                except AllowanceExhausted as error:result=dict(passed=False,error=str(error));terminal=str(error)
                except Exception as error:result=dict(passed=False,error=type(error).__name__+': '+str(error))
                artifact='results/'+identity+'.json';write(DATA/artifact,dict(task,**result,generated_artifact=generated,
                    generated_sha256=sha(DATA/generated)))
                rows.append(dict(task,passed=result['passed'],artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                write(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['passed'] for r in rows)),replace=True)
                if terminal:break
        except AllowanceExhausted as error:terminal=str(error)
        state='terminal' if terminal else 'complete';elapsed=time.time()-started
        write(DATA/'summary.json',dict(state=state,passed=len(rows)==72 and all(r['passed'] for r in rows) and not terminal,
            results=rows,elapsed_s=elapsed,wall_overrun_s=max(0.,elapsed-LIMITS['maximum_wall_s']),terminal_reason=terminal,
            charged_calls=charged,optimizer_starts=0,native_evaluations=0,archive_native_evaluations=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=72,numerical_threads=0),replace=True)
    publish()


def publish():
    manifest=load(DATA/'manifest.json');completion=load(DATA/'completion.json');summary=load(DATA/'summary.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):
        raise ValueError('completed geographic controls changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('geographic control result changed')
        result=load(DATA/row['artifact']);results.append(result)
        if sha(DATA/result['generated_artifact'])!=result['generated_sha256']:raise ValueError('generated evidence changed')
        names.extend([row['artifact'],result['generated_artifact'],'charges/'+row['identity']+'.json'])
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    calls=summary['charged_calls']
    lines=['# Geographic-step and antenna-observation bounds','',
        f"**{sum(r['passed'] for r in results)}/72 identities passed** in {summary['elapsed_s']:.2f} seconds. "
        f"Charged calls: {calls['c']:,} C steps, {calls['tangent']:,} C++ tangents and {calls['reference']:,} independent references. "
        'All inputs are generated; no archive reads, full-record sweeps or optimizer starts.','',
        '| Candidate | Passed | Maximum C++ Jacobian discrepancy | Largest resolved remainder / bound |',
        '|---|---:|---:|---:|']
    for model in MODELS:
        selected=[r for r in results if r['model']==model]
        jac=max((r.get('maximum_native_jacobian_error_m',0.) for r in selected),default=0.)
        ratio=max((r.get('maximum_resolved_remainder_bound_ratio',0.) for r in selected),default=0.)
        lines.append(f"| {model} | {sum(r['passed'] for r in selected)}/{len(selected)} | {jac:.3g} m / normalized parameter | {ratio:.6g} |")
    lines+=['','All 27 columns remain present. Timing is either fixed at the endpoint or varies strictly inside one packet. '
        'Intervals crossing packet boundaries, repeated-step usefulness, long-record arithmetic and observational error assessment remain unqualified. '
        'Roundoff-limited comparisons are retained separately; the displayed remainder ratio excludes bounds below the declared comparison tolerance.',
        '', '[Proof and frozen limits](PLAN.md) · [Local-step controls](../ilvis0-local-step-bounds/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names+=['README.md','PLAN.md']+['source-freeze/'+name for name in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen 72 geographic identities and both kernels; no execution.')
    elif args.run:run();print('Finite geographic-step qualification finished; inspect saved results.')
    else:publish();print('Published saved geographic controls; no native or reference calls.')


if __name__=='__main__':main()
