# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded, saved-only calibration diagnosis through the shared study engine."""
import json
from collections import Counter,defaultdict

from lll.studies.artifacts import digest,encoded,atomic,safe_path

PARENT='docs/structured-noisy-training'
SCOPE='saved generated calibration and stopping diagnosis; no fits, original/protected reads or noise draws'
SOURCES=('analysis/lll/airquantumgrav_observation_truth.py',
    'analysis/lll/ilvis0_solver_refinement.py','analysis/lll/ilvis0_solver_position.py')


def recipe():
    return dict(version='structured-noisy-saved-diagnosis-v1',maximum_saved_fits=24,
        maximum_parameter_rows=648,maximum_bundle_bytes=32*1024**2,maximum_wall_s=300.)


def tasks():
    return [dict(identity='saved-calibration-and-stopping',input_key='bundle',payload={},native_kind='value',
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))]


def collect(root):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,PARENT)
    try:
        bundle=dict(manifest=study.read('manifest.json',raw=True).decode(),
            summary=study.read('summary.json',raw=True).decode(),completion=study.completion,
            receipt=study.read('evidence-receipt.json'),recipe=study.input('recipe'),
            parent_report=study.read('artifacts/publication/verified-report.json'),
            sources={n:study.read('source-freeze/'+n,study.manifest['sources'][n],raw=True).decode() for n in SOURCES},
            fits={identity:dict(fit=study.artifact(identity,'fit.json'),
                training_error=study.artifact(identity,'training-error-operator.json')) for identity in study.tasks})
    finally:study.close()
    if len(encoded(bundle))>recipe()['maximum_bundle_bytes']:raise ValueError('saved bundle exceeds its byte allowance')
    calculate(bundle)
    return bundle


def calculate(bundle):
    from lll.calibration_diagnostics import fit_parameters,frozen_reference,summarize,column_cosines
    from lll.stopping_diagnostics import frozen_policy,components
    try:
        manifest=json.loads(bundle['manifest']);summary=json.loads(bundle['summary'])
        completion=bundle['completion'];report=bundle['parent_report'];receipt=bundle['receipt']['artifacts'];r=bundle['recipe']
        if (digest(bundle['manifest'].encode())!=completion['manifest_sha256']
                or digest(bundle['summary'].encode())!=completion['summary_sha256']
                or receipt['manifest.json']!=completion['manifest_sha256']
                or receipt['summary.json']!=completion['summary_sha256']
                or receipt['artifacts/publication/verified-report.json']!=digest(encoded(report))
                or manifest['inputs']['recipe']['sha256']!=digest(encoded(r))
                or report['verified'] is not True or completion['state'] not in ('complete','terminal')
                or report['total']!=24 or report['complete']!=24 or r['duration_s']!=120.
                or r['queries']!=119 or len(manifest['tasks'])!=24 or len(bundle['fits'])!=24):
            raise ValueError('complete hash-bound two-minute parent required')
        for name in SOURCES:
            if digest(bundle['sources'][name].encode())!=manifest['sources'][name]:
                raise ValueError('frozen diagnostic reference source differs')
        policy=frozen_policy(*(bundle['sources'][n] for n in SOURCES[1:]));rows=[]
        parent_rows={v['identity']:v for v in report['rows']}
        tasks_by_id={v['identity']:v for v in manifest['tasks']}
        if set(bundle['fits'])!=set(tasks_by_id) or len(parent_rows)!=24:raise ValueError('exact parent identities required')
        for identity,task in tasks_by_id.items():
            payload=task['payload'];saved=bundle['fits'][identity];fit=saved['fit'];error=saved['training_error']
            for name,value in (('fit.json',fit),('training-error-operator.json',error)):
                if digest(encoded(value))!=receipt['artifacts/'+identity+'/'+name]:
                    raise ValueError('saved fit or error descriptor differs from its receipt')
            if fit['converged']!=parent_rows[identity]['converged']:raise ValueError('original stopping labels differ')
            ref=frozen_reference(bundle['sources'][SOURCES[0]],-1 if payload['profile'] else 1)
            parameters=fit_parameters(fit,r['limits'],profile=payload['profile'],reference=ref)
            linear=fit['local_linearization']
            if linear['active_parameters']!=fit['active_parameters']:raise ValueError('saved Jacobian parameter order differs')
            cosines=column_cosines(linear,pairs=[('accel_bias_z','gravity_delta'),
                ('accel_gain_z','gravity_delta'),('gyro_bias_z','gyro_gain_z')])
            rows.append(dict(identity=identity,**payload,converged=fit['converged'],parameters=parameters,
                column_cosines=cosines,
                evaluations=fit['evaluations'],maximum_evaluations=fit['maximum_evaluations'],
                stopping=components(fit,policy),cost=fit['residual_sum_squares'],
                gravity_base_mps2=error['gravity_mps2'],normalized_parameters=fit['normalized_parameters']))
        seed={v['seed'] for v in r['noise_by_law'].values()}
        if len(seed)!=1:raise ValueError('matched single configured noise seed required')
    except (KeyError,TypeError,json.JSONDecodeError) as error:
        raise ValueError('complete hash-bound saved diagnosis inputs required') from error
    count=sum(len(v['parameters']) for v in rows)
    if count>recipe()['maximum_parameter_rows']:raise ValueError('saved parameter allowance exceeded')
    paired=defaultdict(list)
    for row in rows:paired[row['law'],row['model'],row['profile']].append(row)
    repeats=[]
    for (law,model,profile),values in sorted(paired.items()):
        if len(values)!=2 or {v['start'] for v in values}!={0,1}:raise ValueError('both matched starts required')
        a,b=sorted(values,key=lambda v:v['start'])
        repeats.append(dict(law=law,model=model,profile=profile,identities=[a['identity'],b['identity']],
            absolute_cost_difference=abs(a['cost']-b['cost']),
            maximum_normalized_parameter_difference=max(abs(x-y) for x,y in zip(a['normalized_parameters'],b['normalized_parameters'])),
            both_converged=a['converged'] and b['converged']))
    return dict(verified=True,version=recipe()['version'],manifest_sha256=completion['manifest_sha256'],
        summary_sha256=completion['summary_sha256'],parent=PARENT,total=len(rows),rows=rows,repeat_groups=repeats,
        numerically_converged=sum(v['converged'] for v in rows),parameter_rows=count,
        boundary_fits=sum(any(v['boundary']!='interior' for v in row['parameters']) for row in rows),
        intrinsic_references_outside_bounds=sum(v['reference_inside_bounds'] is False for row in rows for v in row['parameters']),
        parameters=summarize(rows),shared_seed=seed.pop(),stopping_policy=policy,
        stopping_counts=dict(sorted(Counter('+'.join(v['stopping'].get('failed_components',[])) or
            'all_components_satisfied' if v['stopping']['available'] else 'unavailable' for v in rows).items())),
        labels_changed=False,confidence_calibrated=False,scientific_decision='abstain',
        native_calls=0,optimizer_starts=0,original_reads=0,protected_reads=0,random_draws=0)


def render(report):
    if report.get('verified') is not True:raise ValueError('verified saved diagnosis required')
    n=report['total']
    lines=['# Why do short noisy fits reach calibration limits?','',
        f"**{report['numerically_converged']}/{n} fits pass numerical checks; {report['boundary_fits']}/{n} reach calibration limits.**",'',
        'All compared planted sensor settings lie inside the permitted bounds.' if not report['intrinsic_references_outside_bounds']
        else 'Some compared planted sensor settings fall outside the permitted bounds.',
        'Accurate later positions do not establish accurate or unique calibration.','',
        'The original outcomes remain unchanged. The complete uncertainty gate is not qualified.',
        'These are matched software settings with one shared noise seed, not independent aircraft observations.','',
        '| Parameter | Lower bound | Upper bound | Interior | Unit |',
        '|---|---:|---:|---:|---|']
    for p in report['parameters']:
        if p['lower']+p['upper']:
            lines.append(f"| {p['parameter']} | {p['lower']} | {p['upper']} | {p['interior']} | {p['unit']} |")
    lines+=['','The four stopping checks use their original frozen thresholds. A failed check is not relabeled.','',
        '| Unfinished fit | Failed check | Evaluations used |', '|---|---|---:|']
    for row in report['rows']:
        if not row['converged']:
            lines.append(f"| {row['identity']} | {', '.join(row['stopping'].get('failed_components',[]))} | "
                f"{row['evaluations']}/{row['maximum_evaluations']} |")
    lines+=['','This report reads saved results only: no refits, original recordings or protected inputs.',
        'A boundary-gradient sign is a local diagnostic, not proof of a unique optimum.',
        'Reference comparisons exclude starting attitude, velocity, position and the gravity fixture.',
        'A separately qualified experiment must distinguish weak calibration from an inadequate error model.',
        '', '[Parent study](../structured-noisy-training/README.md) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/structured_noisy_diagnostics.py',
        'analysis/tests/test_structured_noisy_diagnostics.py','analysis/tests/test_calibration_diagnostics.py',
        'analysis/tests/test_stopping_diagnostics.py','docs/structured-noisy-diagnosis/PLAN.md'])


def prepare(root,*,qualification,identity='structured-noisy-diagnosis-20261025'):
    if qualification is None:raise ValueError('source-bound saved-diagnosis qualification required')
    from pathlib import Path
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as threads
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    root=Path(root).resolve();env=environment()
    if env['numerical_environment']!=threads(workers=1,threads=1):raise ValueError('declared thread environment required')
    source=qualification_sources(root)
    request,tests=checked(root,qualification,sources=source,environment=env,minimum_tests=25,
        required_tests=['test_boundary_diagnostic_keeps_units_gradient_signs_and_original_fit',
            'test_saved_calibration_scope_has_one_task_and_zero_numerical_work',
            'test_saved_calibration_uses_actual_frozen_loader_and_shared_zero_work_journal',
            'test_saved_jacobian_cosines_identify_aligned_orthogonal_and_zero_columns',
            'test_saved_calibration_render_preserves_failed_gate_and_matched_seed_dependence'])
    safe_path(root,'data/'+identity);base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh finite diagnosis scope required')
    material=dict(bundle=encoded(collect(root)),recipe=encoded(recipe()),qualification_request=request,
        qualification_report=tests,qualification_environment=encoded(env))
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(material.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/structured_noisy_diagnostics.py',sources=source,
        inputs=inputs,tasks=tasks(),workers=1,threads=1,maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,allocation=manifest['allocation'],native_calls=0,optimizer_starts=0)


def evaluate(task,context):
    if {k:v for k,v in task.items() if k not in ('index','shard')}!=tasks()[0]:raise ValueError('unchanged saved-diagnosis task required')
    if context.manifest['scope']!=SCOPE:raise ValueError('unchanged saved-diagnosis scope required')
    if json.loads(context.input_path('recipe').read_bytes())!=recipe():raise ValueError('unchanged finite recipe required')
    raw=context.input_path('bundle').read_bytes()
    if len(raw)>recipe()['maximum_bundle_bytes']:raise ValueError('saved bundle exceeds allowance')
    result=calculate(json.loads(raw));context.save('diagnosis.json',result)
    return dict(passed=True,total=result['total'],parameter_rows=result['parameter_rows'],
        labels_changed=False,native_calls=0,optimizer_starts=0,original_reads=0,protected_reads=0,
        confidence_calibrated=False,scientific_decision='abstain')
