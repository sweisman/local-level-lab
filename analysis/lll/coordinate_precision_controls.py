# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent coordinate-origin controls and their bounded shared lifecycle."""
import math
import json
from pathlib import Path

MODES=('baseline','previous','compensated')
STEPS=(1e-3,1e-4,1e-5)
IDENTITY='coordinate-precision-controls-20261026'
SCOPE='six independent coordinate-origin fixtures under three arithmetic settings; no fits or observed inputs'
QUALIFICATION='data/ilvis0-source-point-development/coordinate-precision-qualification-request.json'


def cases():return tuple(axis+'-'+origin for axis in ('north','east','height') for origin in ('small','large'))


def fixture(identity):
    import numpy as np
    from lll.ilvis0_estimator import Bounds
    from lll.ilvis0_shape import TangentProblem
    from lll.airquantumgrav_training_controls import parameter_limits
    if identity not in cases():raise ValueError('fixed coordinate-axis/origin identity required')
    axis,origin=identity.split('-');n=65;d=1/64;g=9.8;force=10.;radius=2.**30
    rotation=np.eye(3);body_force=np.array([force,0.,-g]);coordinates=np.zeros(3)
    if axis=='north':
        rotation=np.array([[0.,1.,0.],[0.,0.,1.],[1.,0.,0.]])
        body_force=np.array([-g,0.,0.]);index=0;coefficient=g/radius
        if origin=='large':coordinates[0]=1.
    elif axis=='east':
        index=1;coefficient=-force/(radius*math.pi/2)
        if origin=='large':coordinates[1]=1.
    else:
        rotation=np.array([[1.,0.,0.],[0.,0.,-1.],[0.,1.,0.]])
        body_force=np.array([force,-g,0.]);index=2;coefficient=force
        if origin=='large':coordinates[2]=1e6
    times=np.array([.5,1.]);limits=parameter_limits();limits['time_offset']=1/128
    initial=dict(latitude_rad=coordinates[0],longitude_rad=coordinates[1],height_m=coordinates[2],
        velocity_ned_mps=np.zeros(3),attitude_body_to_ned=rotation)
    p=TangentProblem(np.zeros((n,3)),np.tile(body_force*d,(n,1)),np.full(n,d),times,
        np.tile(coordinates,(2,1)),np.eye(6),initial,Bounds(limits),tangent_kernel=None,kernel=None,
        fit_earth_removal=False,clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=d,
        gravity_mps2=g,disc_radius_m=radius)
    # Differentiate the discrete midpoint impulse sum, independently of Dual
    # code or a truth generator. North/height are exact in this flat fixture;
    # east retains the separately bounded finite-radius correction.
    reference=np.array([coefficient*d**3*round(t/d)*(2*round(t/d)**2+1)/12
        *limits['gyro_bias_z'] for t in times])
    return dict(problem=p,point=np.zeros(26),axis=index,reference=reference)


def calculate(identity,*,kernel,reserve):
    import numpy as np
    from lll.ilvis0_wide_tangent import evaluate
    f=fixture(identity);p=f['problem'];u=f['point'];col=p.bounds.active.index('gyro_bias_z');calls=0
    def query(v):
        nonlocal calls
        reserve(native_calls=1,packet_visits=len(p.dt)*len(p.gps_times));calls+=1
        return evaluate(p,v,'flat_still',kernel=kernel)
    out,delta,jac,b=query(u);axis=f['axis'];reference=f['reference']
    analytic=jac.reshape(2,3,26)[:,axis,col];curves=[]
    for h in STEPS:
        plus=u.copy();minus=u.copy();plus[col]+=h;minus[col]-=h
        a=query(plus)[1][:,axis];z=query(minus)[1][:,axis]
        curves.append((a-z)/(2*h))
    an=float(np.max(abs((analytic-reference)/reference)))
    errors=[float(np.max(abs((v-reference)/reference))) for v in curves]
    return dict(identity=identity,passed=True,execution_complete=True,precision_passed=an<1e-7 and max(errors)<1e-7,
        analytic_relative_error=an,difference_relative_errors=errors,reference=reference.tolist(),
        analytic=analytic.tolist(),differences=[v.tolist() for v in curves],steps=list(STEPS),
        evaluations=calls,columns=jac.shape[1],native_boundaries=b,nonlinear_fit_starts=0,
        original_reads=0,protected_reads=0,scientific_decision='abstain',whole_pipeline_qualified=False)


def recipe():return dict(cases=list(cases()),modes=list(MODES),steps=list(STEPS),
    relative_comparison_tolerance=1e-7,packets=65,queries=2,maximum_builds=3,
    maximum_evaluations_per_task=8,nonlinear_fit_starts=0,original_reads=0,protected_reads=0)


def tasks():
    return [dict(identity=case+'-'+mode,input_key='recipe',native_kind='tangent',
        payload=dict(case=case,mode=mode),limits=dict(native_calls=8,packet_visits=1040,bound_calls=0,bound_steps=0))
        for case in cases() for mode in MODES]


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/coordinate_precision_controls.py',
        'analysis/tests/test_coordinate_precision.py','analysis/tests/test_coordinate_precision_controls.py',
        'analysis/tests/test_ilvis0_timing_arithmetic.py','analysis/tests/test_ilvis0_wide_tangent.py',
        'docs/COORDINATE_PRECISION_PLAN.md'])


def prepare(root):
    from lll.studies.runtime import Definition
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.qualification import checked
    from lll.studies.journal import Journal
    from lll.airquantumgrav_inventory import environment
    root=Path(root).resolve();directory=root/'data'/IDENTITY
    prep=root/'data/ilvis0-source-point-development'/f'{IDENTITY}-inputs'
    if directory.exists() or prep.exists():raise ValueError('fresh finite control freeze required')
    names=sources(root);env=environment()
    request,report=checked(root,QUALIFICATION,sources=names,environment=env,minimum_tests=46,
        required_tests=['test_compensated_derivation_requires_exact_supported_source',
            'test_compensated_axis_matches_independent_midpoint_polynomial[large-north]',
            'test_denied_evaluation_charge_prevents_native_execution',
            'test_matrix_has_six_cases_three_settings_and_original_caps',
            'test_summary_does_not_relabel_a_failed_precision_comparison'])
    prep.mkdir(parents=True);inputs={}
    for i,(name,raw) in enumerate({'recipe':encoded(recipe()),'environment':encoded(env),
            'qualification-request':request,'qualification-report':report}.items()):
        path=prep/f'input-{i:03d}';atomic(path,raw);inputs[name]=str(path.relative_to(root))
    definition=dict(id=IDENTITY,scope=SCOPE,adapter='analysis/lll/coordinate_precision_controls.py',
        sources=names,inputs=inputs,tasks=tasks(),workers=1,threads=1,maximum_wall_s=600.)
    atomic(prep/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    j=Journal(directory/'builds.sqlite',freeze=digest((directory/'manifest.json').read_bytes()),
        limits={'compiler':dict(builds=3)});j.start('compiler')
    return dict(path='data/'+IDENTITY,allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    if context.manifest['scope']!=SCOPE:raise ValueError('exact coordinate-control scope required')
    from lll.airquantumgrav_inventory import environment
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll.ilvis0_timing_arithmetic import load as previous
    from lll.ilvis0_coordinate_precision import load
    expected={t['identity']:t for t in tasks()}
    if ({k:v for k,v in task.items() if k not in ('index','shard')}!=expected.get(task['identity'])
            or json.loads(context.input_path('recipe').read_bytes())!=recipe()
            or json.loads(context.input_path('environment').read_bytes())!=environment()):
        raise ValueError('fixed control matrix, recipe and environment required')
    journal=Journal(context.root/'builds.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={'compiler':dict(builds=3)})
    charge=lambda:journal.reserve('compiler','builds');directory=context.root/'native'
    a,am=previous(directory,right_at_lower=False,relative_longitude=False,reserve_build=charge)
    b,bm=previous(directory,right_at_lower=True,relative_longitude=True,reserve_build=charge)
    c,cm=load(directory,reserve_build=charge)
    context.save('kernel-bindings.json',dict(baseline=am,previous=bm,compensated=cm))
    context.save_bytes('build-journal.sqlite',journal.path.read_bytes())
    case,mode=task['payload']['case'],task['payload']['mode']
    result=calculate(case,kernel=dict(baseline=a,previous=b,compensated=c)[mode],reserve=context.charge)
    result.update(identity=task['identity'],case=case,mode=mode);context.save('control.json',result)
    journal.verify();return result


def summarize(value):
    return dict(identity=value['identity'],mode=value['mode'],precision_passed=value['precision_passed'],
        analytic_relative_error=value['analytic_relative_error'],
        maximum_difference_relative_error=max(value['difference_relative_errors']),
        evaluations=value['evaluations'],columns=value['columns'])


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    from lll.studies.journal import inspect_snapshot
    s=ClosedStudy(root,prefix)
    try:
        if s.manifest['scope']!=SCOPE or set(s.tasks)!={t['identity'] for t in tasks()}:
            raise ValueError('exact independent coordinate-control matrix required')
        rows=[];failures=[];builds=[]
        for identity in s.tasks:
            if identity not in s.rows:failures.append(dict(identity=identity,reason='unexecuted'));continue
            envelope=s.envelope(identity)
            if 'artifacts/'+identity+'/control.json' not in envelope['artifacts']:
                failures.append(dict(identity=identity,reason=envelope['result'].get('error','control incomplete')));continue
            d=s.artifact(identity,'control.json')
            if (d['identity']!=identity or d['evaluations']!=s.rows[identity]['charged']['native_calls']
                    or d['columns']!=26 or any(d[k]!=0 for k in ('original_reads','protected_reads','nonlinear_fit_starts'))
                    or d['whole_pipeline_qualified']):raise ValueError('control scope or accounting changed')
            build=inspect_snapshot(s.artifact(identity,'build-journal.sqlite',raw=True),s.completion['manifest_sha256'])
            if build['starts']!=1 or build['sweeps']!=3:raise ValueError('three charged compiler builds required')
            builds.append(build['sweeps']);rows.append(summarize(d))
        candidate=[r for r in rows if r['mode']=='compensated']
        return dict(manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            rows=rows,failures=failures,complete=len(rows),selected=18,
            candidate_qualified=len(candidate)==6 and all(r['precision_passed'] for r in candidate),
            evaluations=sum(r['evaluations'] for r in rows),compiler_builds=max(builds,default=0),
            charged=s.summary['charged'],elapsed_s=s.summary['elapsed_s'],nonlinear_fit_starts=0,
            original_reads=0,protected_reads=0,confidence_calibrated=False,scientific_decision='abstain')
    finally:s.close()


def render(report):
    lines=['# Small coordinate changes survive compensated accumulation','',
        f"Completed {report['complete']}/18 coordinate controls; compensation qualified: {report['candidate_qualified']}.",
        'These are arithmetic controls with known answers, not flight measurements.','',
        '| Control | Arithmetic | Precision check | Largest relative difference error |','|---|---|---|---:|']
    for r in report['rows']:
        lines.append(f"| {r['identity']} | {r['mode']} | {r['precision_passed']} | {r['maximum_difference_relative_error']:.6g} |")
    lines+=['','All 26 nuisance columns remain. A failed precision comparison stays failed.',
        'The report does not qualify a solver, a saved-data fit or an uncertainty threshold.','',
        '[Results CSV](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/'+IDENTITY,output='docs/coordinate-precision-controls'):
    import csv
    import io
    from lll.ilvis0_control_publication import publish as package,check
    from lll.studies.artifacts import atomic,encoded,digest
    root=Path(root).resolve();public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('immutable publication already exists')
    report=inspect(root,prefix);package(root/prefix,public,render(report),plan='docs/COORDINATE_PRECISION_PLAN.md')
    text=io.StringIO(newline='');fields=list(report['rows'][0]) if report['rows'] else ['identity']
    writer=csv.DictWriter(text,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(report['rows'])
    extras={'results.csv':text.getvalue().encode(),'artifacts/publication/verified-report.json':encoded(report)}
    if (public/'INTERPRETATION.md').is_file():extras['INTERPRETATION.md']=(public/'INTERPRETATION.md').read_bytes()
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in extras.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(root/prefix,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('published control replay differs')
    return dict(path=output,complete=report['complete'],candidate_qualified=report['candidate_qualified'],native_calls=0)
