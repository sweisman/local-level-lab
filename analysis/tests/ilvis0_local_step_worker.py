# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite midpoint-bound controls with a frozen C harness and independent reference."""
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

NAME='ilvis0-local-step-bounds-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-local-step-bounds'
HARNESS=ROOT/'analysis/tests/ilvis0_local_bound_harness.c'
CFLAGS=('-std=c11','-D_DEFAULT_SOURCE','-O2','-fno-fast-math','-ffp-contract=off','-shared','-fPIC')
SEED=2026101922
MODELS=('sphere_rotating','sphere_still','flat_still')
TASKS=[dict(identity=f'{model}-{hemisphere}-{int(profile)}-{width}',model=model,hemisphere=hemisphere,profile=profile,
    width=width,zero_center=False,probes=64,maximum_native_calls=65,maximum_reference_calls=129)
    for model in MODELS for hemisphere in ('south','north') for profile in (False,True) for width in ('narrow','broad')]+[
    dict(identity=f'{model}-zero-{int(profile)}',model=model,hemisphere='zero',profile=profile,width='narrow',
        zero_center=True,probes=64,maximum_native_calls=65,maximum_reference_calls=129) for model in MODELS for profile in (False,True)]
LIMITS=dict(maximum_identities=30,maximum_probes=1920,maximum_software_native_calls=1950,maximum_reference_calls=3870,
    maximum_wall_s=300,numerical_threads=4,original_reads=0,archive_native_evaluations=0,optimizer_starts=0,retries=0,
    deadline_policy='cooperative-no-signals',charges='complete per-identity allowance reserved before execution')


class AllowanceExhausted(BaseException):pass


def check_time(deadline):
    if time.monotonic()>=deadline:raise AllowanceExhausted('cooperative wall allowance exhausted')


class Calls:
    def __init__(self,native,reference,deadline=None):
        if any(type(v) is not int or v<1 for v in (native,reference)):raise ValueError('positive finite call allowances required')
        self.maximum=dict(native=native,reference=reference);self.counts=dict(native=0,reference=0);self.deadline=deadline
    def tick(self,kind):
        if self.deadline is not None:check_time(self.deadline)
        if kind not in self.maximum or self.counts[kind]>=self.maximum[kind]:raise ValueError('local-step call allowance exhausted')
        self.counts[kind]+=1


def compiler_info():
    path=shutil.which('cc')
    if not path:raise ValueError('installed C compiler required; no download')
    compiler=str(Path(path).resolve())
    return dict(executable=compiler,sha256=sha(Path(compiler)),
        version=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0],flags=list(CFLAGS))


def compile_kernel(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);info=compiler_info()
    binary=directory/'local-bound-kernel.so'
    subprocess.run([info['executable'],*CFLAGS,str(HARNESS),'-o',str(binary),'-lm'],check=True,capture_output=True,text=True)
    return dict(compiler=info,binary_sha256=sha(binary),harness_sha256=sha(HARNESS),kernel_sha256=sha(ROOT/'analysis/lll/ilvis0_native.c'))


class Kernel:
    def __init__(self,path):
        self.library=ctypes.CDLL(str(Path(path).resolve()));self.function=self.library.lll_local_bound_value
        pointer=ctypes.POINTER(ctypes.c_double);scalar=ctypes.c_double
        self.function.argtypes=[pointer,pointer,pointer,pointer,scalar,pointer,pointer,scalar,scalar,scalar,pointer,pointer]
        self.function.restype=None
    def value(self,inputs,book=None):
        import numpy as np
        arrays=[]
        for name,size in (('attitude',9),('velocity',3),('theta',3),('dv',3),('earth',3),('transport',3)):
            value=np.asarray(inputs[name])
            if value.size!=size or np.iscomplexobj(value) or not np.all(np.isfinite(value)):raise ValueError('real finite local C inputs required')
            arrays.append(np.ascontiguousarray(value,dtype=np.float64).ravel())
        attitude=np.empty(9);velocity=np.empty(3);pointer=ctypes.POINTER(ctypes.c_double)
        p=lambda a:a.ctypes.data_as(pointer)
        if book:book.tick('native')
        self.function(p(arrays[0]),p(arrays[1]),p(arrays[2]),p(arrays[3]),inputs['dt'],p(arrays[4]),p(arrays[5]),
            float(inputs['latitude']),float(inputs['removal']),float(inputs['gravity']),p(attitude),p(velocity))
        if not np.all(np.isfinite(attitude)) or not np.all(np.isfinite(velocity)):raise ValueError('nonfinite native local output')
        return dict(attitude=attitude.reshape(3,3),velocity=velocity,
            local_displacement=(arrays[1]+velocity)*inputs['dt']/2.)


def case_inputs(task):
    import numpy as np
    broad=task['width']=='broad';zero=task['zero_center'];sign=-1. if task['hemisphere']=='south' else 1.
    phi=0. if zero else sign*math.radians(65.);dt=.01 if zero else .005
    attitude=np.zeros(3) if zero else np.array([.03,-.02,.7])
    velocity=np.zeros(3) if zero else np.array([210.*math.cos(.8),210.*math.sin(.8),-.1])
    theta=np.zeros(3) if zero else np.array([3e-5,-2e-5,1e-5]);dv=np.array([.0001,-.0002,-9.81*dt])
    if zero:dv=np.array([0.,0.,-9.81*dt])
    transport=np.zeros(3) if zero else np.array([velocity[1]/6371000.,-velocity[0]/6371000.,-velocity[1]*math.tan(phi)/6371000.])
    if task['model']=='flat_still':transport[:2]=0.
    widths=np.zeros(24)
    widths[:3]=[math.radians(10.),math.radians(10.),math.pi] if broad else [.01,.01,.01]
    widths[3:6]=[15.,15.,5.] if broad else [2.,2.,1.]
    widths[6:9]=math.radians(1.)/3600.;widths[9:12]=.02 if broad else .001
    widths[12:15]=.25 if broad else .05;widths[15:18]=.15 if broad else .01
    widths[18]=.01 if broad else 1e-5;widths[19:22]=1e-4 if broad else 1e-6
    if task['model']=='flat_still':widths[19:21]=0.
    widths[22]=.5 if task['profile'] else 0.;widths[23]=.05 if broad else .01
    index=next(i for i,t in enumerate(TASKS) if t['identity']==task['identity'])
    return dict(model=task['model'],case_index=index,attitude_vector=attitude,velocity=velocity,raw_theta=theta,raw_dv=dv,
        latitude=phi,transport=transport,removal=.5 if task['profile'] else 0.,gravity=9.81,dt=dt,widths=widths)


def reference(case,normalized,book=None):
    import numpy as np
    from scipy.linalg import expm
    if book:book.tick('reference')
    z=np.asarray(normalized);w=case['widths'];dt=case['dt']
    def skew(v):
        x,y,z=v;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    attitude=expm(skew(case['attitude_vector']+w[:3]*z[:3]));velocity=case['velocity']+w[3:6]*z[3:6]
    theta=(case['raw_theta']-w[6:9]*z[6:9]*dt)/(1.+w[9:12]*z[9:12])
    dv=(case['raw_dv']-w[12:15]*z[12:15]*dt)/(1.+w[15:18]*z[15:18])
    phi=case['latitude']+w[18]*z[18];transport=case['transport']+w[19:22]*z[19:22]
    removal=case['removal']+w[22]*z[22];gravity=case['gravity']+w[23]*z[23]
    standard=7.2921150e-5*np.array([np.cos(phi),0.,-np.sin(phi)])
    earth=standard if case['model']=='sphere_rotating' else np.zeros(3,dtype=z.dtype)
    win=earth+transport-removal*standard;a=(2.*earth+transport)*dt/2.
    middle=expm(skew(-win*dt/2.))@attitude@expm(skew(theta/2.))
    final_attitude=expm(skew(-win*dt))@attitude@expm(skew(theta))
    final_velocity=np.linalg.solve(np.eye(3)+skew(a),(np.eye(3)-skew(a))@velocity+middle@dv+np.array([0.,0.,gravity*dt]))
    inputs=dict(attitude=attitude,velocity=velocity,theta=theta,dv=dv,earth=earth,transport=transport,
        latitude=phi,removal=removal,gravity=gravity,dt=dt)
    return dict(attitude=final_attitude,velocity=final_velocity,local_displacement=(velocity+final_velocity)*dt/2.,inputs=inputs)


def enclosure(case):
    import numpy as np
    from lll.ilvis0_forward import exp
    from lll.ilvis0_increment_remainders import calibrated_box
    from lll.ilvis0_local_step_bounds import Value,Matrix,local_bound
    w=case['widths'];dt=case['dt'];zero=np.zeros(3)
    def calibrated(raw,bias,gain):
        box=calibrated_box(raw,dt,bias_center=zero,gain_center=zero,bias_lower=-bias,bias_upper=bias,gain_lower=-gain,gain_upper=gain)
        return Value(box['center'],box['change_radius'],box['remainder_radius'])
    rotation_change=float(np.linalg.norm(w[:3]));attitude=Matrix(exp(case['attitude_vector']),min(2.,rotation_change),.5*rotation_change**2,'rotation')
    return local_bound(model=case['model'],attitude=attitude,velocity=Value(case['velocity'],float(np.linalg.norm(w[3:6]))),
        theta=calibrated(case['raw_theta'],w[6:9],w[9:12]),dv=calibrated(case['raw_dv'],w[12:15],w[15:18]),
        latitude=Value(case['latitude'],w[18]),transport=Value(case['transport'],float(np.linalg.norm(w[19:22]))),
        removal=Value(case['removal'],w[22]),gravity=Value(case['gravity'],w[23]),dt=dt)


def evaluate(task,kernel,output=None,deadline=None):
    import numpy as np
    book=Calls(task['maximum_native_calls'],task['maximum_reference_calls'],deadline);case=case_inputs(task)
    context=dict(task=task,inputs=case,records=[])
    try:
        bound=enclosure(case);context['analytic_bound']={k:bound[k].report() for k in ('attitude','velocity','local_displacement')}
        nominal=reference(case,np.zeros(24),book);native_nominal=kernel.value(nominal['inputs'],book)
        maximum_native=0.;maximum_ratio=0.;passed=True
        def norm(v):return float(np.linalg.norm(v,ord=2)) if np.ndim(v)==2 else float(np.linalg.norm(v))
        def tol(v,linear,radius):return 2e-12*(1.+norm(v)+norm(linear)+radius)
        for key in ('attitude','velocity','local_displacement'):
            error=max(norm(native_nominal[key]-nominal[key]),norm(bound[key].center-nominal[key]))
            maximum_native=max(maximum_native,error);passed=passed and error<=tol(nominal[key],0.,0.)
        context['nominal_reference']={k:nominal[k] for k in ('attitude','velocity','local_displacement')}
        for i in range(task['probes']):
            rng=np.random.default_rng(np.random.SeedSequence([SEED,case['case_index'],i]))
            z=np.full(24,-1.) if i==0 else np.ones(24) if i==1 else np.zeros(24) if i==2 else rng.uniform(-1.,1.,24)
            record=dict(probe=i,normalized_parameters=z);context['records'].append(record)
            actual=reference(case,z,book);native=kernel.value(actual['inputs'],book)
            directional=reference(case,1e-25j*z,book);comparisons={};okay=True
            for key in ('attitude','velocity','local_displacement'):
                linear=directional[key].imag/1e-25
                error=norm(actual[key]-nominal[key]-linear);change=norm(actual[key]-nominal[key])
                native_error=norm(native[key]-actual[key]);radius=bound[key].remainder;tolerance=tol(actual[key],linear,radius)
                accepted=change<=bound[key].change+tolerance and error<=radius+tolerance and native_error<=tolerance
                comparisons[key]=dict(actual=actual[key],linear_delta=linear,remainder_norm=error,change_norm=change,
                    repository_reference_error=native_error,tolerance=tolerance,passed=accepted)
                okay=okay and accepted;maximum_native=max(maximum_native,native_error)
                if radius:maximum_ratio=max(maximum_ratio,error/radius)
            record.update(comparisons=comparisons,passed=okay);passed=passed and okay
        return dict(passed=passed,probe_count=len(context['records']),software_native_calls=book.counts['native'],
            reference_calls=book.counts['reference'],maximum_remainder_bound_ratio=maximum_ratio,
            maximum_repository_reference_error=maximum_native,native_full_map_covered=False,
            floating_point_enclosure_verified=False,scientific_decision='abstain')
    finally:
        if output is not None:write(output,context)


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import ilvis0_local_step_bounds,ilvis0_increment_remainders
    sources={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    sources.update('analysis/tests/'+name for name in ('ilvis0_local_step_worker.py','ilvis0_local_bound_harness.c',
        'ilvis0_channel_envelope_worker.py','run_numerical.py','test_ilvis0_local_step_bounds.py','test_ilvis0_local_step_worker.py'))
    sources.update(['analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','docs/ilvis0-local-step-bounds/PLAN.md'])
    hashes={name:sha(ROOT/name) for name in sorted(sources)}
    for name in hashes:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    binary=compile_kernel(DATA)
    write(DATA/'manifest.json',dict(version='native-midpoint-local-global-bounds-v1',sources=hashes,environment=environment(),
        build=binary,limits=LIMITS,plan=dict(tasks=TASKS,numerical_threads=4),seed=SEED,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS));return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['plan']['tasks']!=TASKS:
        raise ValueError('frozen environment or finite task scope changed')
    if manifest['build']['compiler']!=compiler_info() or manifest['build']['binary_sha256']!=sha(DATA/'local-bound-kernel.so'):
        raise ValueError('compiler or frozen kernel binary changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('frozen source changed: '+name)
    return manifest


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged local-step controls cannot restart')
        verify();kernel=Kernel(DATA/'local-bound-kernel.so');started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s']
        rows=[];native_charged=0;reference_charged=0;terminal=None
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        try:
            for task in TASKS:
                check_time(deadline);identity=task['identity']
                if (native_charged+task['maximum_native_calls']>LIMITS['maximum_software_native_calls']
                        or reference_charged+task['maximum_reference_calls']>LIMITS['maximum_reference_calls']):
                    raise ValueError('total local-step allowance exhausted')
                write(DATA/'charges'/(identity+'.json'),dict(task,manifest_sha256=sha(DATA/'manifest.json')))
                native_charged+=task['maximum_native_calls'];reference_charged+=task['maximum_reference_calls']
                write(DATA/'status.json',dict(state='running',identity=identity,total=30,numerical_threads=4,pid=os.getpid()),replace=True)
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
        elapsed=time.time()-started;state='terminal' if terminal else 'complete'
        write(DATA/'summary.json',dict(state=state,passed=len(rows)==30 and all(r['passed'] for r in rows) and not terminal,
            results=rows,elapsed_s=elapsed,wall_overrun_s=max(0.,elapsed-LIMITS['maximum_wall_s']),terminal_reason=terminal,
            charged_software_native_calls=native_charged,charged_reference_calls=reference_charged,
            optimizer_starts=0,native_evaluations=0,archive_native_evaluations=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=30,numerical_threads=0),replace=True)
    publish()


def publish():
    completion=load(DATA/'completion.json');summary=load(DATA/'summary.json');manifest=load(DATA/'manifest.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):
        raise ValueError('completed local-step controls changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('local-step result changed')
        result=load(DATA/row['artifact']);results.append(result)
        if sha(DATA/result['generated_artifact'])!=result['generated_sha256']:raise ValueError('generated probe evidence changed')
        names.extend([row['artifact'],result['generated_artifact'],'charges/'+row['identity']+'.json'])
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Native midpoint local-step bounds','',
        f"**{sum(r['passed'] for r in results)}/30 identities passed** in {summary['elapsed_s']:.2f} seconds. "
        f"The study charged {summary['charged_software_native_calls']:,} C local-step calls and {summary['charged_reference_calls']:,} independent reference calls, all on generated inputs. "
        'No archive originals, full-record native sweeps or optimizer starts.','',
        '| Candidate | Passed | Largest actual remainder / bound | Largest C/reference discrepancy |','|---|---:|---:|---:|']
    for model in MODELS:
        selected=[r for r in results if r['model']==model]
        ratio=max((r.get('maximum_remainder_bound_ratio',0.) for r in selected),default=0.)
        error=max((r.get('maximum_repository_reference_error',0.) for r in selected),default=0.)
        lines.append(f"| {model} | {sum(r['passed'] for r in selected)}/{len(selected)} | {ratio:.6g} | {error:.3g} |")
    lines+=['','The bounds retain joint calibration, attitude, force, latitude and processing-removal effects. '
        'Rate removal changes attitude propagation while physical Coriolis stays unchanged. '
        'Inputs must themselves have valid global bounds. Geographic predictor/corrector closure, receiver timing and long-record arithmetic remain open.',
        '', '[Proof and frozen limits](PLAN.md) · [Previous increment components](../ilvis0-increment-remainders/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names+=['README.md','PLAN.md']+['source-freeze/'+name for name in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen 30 local-step identities and C harness; no control execution.')
    elif args.run:run();print('Finite midpoint local-step qualification complete; inspect saved results.')
    else:publish();print('Published saved local-step controls; no native or reference calls.')


if __name__=='__main__':main()
