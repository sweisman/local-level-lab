# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite global increment-bound controls against an independent matrix reference."""
import argparse
import fcntl
import math
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_channel_envelope_worker import sha,load,write,environment

NAME='ilvis0-increment-remainders-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-increment-remainders'
SEED=2026101921
TASKS=[dict(identity=f'cal-{channel}-{center}-{width}',kind='calibration',channel=channel,center=center,width=width,
    probes=64,maximum_calls=64) for channel in ('angle','velocity') for center in ('lower','zero','upper') for width in ('narrow','broad')]+[
    dict(identity=f'packet-{map_kind}-{center}-{width}',kind='packet',map_kind=map_kind,center=center,width=width,
        probes=64,maximum_calls=132) for map_kind in ('rotation','velocity','position') for center in ('small','large') for width in ('narrow','broad')]+[
    dict(identity=f'history-{packets}-{width}',kind='history',packets=packets,width=width,probes=64,maximum_calls=133*packets)
    for packets in (1,7,31) for width in ('narrow','broad')]
LIMITS=dict(maximum_identities=30,maximum_probes=1920,maximum_software_evaluations=13000,maximum_packets=31,
    maximum_wall_s=300,numerical_threads=4,original_reads=0,optimizer_starts=0,native_evaluations=0,retries=0,
    deadline_policy='cooperative-no-signals',charges='complete per-identity allowance reserved before execution')


class AllowanceExhausted(BaseException):pass


def check_time(deadline):
    if time.monotonic()>=deadline:raise AllowanceExhausted('cooperative wall allowance exhausted')


class Calls:
    def __init__(self,maximum,deadline=None):
        if type(maximum) is not int or maximum<1:raise ValueError('positive fixed reference-call allowance required')
        self.maximum=maximum;self.count=0;self.deadline=deadline
    def tick(self):
        if self.deadline is not None:check_time(self.deadline)
        if self.count>=self.maximum:raise ValueError('software reference allowance exhausted')
        self.count+=1


def reference(theta,book,derivatives=False):
    """Independent block exponential, not Rodrigues or repository preintegration."""
    import numpy as np
    from scipy.linalg import expm,expm_frechet
    def skew(v):
        x,y,z=v;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    a=np.zeros((9,9));a[:3,:3]=skew(theta);a[:3,3:6]=np.eye(3);a[3:6,6:]=np.eye(3)
    def blocks(value):return np.array([value[:3,:3],value[:3,3:6],value[:3,6:9]])
    book.tick();maps=blocks(expm(a))
    if not derivatives:return maps
    derivative=[]
    for axis in range(3):
        direction=np.zeros((9,9));direction[:3,:3]=skew(np.eye(3)[axis])
        book.tick();derivative.append(blocks(expm_frechet(a,direction,compute_expm=False)))
    return maps,np.array(derivative)


def calibration_arguments(channel,width,center='zero',raw=None,dt=.005):
    import numpy as np
    if channel=='angle':
        limit=math.radians(1. if width=='narrow' else 10.)/3600.;gain=.001 if width=='narrow' else .02
        if raw is None:raw=[3e-5,-2e-5,1e-5]
    else:
        limit=.05 if width=='narrow' else .25;gain=.01 if width=='narrow' else .15
        if raw is None:raw=[.0001,-.0002,-9.81*dt]
    center_sign={'lower':-1.,'zero':0.,'upper':1.}[center]
    return dict(raw=np.array(raw,float),dt=dt,bias_center=np.full(3,center_sign*limit),gain_center=np.full(3,center_sign*gain),
        bias_lower=np.full(3,-limit),bias_upper=np.full(3,limit),gain_lower=np.full(3,-gain),gain_upper=np.full(3,gain))


def tolerance(reference_value,linear,radius):
    import numpy as np
    return 1e-12*(1.+float(np.linalg.norm(reference_value))+float(np.linalg.norm(linear))+radius)


def calibration_control(task,book,context):
    import numpy as np
    from lll.ilvis0_increment_remainders import calibrated_box
    arguments=calibration_arguments(task['channel'],task['width'],task['center']);box=calibrated_box(**arguments)
    context.update(inputs=arguments,analytic_bound=box);passed=True;maximum_ratio=0.
    raw=arguments['raw'];dt=arguments['dt'];b0=arguments['bias_center'];g0=arguments['gain_center']
    nominal=(raw-b0*dt)/(1+g0)
    for i in range(64):
        mask=np.array([bool(i&(1<<j)) for j in range(6)])
        b=np.where(mask[:3],arguments['bias_upper'],arguments['bias_lower'])
        g=np.where(mask[3:],arguments['gain_upper'],arguments['gain_lower']);book.tick()
        actual=(raw-b*dt)/(1+g)
        linear=-dt*(b-b0)/(1+g0)-(raw-b0*dt)*(g-g0)/(1+g0)**2
        error=float(np.linalg.norm(actual-nominal-linear));change=float(np.linalg.norm(actual-nominal))
        tol=tolerance(actual,linear,box['remainder_radius'])
        okay=error<=box['remainder_radius']+tol and change<=box['change_radius']+tol
        context['records'].append(dict(probe=i,bias=b,gain=g,actual=actual,linear_delta=linear,remainder_norm=error,
            change_norm=change,tolerance=tol,passed=okay));passed=passed and okay
        maximum_ratio=max(maximum_ratio,error/box['remainder_radius'] if box['remainder_radius'] else 0.)
    return dict(passed=passed,maximum_remainder_bound_ratio=maximum_ratio)


def packet_control(task,book,context):
    import numpy as np
    from lll.ilvis0_increment_remainders import packet_bound
    from lll.ilvis0_forward import interval_matrices
    theta=np.array([.003,-.002,.001] if task['center']=='small' else [2.4,-1.7,.9]);dv=np.array([.2,-.4,-.1])
    angle_width=.003 if task['width']=='narrow' else .8;force_width=.001 if task['width']=='narrow' else .1
    angle=dict(center=theta,change_radius=float(np.sqrt(3)*angle_width),remainder_radius=0.)
    force=dict(center=dv,change_radius=float(np.sqrt(3)*force_width),remainder_radius=0.)
    box=packet_bound(angle,force,kind=task['map_kind']);kind=('rotation','velocity','position').index(task['map_kind'])
    maps,derivatives=reference(theta,book,derivatives=True);nominal=maps[kind]@dv;passed=True;maximum_ratio=0.;max_native=0.
    context.update(inputs=dict(theta=theta,dv=dv,angle_width=angle_width,force_width=force_width),analytic_bound=box)
    for i in range(64):
        sign=np.array([1. if i&(1<<j) else -1. for j in range(6)])
        da=angle_width*sign[:3];df=force_width*sign[3:]
        actual_maps=reference(theta+da,book);actual=actual_maps[kind]@(dv+df)
        direction=np.tensordot(da,derivatives,axes=1)[kind]
        linear=direction@dv+maps[kind]@df
        book.tick();native=interval_matrices(theta+da)[kind]
        native_error=float(np.linalg.norm(native-actual_maps[kind],ord=2))
        error=float(np.linalg.norm(actual-nominal-linear));change=float(np.linalg.norm(actual-nominal))
        tol=tolerance(actual,linear,box['remainder_radius'])
        okay=error<=box['remainder_radius']+tol and change<=box['change_radius']+tol and native_error<=tol
        context['records'].append(dict(probe=i,angle_delta=da,velocity_delta=df,actual=actual,linear_delta=linear,
            remainder_norm=error,change_norm=change,repository_matrix_error=native_error,tolerance=tol,passed=okay))
        passed=passed and okay;max_native=max(max_native,native_error);maximum_ratio=max(maximum_ratio,error/box['remainder_radius'])
    return dict(passed=passed,maximum_remainder_bound_ratio=maximum_ratio,maximum_repository_matrix_error=max_native)


def history_control(task,book,context):
    import numpy as np
    from lll.ilvis0_increment_remainders import calibrated_box,PreintegrationBounds
    from lll.ilvis0_forward import Preintegration
    envelope=PreintegrationBounds();packets=[];nominal=Preintegration();r0=np.eye(3);v0=np.zeros(3);p0=np.zeros(3)
    for i in range(task['packets']):
        dt=.005*(1.+.1*math.sin(i));theta=np.array([3e-5*math.sin(.3*i),-4e-5*math.cos(.2*i),2e-5])
        dv=np.array([.0002*math.sin(.5*i),.0001*math.cos(.8*i),-9.81*dt])
        a=calibration_arguments('angle',task['width'],raw=theta,dt=dt);f=calibration_arguments('velocity',task['width'],raw=dv,dt=dt)
        angle=calibrated_box(**a);force=calibrated_box(**f);envelope=envelope.advance(angle,force,dt)
        maps,derivatives=reference(theta,book,derivatives=True);book.tick();nominal.step(theta,dv,dt)
        p0=p0+v0*dt+r0@(maps[2]@dv)*dt;v0=v0+r0@(maps[1]@dv);r0=r0@maps[0]
        packets.append(dict(dt=dt,theta=theta,dv=dv,angle_arguments=a,velocity_arguments=f,maps=maps,derivatives=derivatives))
    radii=envelope.report();passed=True;maximum_ratio=0.;maximum_native=0.
    native_nominal=nominal.result()
    nominal_error=max(float(np.linalg.norm(np.array(native_nominal['delta_rotation'])-r0,ord=2)),
        float(np.linalg.norm(np.array(native_nominal['rotated_specific_force_integral_mps'])-v0)),
        float(np.linalg.norm(np.array(native_nominal['specific_force_position_integral_m_by_clock']['header_elapsed'])-p0)))
    passed=nominal_error<=tolerance(p0,v0,0.)
    context.update(inputs=[{k:v for k,v in packet.items() if k not in ('maps','derivatives')} for packet in packets],analytic_bound=radii)
    for i in range(64):
        rng=np.random.default_rng(np.random.SeedSequence([SEED,task['packets'],int(task['width']=='broad'),i]))
        z=np.full(12,-1.) if i==0 else np.ones(12) if i==1 else np.zeros(12) if i==2 else rng.uniform(-1.,1.,12)
        r=np.eye(3);v=np.zeros(3);p=np.zeros(3);dr=np.zeros((3,3));dv_linear=np.zeros(3);dp=np.zeros(3)
        previous_r=np.eye(3);native=Preintegration()
        for packet in packets:
            dt=packet['dt'];a=packet['angle_arguments'];f=packet['velocity_arguments'];theta=packet['theta'];force=packet['dv']
            gb=z[:3]*a['bias_upper'];gg=z[3:6]*a['gain_upper'];ab=z[6:9]*f['bias_upper'];ag=z[9:]*f['gain_upper']
            observed_theta=(theta-gb*dt)/(1.+gg);observed_force=(force-ab*dt)/(1.+ag)
            observed_maps=reference(observed_theta,book);book.tick();native.step(observed_theta,observed_force,dt)
            p=p+v*dt+r@(observed_maps[2]@observed_force)*dt;v=v+r@(observed_maps[1]@observed_force);r=r@observed_maps[0]
            delta_theta=-gb*dt-theta*gg;delta_force=-ab*dt-force*ag
            maps=packet['maps'];direction=np.tensordot(delta_theta,packet['derivatives'],axes=1)
            dp=dp+dv_linear*dt+(dr@(maps[2]@force)+previous_r@(direction[2]@force+maps[2]@delta_force))*dt
            dv_linear=dv_linear+dr@(maps[1]@force)+previous_r@(direction[1]@force+maps[1]@delta_force)
            dr=dr@maps[0]+previous_r@direction[0];previous_r=previous_r@maps[0]
        comparisons=dict(rotation=(float(np.linalg.norm(r-r0,ord=2)),float(np.linalg.norm(r-r0-dr,ord=2))),
            velocity=(float(np.linalg.norm(v-v0)),float(np.linalg.norm(v-v0-dv_linear))),
            position=(float(np.linalg.norm(p-p0)),float(np.linalg.norm(p-p0-dp))))
        native_values=native.result();native_error=max(float(np.linalg.norm(np.array(native_values['delta_rotation'])-r,ord=2)),
            float(np.linalg.norm(np.array(native_values['rotated_specific_force_integral_mps'])-v)),
            float(np.linalg.norm(np.array(native_values['specific_force_position_integral_m_by_clock']['header_elapsed'])-p)))
        tol=tolerance(p,dp,radii['position_remainder']);okay=native_error<=tol
        for kind,(change,error) in comparisons.items():
            radius=radii[kind+'_remainder'];okay=okay and change<=radii[kind+'_change']+tol and error<=radius+tol
            if radius:maximum_ratio=max(maximum_ratio,error/radius)
        context['records'].append(dict(probe=i,normalized_parameters=z,actual_rotation=r,actual_velocity=v,actual_position=p,
            linear_rotation_delta=dr,linear_velocity_delta=dv_linear,linear_position_delta=dp,comparisons=comparisons,
            repository_value_error=native_error,tolerance=tol,passed=okay))
        passed=passed and okay;maximum_native=max(maximum_native,native_error)
    return dict(passed=passed,maximum_remainder_bound_ratio=maximum_ratio,maximum_repository_value_error=maximum_native,
        nominal_repository_error=nominal_error,final_global_bound=radii)


def evaluate(task,output=None,deadline=None):
    book=Calls(task['maximum_calls'],deadline);context=dict(task=task,records=[])
    try:
        if task['kind']=='calibration':result=calibration_control(task,book,context)
        elif task['kind']=='packet':result=packet_control(task,book,context)
        else:result=history_control(task,book,context)
        return dict(result,probe_count=len(context['records']),actual_calls=book.count,
            native_full_map_covered=False,floating_point_enclosure_verified=False,scientific_decision='abstain')
    finally:
        if output is not None:write(output,context)


def prepare():
    if (DATA/'manifest.json').exists():return verify()
    from lll import ilvis0_increment_remainders,ilvis0_forward
    sources={str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT)}
    sources.update('analysis/tests/'+name for name in ('ilvis0_increment_remainder_worker.py','ilvis0_channel_envelope_worker.py',
        'run_numerical.py','test_ilvis0_increment_remainders.py','test_ilvis0_increment_remainder_worker.py'))
    sources.add('docs/ilvis0-increment-remainders/PLAN.md');hashes={name:sha(ROOT/name) for name in sorted(sources)}
    for name in hashes:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(DATA/'manifest.json',dict(version='increment-global-bound-controls-v1',sources=hashes,environment=environment(),
        limits=LIMITS,plan=dict(tasks=TASKS,numerical_threads=4),seed=SEED,scientific_decision='abstain'))
    write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS));return verify()


def verify():
    manifest=load(DATA/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS or manifest['plan']['tasks']!=TASKS:
        raise ValueError('frozen environment or finite task scope changed')
    if load(DATA/'authorization.json')!=dict(manifest_sha256=sha(DATA/'manifest.json'),**LIMITS):raise ValueError('authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(DATA/'source-freeze'/name)!=digest:raise ValueError('frozen source changed: '+name)
    return manifest


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists():raise ValueError('charged increment-bound controls cannot restart')
        verify();started=time.time();deadline=time.monotonic()+LIMITS['maximum_wall_s'];rows=[];charged=0;terminal=None
        write(DATA/'start.json',dict(started_at=started,manifest_sha256=sha(DATA/'manifest.json')))
        try:
            for task in TASKS:
                check_time(deadline);identity=task['identity']
                if charged+task['maximum_calls']>LIMITS['maximum_software_evaluations']:raise ValueError('total software allowance exceeded')
                write(DATA/'charges'/(identity+'.json'),dict(task,reserved_software_evaluations=task['maximum_calls'],
                    manifest_sha256=sha(DATA/'manifest.json')));charged+=task['maximum_calls']
                write(DATA/'status.json',dict(state='running',identity=identity,total=30,numerical_threads=4,pid=os.getpid()),replace=True)
                generated='generated/'+identity+'.json.gz'
                try:result=evaluate(task,DATA/generated,deadline)
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
            charged_software_evaluations=charged,optimizer_starts=0,native_evaluations=0,scientific_decision='abstain'))
        write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        write(DATA/'status.json',dict(state=state,total=30,numerical_threads=0),replace=True)
    publish()


def publish():
    completion=load(DATA/'completion.json');summary=load(DATA/'summary.json');manifest=load(DATA/'manifest.json')
    if completion['manifest_sha256']!=sha(DATA/'manifest.json') or completion['summary_sha256']!=sha(DATA/'summary.json'):
        raise ValueError('completed controls changed')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json'];results=[]
    for row in summary['results']:
        if sha(DATA/row['artifact'])!=row['artifact_sha256']:raise ValueError('control result changed')
        value=load(DATA/row['artifact']);results.append(value)
        if sha(DATA/value['generated_artifact'])!=value['generated_sha256']:raise ValueError('generated probe evidence changed')
        names.extend([row['artifact'],value['generated_artifact'],'charges/'+row['identity']+'.json'])
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copytree(DATA/'source-freeze',PUBLIC/'source-freeze',dirs_exist_ok=True)
    lines=['# Global calibration and rotating-force bound controls','',
        f"**{sum(r['passed'] for r in results)}/30 identities passed** in {summary['elapsed_s']:.2f} seconds. "
        f"The study charged {summary['charged_software_evaluations']:,} software reference/value evaluations, with no original reads or native-engine fits.",'',
        '| Control | Passed | Maximum actual remainder / bound | Largest repository/reference difference |','|---|---:|---:|---:|']
    for kind in ('calibration','packet','history'):
        selected=[r for r in results if r['kind']==kind]
        ratios=[r.get('maximum_remainder_bound_ratio',0.) for r in selected]
        errors=[max(r.get('maximum_repository_matrix_error',0.),r.get('maximum_repository_value_error',0.)) for r in selected]
        lines.append(f"| {kind} | {sum(r['passed'] for r in selected)}/{len(selected)} | {max(ratios,default=0.):.6g} | {max(errors,default=0.):.3g} |")
    lines+=['','The bounds come from global analytic inequalities, not the largest sampled error. Probes test their implementation. '
        'Fixed-time body preintegration is covered; candidate-specific geographic dynamics, timing across packet boundaries '
        'and a whole-record floating-point enclosure remain outside this result. No archive prediction fit is authorized by these controls.',
        '', '[Proof outline and frozen limits](PLAN.md) · [Prediction interface](../ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n');names+=['README.md','PLAN.md']+['source-freeze/'+name for name in manifest['sources']]
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in names}),replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('prepare','run','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only))!=1:parser.error('choose one operation')
    from lll.compute_budget import environment as guard
    if any(os.environ.get(k)!=v for k,v in guard(threads=4).items()):parser.error('use run_numerical.py with four threads')
    if args.prepare:prepare();print('Frozen 30 component-bound identities; no execution.')
    elif args.run:run();print('Finite global increment-bound qualification complete; inspect saved results.')
    else:publish();print('Published saved component controls; no calculations.')


if __name__=='__main__':main()
