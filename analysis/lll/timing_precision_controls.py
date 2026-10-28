# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small independent timing/rounding controls; no fitting or observed inputs."""
import math
from pathlib import Path

IDENTITY='timing-precision-controls-20261026'
SCOPE='seven known-answer timing/rounding controls; zero nonlinear fits or observed reads'
STEPS=(1e-3,1e-4,1e-5)
QUALIFICATION='data/ilvis0-source-point-development/timing-precision-qualification-request.json'


def cases():
    return ('vertical-interior','vertical-boundary','vertical-bound-offset',
        'turning-slow','turning-fast','gyro-origin-zero','gyro-origin-one')


def turning_reference(force,omega,duration):
    """Differentiate the midpoint formula independently, not native Dual code."""
    a,w,d=force,omega,duration;c=math.cos(w*d/2);s=math.sin(w*d/2)
    return dict(left=[a*d*c-a*w*d*d*s/4,a*d*s+a*w*d*d*c/4],
        right=[a*d*c,a*d*s],continuous=[a*math.sin(w*d)/w,a*(1-math.cos(w*d))/w])


def fixture(identity):
    import numpy as np
    from lll.ilvis0_estimator import Bounds
    from lll.ilvis0_shape import TangentProblem
    from lll.airquantumgrav_training_controls import parameter_limits
    if identity not in cases():raise ValueError('one fixed control identity required')
    limits=parameter_limits();limits['time_offset']=1/128
    n,d,radius=8,1/8,2.**50;force=2.;omega=0.;origin=0.;velocity=0.;az=0.
    point=np.zeros(26);column='time_offset';direction=0
    if identity.startswith('vertical'):
        velocity=2.;az=3.;times=np.array([5/16,11/16])
        if identity!='vertical-interior':times=np.array([1/4,3/4])
        if identity=='vertical-bound-offset':point[25]=-1.;times+=limits['time_offset'];direction=1
    elif identity.startswith('turning'):
        n,d=2,1/4;omega=.8 if identity=='turning-slow' else 1.6
        times=np.array([d+limits['time_offset'],d+limits['time_offset']+1/16]);point[25]=-1.;direction=1
    else:
        n,d,radius=65,1/64,2.**30;force=10.;column='gyro_bias_z'
        origin=float(identity=='gyro-origin-one');times=np.array([.5,1.])
    theta=np.zeros((n,3));dv=np.zeros((n,3));dt=np.full(n,d)
    theta[:,2]=omega*d;dv[:,2]=(az-9.8)*d
    if not identity.startswith('vertical'):dv[:,0]=force*d
    gps=np.tile([0.,origin,1000.],(2,1))
    initial=dict(latitude_rad=0.,longitude_rad=origin,height_m=1000.,
        velocity_ned_mps=np.array([0.,0.,velocity]),attitude_body_to_ned=np.eye(3))
    p=TangentProblem(theta,dv,dt,times,gps,np.eye(6),initial,Bounds(limits),
        tangent_kernel=None,kernel=None,fit_earth_removal=False,clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=d,
        gravity_mps2=9.8,disc_radius_m=radius)
    return dict(problem=p,point=point,column=column,direction=direction,
        force=force,omega=omega,duration=d,az=az,velocity=velocity)


def calculate(identity,*,kernel,reserve):
    import numpy as np
    from lll.ilvis0_wide_tangent import evaluate as native
    f=fixture(identity);p=f['problem'];u=f['point'];col=p.bounds.active.index(f['column']);calls=0
    def evaluate(point):
        nonlocal calls
        reserve(native_calls=1,packet_visits=len(p.dt)*len(p.gps_times));calls+=1
        return native(p,point,'flat_still',kernel=kernel)
    out,delta,jac,boundaries=evaluate(u);j=jac.reshape(2,3,26)[:,:,col]
    differences=[]
    for h in STEPS:
        plus=u.copy();minus=u.copy();plus[col]+=h
        if f['direction']:
            minus[col]+=2*h;a=evaluate(plus)[1];b=evaluate(minus)[1]
            differences.append((-3*delta+4*a-b)/(2*h))
        else:
            minus[col]-=h;a=evaluate(plus)[1];b=evaluate(minus)[1]
            differences.append((a-b)/(2*h))
    result=dict(identity=identity,native_evaluations=calls,nonlinear_fit_starts=0,
        original_reads=0,protected_reads=0,boundaries=boundaries,steps=list(STEPS),
        derivative_column=f['column'],analytic=j.tolist(),finite_differences=[v.tolist() for v in differences],
        scientific_decision='abstain',whole_pipeline_qualified=False)
    if identity.startswith('vertical'):
        t=p.gps_times+u[25]*p.bounds.limits['time_offset']
        expected=-f['velocity']*t-.5*f['az']*t*t
        derivative=-(f['velocity']+f['az']*t)*p.bounds.limits['time_offset']
        result.update(position_error=float(np.max(abs(delta[:,2]-expected))),
            derivative_error=float(np.max(abs(j[:,2]-derivative))),
            finite_difference_error=[float(np.max(abs(v[:,2]-derivative))) for v in differences])
        result['passed']=(result['position_error']<1e-12 and result['derivative_error']<1e-13
            and max(result['finite_difference_error'])<1e-7)
    elif identity.startswith('turning'):
        reference=turning_reference(f['force'],f['omega'],f['duration'])
        scale=np.array([p.radius,p.radius*math.pi/2])/p.bounds.limits['time_offset']
        measured=j[0,:2]*scale;curves=[v[0,:2]*scale for v in differences]
        left=np.array(reference['left']);right=np.array(reference['right'])
        result.update(reference=reference,measured_left=measured.tolist(),
            measured_inward=[v.tolist() for v in curves],
            derivative_branch_gap=float(np.linalg.norm(left-right)),
            analytic_error_to_left=float(np.linalg.norm(measured-left)),
            finite_difference_error_to_right=[float(np.linalg.norm(v-right)) for v in curves])
        result['passed']=(result['analytic_error_to_left']<1e-10
            and max(result['finite_difference_error_to_right'])<1e-7)
    else:
        # At zero yaw/bias, midpoint impulses give sum((N-i-.5)*(i+.5)).
        # This independent polynomial is the large-radius limit; finite-radius
        # transport remains present in the native comparison.
        d=f['duration'];n=round(p.gps_times[-1]/d);metric=p.radius*math.pi/2
        reference=-f['force']*d**3*n*(2*n*n+1)/12*p.bounds.limits['gyro_bias_z']/metric
        analytic=float(j[-1,1]);relative=[float(abs(v[-1,1]-analytic)/abs(analytic)) for v in differences]
        result.update(reference=reference,analytic_relative_error=abs(analytic-reference)/abs(reference),
            finite_difference_relative_error=relative)
        result['passed']=result['analytic_relative_error']<1e-7
    return result


def load(directory,*,reserve_build):
    """Bind the existing wider equations through the shared charged build cache."""
    import ctypes
    import numpy as np
    from lll.ilvis0_wide_tangent import derive
    from lll.native_build import cpp
    from lll.studies.artifacts import digest
    original=Path(__file__).with_name('ilvis0_tangent.cpp').read_bytes()
    raw=derive(original,expected_sha256=digest(original))
    binary,meta=cpp(directory,raw,prefix='timing-control',expected_sha256=digest(raw),reserve_build=reserve_build)
    lib=ctypes.CDLL(str(binary));bits=lib.ilvis0_wide_bits()
    if bits<=53:raise ValueError('genuinely wider arithmetic required')
    array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');fn=lib.ilvis0_wide_tangent
    fn.argtypes=[ctypes.c_size_t,array,array,array,ctypes.c_size_t,array,array,array,array,array,array,
        ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,array,array,array,array,
        ctypes.POINTER(ctypes.c_int),ctypes.c_int,ctypes.c_double];fn.restype=ctypes.c_int
    def kernel(*args,observations,difference):
        return fn(*args[:-1],observations,difference,args[-1],0,0.)
    return kernel,dict(meta,internal_mantissa_bits=bits,original_source_sha256=digest(original))


def sources(root):
    from lll.studies.dependencies import source_closure
    source=source_closure(root,['analysis/lll/timing_precision_controls.py'])
    return sorted(set(source)|{'analysis/lll/ilvis0_tangent.cpp','analysis/tests/test_timing_precision_controls.py',
        'docs/TIMING_PRECISION_CONTROLS.md'})


def prepare(root):
    from lll.studies.runtime import Definition
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.journal import Journal
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    root=Path(root);directory=root/'data'/IDENTITY
    if directory.exists():raise ValueError('fresh separate control freeze required')
    source=sources(root)
    request,report=checked(root,QUALIFICATION,sources=source,environment=environment(),minimum_tests=13,
        required_tests=['test_reference_separates_packet_derivatives_from_continuous_motion',
            'test_native_control_matches_its_independent_reference[turning-fast]',
            'test_native_control_matches_its_independent_reference[gyro-origin-one]',
            'test_native_charge_rejection_prevents_execution','test_study_rejects_wrong_scope_before_building'])
    inputs=root/'data/ilvis0-source-point-development/timing-precision-input.json'
    atomic(inputs,encoded(dict(identities=list(cases()),steps=list(STEPS),native_evaluations_per_case=8,
        maximum_builds=1,nonlinear_fit_starts=0,original_reads=0,protected_reads=0)))
    request_path=inputs.with_name('timing-precision-qualified-request.json');atomic(request_path,request)
    report_path=inputs.with_name('timing-precision-qualified-tests.xml');atomic(report_path,report)
    tasks=[dict(identity=i,input_key='recipe',native_kind='tangent',payload=dict(identity=i),
        limits=dict(native_calls=8,packet_visits=8*len(fixture(i)['problem'].dt)*2,bound_calls=0,bound_steps=0)) for i in cases()]
    definition=dict(id=IDENTITY,scope=SCOPE,adapter='analysis/lll/timing_precision_controls.py',
        sources=source,inputs={'recipe':str(inputs.relative_to(root)),
            'qualification-request':str(request_path.relative_to(root)),
            'qualification-report':str(report_path.relative_to(root))},tasks=tasks,
        workers=1,threads=1,maximum_wall_s=600.)
    manifest=Definition.from_dict(definition,root).prepare(root)
    journal=Journal(directory/'builds.sqlite',freeze=digest((directory/'manifest.json').read_bytes()),
        limits={'compiler':dict(builds=1)});journal.start('compiler')
    return dict(path=str(directory.relative_to(root)),allocation=manifest['allocation'],tasks=len(tasks))


def evaluate(task,context):
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    if task['identity'] not in cases() or task['payload']!={'identity':task['identity']} or context.manifest['scope']!=SCOPE:
        raise ValueError('fixed known-answer control identity and scope required')
    journal=Journal(context.root/'builds.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={'compiler':dict(builds=1)})
    kernel,meta=load(context.root/'native',reserve_build=lambda:journal.reserve('compiler','builds'))
    context.save('native-binding.json',meta)
    result=calculate(task['identity'],kernel=kernel,reserve=context.charge)
    context.save('control.json',result);journal.verify()
    return result
