# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite complete-state prefix comparisons against sealed cold orchestration."""
from fractions import Fraction as F
import json
from pathlib import Path


def recipe():
    return dict(identities=14,supported_identities=12,unsupported_controls=2,packets=16,queries=3,proof_scopes=['physical','conditioned'],
        maximum_packet_steps=48,maximum_bound_seconds=120.,maximum_wall_s=600.,
        oracle_arithmetic_allowance_m=1e-5,force_change_mps2=.2,
        native_queries_per_identity=3,diagnostic_queries_per_identity=4,
        whole_native_prefix_qualified=False,original_reads=0,optimizer_starts=0)


def limits(scope,rejected=False):
    if scope not in recipe()['proof_scopes']:raise ValueError('fixed proof scope required')
    return dict(reference_setups=1,physical_proofs=int(scope=='physical'),conditional_proofs=int(scope=='conditioned'),
        lp_proposals=6*int(scope=='conditioned'),exact_supports=24*int(scope=='conditioned'),
        native_queries=0 if rejected else 3,cold_bound_queries=1 if rejected else 3,
        report_comparisons=1 if rejected else 3,design_comparisons=0 if rejected else 3,
        expected_rejections=2 if rejected else 0,
        preparation_packets=16,force_profile_packets=48,packet_steps=48,
        prefix_packet_steps=16,tail_packet_steps=48,cursor_copies=3,source_state_copies=9,source_query_checks=9)


def make_case(model,profile,scope,*,reserve,unsupported_source=False):
    import numpy as np
    from lll.ilvis0_source_prefix_controls import case as source_case
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    from lll.ilvis0_acceleration_projection import project
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    value,center,lo,hi=source_case(model,profile);config=value['configuration']
    config.update(initial_c=np.array([-.8,1.,10000.]),initial_v=np.array([150.,-20.,.1]),gravity=9.81,radius=6371000.)
    config['limits']=np.r_[[.01]*3,[2.]*3,[10.]*3,[2e-6]*3,[.01]*3,[.001]*6,[2.]*3,.01,1/1024,1.]
    if not unsupported_source:
        # Match the already supported gravity-centered native fixture. Retain
        # the more general source as an explicit baseline-rejection control.
        config['initial_r']=np.eye(3);center=np.full(27,.1);center[25]=-.125 if not profile else .125
        value['theta']=np.tile([1e-5,-2e-5,3e-6],(len(value['dt']),1))
        value['dv']=np.c_[1e-5*np.sin(np.arange(len(value['dt']))),
            2e-5*np.cos(np.arange(len(value['dt']))),-9.81*value['dt']]
    lo=np.full(27,-.2);hi=np.full(27,.5);lo[25]=-.3;hi[25]=.7
    reserve(reference_setups=1)
    ref=make_reference(config,value['theta'],value['dv'],value['dt'],lower=lo,upper=hi,center=center)
    if scope=='physical':
        reserve(physical_proofs=1);proof=DirectionalAcceleration(ref,lo,hi)
    elif scope=='conditioned':
        reserve(conditional_proofs=1);a=ref.acceleration;rows=[];shifts=[]
        for axis in range(3):
            row=list(a.jacobian[axis])+[0.]*24;row[39+axis]=float(a.caps[6+axis]);rows.append(row)
            shifts.append(sum((F(float(v))*F(float(c)) for v,c in zip(row,center)),F(0)))
        from lll.ilvis0_saved_prediction_audit import endpoint
        change=F(recipe()['force_change_mps2'])
        region=dict(parameter_count=51,center=center.tolist()+[0.]*24,
            lower=lo.tolist()+[-1.]*24,upper=hi.tolist()+[1.]*24,
            inequality_design=rows+[[-v for v in row] for row in rows],
            inequality_upper=[endpoint(v+change,True) for v in shifts]+[endpoint(-v+change,True) for v in shifts],
            binding=ref.binding,source_id=ref.parent.source_id,future_truth_used=False)
        bundle=dict(training=dict(region=region),reference=ref.report(),lower=region['lower'],upper=region['upper'])
        callback=lambda p,s:reserve(lp_proposals=p,exact_supports=s)
        certificate=project(**bundle,reserve=callback)
        proof=ConditionedAcceleration(bundle,certificate,reserve=lambda s:reserve(exact_supports=s))
    else:raise ValueError('fixed proof scope required')
    tags=[0.]
    for duration in value['dt']:tags.append(tags[-1]+float(duration))
    clock=float(config['limits'][25]*center[25]);knot=tags[8]-clock
    times=[knot,float(np.nextafter(knot,np.inf)),tags[-1]-.004-clock]
    return dict(configuration=config,theta=value['theta'],dv=value['dv'],dt=value['dt'],
        center=center,lower=lo,upper=hi,reference=ref,conditioning=proof,times=times)


def check(model,profile,scope,*,original,prefix_kernels,cold_kernels,tangent,reserve,charge,save):
    import ctypes
    import time
    import numpy as np
    from lll.ilvis0_native_prefix import enclose_many
    from lll.ilvis0_packet_boundary_flags import validate
    value=make_case(model,profile,scope,reserve=reserve);config=value['configuration']
    theta,dv,dt=(np.ascontiguousarray(value[k],float) for k in ('theta','dv','dt'))
    n=len(dt);r=recipe();times=value['times'];ref=value['reference'];started=time.monotonic()
    common=dict(lower=value['lower'],upper=value['upper'],reference=ref,conditioning=value['conditioning'],
        maximum_seconds=r['maximum_bound_seconds'])
    expected=[];native=[];jacobians=[];scale=np.array([6371000.,6371000.,1.])
    for i,t in enumerate(times):
        reserve(cold_bound_queries=1);charge(bound_calls=1,bound_steps=9*n)
        expected.append(original.enclose(config,theta,dv,dt,time=t,**common,**cold_kernels))
        save(f'cold-{i:02d}.json',expected[-1].report())
        reserve(native_queries=1);charge(native_calls=1,packet_visits=n)
        out=np.empty((1,3));jac=np.empty((3,27));flag=ctypes.c_int()
        code=tangent(n,theta,dv,dt,1,np.array([t]),config['initial_c'],config['initial_v'],config['initial_r'],
            config['limits'],np.ascontiguousarray(value['center'],float),model,int(profile),
            config['gravity'],config['radius'],out,jac,ctypes.byref(flag))
        classification=validate(status=int(code),counter=flag.value,dt=dt,time_s=t,
            clock_offset_s=float(config['limits'][25]*value['center'][25]))
        if code:raise ValueError('independent native point query failed')
        native.append(out[0].copy());jacobians.append(jac.copy())
        save(f'native-{i:02d}.json',dict(time_s=t,point=value['center'].tolist(),prediction=out[0].tolist(),
            jacobian=jac.tolist(),status=int(code),warning=flag.value,boundary=classification))
    charge(bound_calls=1,bound_steps=9*r['maximum_packet_steps'])
    result=enclose_many(config,theta,dv,dt,times=times,prefix_kernels=prefix_kernels,
        maximum_packet_steps=r['maximum_packet_steps'],reserve=reserve,**common)
    errors=[]
    for i,(actual,old,jac,point) in enumerate(zip(result['bounds'],expected,jacobians,native,strict=True)):
        save(f'batched-{i:02d}.json',actual.report());reserve(report_comparisons=1)
        if actual.report()!=old.report():raise ValueError('complete batched report differs from original cold calculation')
        reserve(design_comparisons=1);a=actual.design(jac,ref);b=old.design(jac,ref)
        if a.shape!=(3,51) or not np.array_equal(a,b):raise ValueError('physical/shared coefficient design changed')
        error=abs((actual.center-point)*scale);errors.append(error.tolist())
        if np.max(error)>r['oracle_arithmetic_allowance_m']:raise ValueError('center differs from independent native oracle')
        save(f'design-{i:02d}.json',dict(matrix=a.tolist(),native_center_error_m=error.tolist()))
    save('batch-work.json',dict(work=result['work'],binding=result['binding']))
    return dict(passed=True,model=model,profile=profile,scope=scope,queries=3,
        complete_reports_equal=True,design_columns_checked=51,physical_parameter_count=27,shared_coordinates=24,
        maximum_native_center_error_m=float(np.max(errors)),oracle_arithmetic_allowance_m=r['oracle_arithmetic_allowance_m'],
        work=result['work'],elapsed_s=time.monotonic()-started,
        native_evaluations=3,bound_evaluations=4,original_reads=0,optimizer_starts=0,
        whole_native_prefix_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def check_rejection(scope,*,original,prefix_kernels,cold_kernels,reserve,charge,save):
    from lll.ilvis0_native_prefix import enclose_many
    value=make_case(0,False,scope,reserve=reserve,unsupported_source=True)
    args=[value[k] for k in ('configuration','theta','dv','dt')];n=len(value['dt']);r=recipe()
    common=dict(lower=value['lower'],upper=value['upper'],reference=value['reference'],
        conditioning=value['conditioning'],maximum_seconds=r['maximum_bound_seconds'])
    expected='initial source nonlinear cap is insufficient; no expansion permitted';reasons=[]
    reserve(cold_bound_queries=1);charge(bound_calls=1,bound_steps=9*n)
    try:original.enclose(*args,time=value['times'][0],**common,**cold_kernels)
    except ValueError as error:
        if str(error)!=expected:raise
        reserve(expected_rejections=1);reasons.append(str(error))
    else:raise ValueError('original unsupported fixture unexpectedly accepted')
    charge(bound_calls=1,bound_steps=9*r['maximum_packet_steps'])
    try:enclose_many(*args,times=value['times'],prefix_kernels=prefix_kernels,
        maximum_packet_steps=r['maximum_packet_steps'],reserve=reserve,**common)
    except ValueError as error:
        if str(error)!=expected:raise
        reserve(expected_rejections=1);reasons.append(str(error))
    else:raise ValueError('batched path silently promoted unsupported source')
    reserve(report_comparisons=1);save('rejection-checks.json',dict(reasons=reasons))
    return dict(passed=True,model=0,profile=False,scope=scope,baseline_unsupported=True,
        expected_rejections=2,rejection_reason=expected,native_evaluations=0,bound_evaluations=2,
        original_reads=0,optimizer_starts=0,whole_native_prefix_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def prepare(root,identity='ilvis0-native-prefix-controls-v2-20261022'):
    import subprocess
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import safe_path,atomic,encoded
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh complete-native-prefix freeze required')
    source='analysis/lll/ilvis0_remainder_native.py'
    prior=ClosedStudy(root,'data/ilvis0-long-remainder-feasibility-20261022')
    try:
        cold_sha=prior.manifest['sources'][source];cold=prior.read('source-freeze/'+source,cold_sha,raw=True)
        parent_manifest=prior.completion['manifest_sha256']
    finally:prior.close()
    base.mkdir(parents=True);atomic(base/'cold.py',cold)
    settings=dict(recipe(),cold_sha256=cold_sha,parent_manifest_sha256=parent_manifest,
        compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0])
    atomic(base/'recipe.json',encoded(settings));adapter='analysis/lll/ilvis0_native_prefix_controls.py'
    sources=source_closure(root,[adapter,'docs/ilvis0-native-prefix-controls/PLAN.md',
        'docs/ilvis0-prefix-reuse/NATIVE_PLAN.md','analysis/tests/test_ilvis0_native_prefix.py',
        'analysis/tests/test_ilvis0_native_prefix_controls.py','analysis/tests/native_prefix_reference.py',
        'analysis/tests/ilvis0_native_prefix_reference.json','analysis/tests/test_study_dependencies.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_source_prefix_reference.cpp','analysis/lll/ilvis0_source_prefix_intervals.cpp'])
    tasks=[]
    for model in range(3):
        for profile in (False,True):
            for scope in recipe()['proof_scopes']:
                tasks.append(dict(identity=f'native-prefix-{model}-{int(profile)}-{scope}',input_key='recipe',
                    payload=dict(model=model,profile=profile,scope=scope,limits=limits(scope)),
                    limits=dict(native_calls=3,packet_visits=48,bound_calls=4,bound_steps=864)))
    for scope in recipe()['proof_scopes']:
        tasks.append(dict(identity=f'unsupported-initial-{scope}',input_key='recipe',
            payload=dict(model=0,profile=False,scope=scope,rejected=True,limits=limits(scope,True)),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=2,bound_steps=576)))
    definition=dict(id=identity,adapter=adapter,sources=sources,
        inputs={'recipe':(base/'recipe.json').relative_to(root).as_posix(),'cold':(base/'cold.py').relative_to(root).as_posix()},
        tasks=tasks,workers=1,threads=1,maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,identities=14,sources=len(m['sources']),allocation=m['allocation'],limits=m['limits'])


def evaluate(task,context):
    from lll.studies.closed import load_python_reference
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_source_prefix import load_kernels
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel as interval_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as point_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_batched_transport import configure_backend
    settings=json.loads(context.input_path().read_bytes());spec=task['payload']
    rejected=bool(spec.get('rejected',False))
    if any(settings.get(k)!=v for k,v in recipe().items()) or spec['limits']!=limits(spec['scope'],rejected):
        raise ValueError('fixed complete-prefix recipe and scope required')
    raw=context.input_path('cold').read_bytes();sha=settings['cold_sha256']
    original=load_python_reference(raw,name='lll._sealed_prefix_control_'+sha[:16],sha256=sha)
    path=context.directory/'allowance.sqlite';journal=Journal(path,
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:limits(spec['scope'],rejected)})
    journal.start(task['identity'])
    def reserve(**values):
        _check_continue(context.root,context.manifest)
        for key,v in values.items():journal.reserve(task['identity'],key,v)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';source=context.root/'source-freeze/analysis/lll'
    try:
        backend=configure_backend(directory,source_directory=source)
        kernels,meta=load_kernels(directory,source_directory=source);cold={}
        for key,loader in (('source_kernel',load_stream),('derivative_kernel',interval_kernel),('point_kernel',point_kernel)):
            k,m=loader(directory,source_directory=source);cold[key]=k;meta[key]=m
        tangent,tangent_meta=load_tangent(directory)
        meta['backend']=backend
        for m in meta.values():
            if m['compiler']!=settings['compiler'] or any(context.manifest['sources'].get('analysis/lll/'+name)!=sha for name,sha in m['sources'].items()):
                raise ValueError('compiled native source differs from freeze')
        if (tangent_meta['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
                or tangent_meta['compiler']!=settings['compiler']):
            raise ValueError('point oracle differs from freeze')
        context.save('compilation.json',dict(components=meta,tangent=tangent_meta))
        if rejected:
            result=check_rejection(spec['scope'],original=original,prefix_kernels=kernels,cold_kernels=cold,
                reserve=reserve,charge=context.charge,save=context.save)
        else:
            result=check(spec['model'],spec['profile'],spec['scope'],original=original,prefix_kernels=kernels,
                cold_kernels=cold,tangent=tangent,reserve=reserve,charge=context.charge,save=context.save)
        counts={k:journal.count(task['identity'],k) for k in limits(spec['scope'],rejected)}
        context.save('accounting.json',counts)
        result=dict(result,identity=task['identity'],charged_auxiliary=counts);context.save('native-prefix-checks.json',result)
        return result
    finally:journal.verify();context.note_file(path)


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[]
    try:
        settings=study.input('recipe')
        if any(settings.get(k)!=v for k,v in recipe().items()):raise ValueError('fixed complete-prefix recipe required')
        for identity in study.tasks:
            if identity not in study.rows:continue
            value=study.envelope(identity)['result']
            if value.get('passed'):
                if value!=study.artifact(identity,'native-prefix-checks.json'):raise ValueError('saved complete-prefix result differs')
                if value.get('baseline_unsupported'):study.artifact(identity,'rejection-checks.json')
                else:
                    for i in range(3):
                        for stem in ('cold','batched','native','design'):study.artifact(identity,f'{stem}-{i:02d}.json')
                    study.artifact(identity,'batch-work.json')
                study.artifact(identity,'accounting.json')
            rows.append(value)
        actual={(r.get('model'),r.get('profile'),r.get('scope'),bool(r.get('baseline_unsupported'))) for r in rows if r.get('passed')}
        expected={(m,p,s,False) for m in range(3) for p in (False,True) for s in recipe()['proof_scopes']}
        expected.update((0,False,s,True) for s in recipe()['proof_scopes'])
        return dict(rows=rows,complete=len(rows)==14 and actual==expected,numerical_work=0,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            whole_native_prefix_qualified=False)
    finally:study.close()


def render(report):
    text=['# Complete native-prefix software comparison','',
        'This checks the complete cached state: geographic motion, relative attitudes, accumulated '
        'force, common clock, source streams and calibration proof. The reference is the sealed '
        'original cold orchestration, with all dependencies fixed by the new study. Inputs are '
        'generated software cases, not aircraft recordings.',
        '', '| Candidate | Processing | Proof | Complete reports equal | Native center error (m) | Prefix + tail steps |',
        '|---|---|---|---|---:|---:|']
    labels=['Globe + field','Globe, zero field','Stationary disc']
    for r in report['rows']:
        if not r.get('passed'):
            text.append('| — | — | — | Failed ('+r.get('error_type','unsupported')+') | — | — |');continue
        if r.get('baseline_unsupported'):
            text.append('| Globe + field | Zero removal | '+r['scope']+' | Unsupported source rejected by both paths | — | 0 |');continue
        steps=r['work']['prefix_packet_steps']+r['work']['tail_packet_steps']
        text.append('| '+' | '.join([labels[r['model']],'Profiled removal' if r['profile'] else 'Zero removal',r['scope'],
            'Yes',f"{r['maximum_native_center_error_m']:.3g}",str(steps)])+' |')
    if not report['complete']:
        text+=['', '**Qualification did not pass.** The sealed outcomes retain their failure reasons '
            'and charged identities. They are not supported native-prefix results.']
    text+=['', 'Each supported case compares three complete reports and all 51 design columns: 27 physical '
        'parameters plus 24 shared source coordinates. An independent native point query checks '
        'each center at the predeclared ten-micrometre software allowance. Both physical-domain '
        'and training-conditioned proof paths are covered. The latter uses a declared generated '
        'acceleration constraint; it is not an observation from a flight.',
        '', 'Two additional controls retain a broader initial-source fixture that the original engine '
        'cannot certify. Both paths must reject it with the same insufficient-cap error; it does not '
        'become a supported case or disappear from the report.',
        '', 'The common-clock force certificate is still computed by the original cold routine '
        'for each query. Cached source work must preserve packet positions, allowances and exact '
        'boundary handling. Local tests separately cover zero time and adjacent exact boundaries.',
        '', '**Long-history performance and full prediction uncertainty remain unqualified.** '
        'Passing these short controls is not an aircraft result or a reason to change the '
        '53-stretch findings. A separately bounded long comparison must precede complete-cadence use.',
        '', '[Frozen scope](PLAN.md) · [Implementation plan](../ilvis0-prefix-reuse/NATIVE_PLAN.md) · '
        '[Prediction gates](../ilvis0-joint-projection-controls/NEXT_PLAN.md)']
    return '\n'.join(text)+'\n'


def publish(root,prefix,output='docs/ilvis0-native-prefix-controls'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/ilvis0-native-prefix-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
