# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four exposed saved points; shared reconstruction, kernels and study lifecycle."""
import json
import math
from pathlib import Path

IDENTITY='saved-timing-boundary-20261027'
PARENT='docs/prediction-calibration-compensated'
PLAN='docs/SAVED_TIMING_BOUNDARY_PLAN.md'
SCOPE='four exposed saved-point timing branches and correction decomposition; no fitting or forecasts'
SEEDS=(281474977010692,281474977010693)


def configuration():
    return dict(id=IDENTITY,scope=SCOPE,maximum_evaluations=64,workers=4,threads=1,
                maximum_wall_s=3600.,nonlinear_fit_starts=0)


def identities():
    return [f'calibration-seed-{seed}-point-sphere_rotating-1-{start}' for seed in SEEDS for start in (0,1)]


def work_allowance(seed):
    from lll.compensated_prediction_release import case_recipe
    from lll.timing_arithmetic_study import allowance
    if type(seed) is not int or seed not in SEEDS:raise ValueError('one of the two exposed seeds required')
    return allowance(case_recipe(seed),64)


def canonical_fit(fit):
    names=fit['active_parameters'];point=fit['normalized_parameters']
    vector=[point[name] for name in names] if isinstance(point,dict) else list(point)
    if (len(names)!=27 or len(set(names))!=27 or len(vector)!=27
            or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1 for v in vector)
            or vector!=fit['local_linearization']['normalized_parameters']):
        raise ValueError('unchanged complete ordered saved point required')
    return dict(fit,normalized_parameters=vector)


def parent_changes(parent,current):
    allowed={'analysis/lll/prediction_calibration_report.py','analysis/tests/test_compensated_prediction_release.py',
             'analysis/lll/structured_noisy_publication.py','analysis/tests/test_structured_noisy_publication.py'}
    changes={name:dict(original_sha256=sha,current_sha256=current.get(name))
             for name,sha in parent.items() if current.get(name)!=sha}
    if not set(changes)<=allowed:raise ValueError('parent scientific source changed')
    return changes


def bind_capture(provider,*,raw,expected_sha256):
    from lll.saved_point_runtime import bind_capture as shared
    from lll.studies.artifacts import digest
    return shared(provider,raw=raw,expected_sha256=expected_sha256,
                  provider_sha256=digest(Path(__file__).read_bytes()))


def _saved_linear_report(root):
    from lll.studies.artifacts import ArchiveStore,digest
    prefix='docs/prediction-linear-timing-review';store=ArchiveStore(root)
    try:
        cat=store.catalog();raw=store._read(prefix+'/manifest.json',cat);m=json.loads(raw)
        receipt=json.loads(store._read(prefix+'/evidence-receipt.json',cat))
        if digest(raw)!=receipt['manifest_sha256']:raise ValueError('saved linear report manifest changed')
        raw=store._read(prefix+'/review.json',cat)
        if digest(raw)!=m['artifacts']['review.json']:raise ValueError('saved linear corrections changed')
        report=json.loads(raw)
        if report['charged_linear_solves']!=4 or len(report['rows'])!=4:
            raise ValueError('complete saved four-point linear review required')
        return report
    finally:store.close()


def selection(root):
    import statistics
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    from lll.prediction_phase_review import clock_geometry
    report=_saved_linear_report(root);linear={r['identity']:r for r in report['rows']}
    s=ClosedStudy(root,PARENT)
    try:
        if set(linear)!=set(identities()) or report['manifest_sha256']!=s.completion['manifest_sha256']:
            raise ValueError('same four exposed source points required')
        r=s.input('population')['descriptor']['recipe'];rate=r['rate_hz'];scale=r['limits']['time_offset'];points=[]
        for identity in identities():
            task=s.tasks[identity];envelope=s.envelope(identity);raw_fit=s.artifact(identity,'fit.json');fit=canonical_fit(raw_fit)
            old={name:s.artifact(identity,name) for name in ('input-binding.json','training-observations.json',
                                                            'training-error-operator.json')}
            fit_sha=envelope['artifacts']['artifacts/'+identity+'/fit.json'];saved=linear[identity]
            if (saved['fit_sha256']!=fit_sha or not saved['result']['replay_matches_saved']
                    or saved['result']['replay']['active_parameters']!=fit['active_parameters']):
                raise ValueError('unchanged full-column linear correction required')
            n=old['input-binding.json']['native_packets'];dt=[(i+1)/rate-i/rate for i in range(n)]
            hashes=old['input-binding.json']['full_array_sha256'];times=s.artifact(identity,'forecast.json')['times_s']
            g=clock_geometry(fit,times,dt,expected_dt_sha256=hashes['dt'],expected_times_sha256=hashes['times'])
            cut=old['input-binding.json']['training_epochs'];column=fit['active_parameters'].index('time_offset')
            center=fit['normalized_parameters'][column]-statistics.median(g['signed_distance_s'][:cut])/scale
            point=dict(identity=identity,payload=task['payload'],fit=fit,saved_converged=fit['converged'],artifacts=old,
                artifact_sha256={name:envelope['artifacts']['artifacts/'+identity+'/'+name] for name in ('fit.json',*old)},
                source_completion=s.completion,original_parameter_encoding=type(raw_fit['normalized_parameters']).__name__,
                correction=saved['result']['replay']['correction'],timing_center=center,timing_scale=scale)
            point['selection_sha256']=digest(encoded(point));points.append(point)
        return points
    finally:s.close()


def sources(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    s=ClosedStudy(root,PARENT)
    try:parent=set(s.manifest['sources'])
    finally:s.close()
    own=['analysis/lll/timing_boundary_probe.py','analysis/lll/timing_boundary_study.py',
         'analysis/lll/timing_boundary_report.py','analysis/tests/test_timing_boundary_probe.py',
         'analysis/tests/test_timing_boundary_study.py','analysis/tests/test_timing_boundary_report.py',PLAN]
    return sorted(parent|set(source_closure(root,own)))


def prepare(root,*,qualification):
    if qualification is None:raise ValueError('source-bound diagnostic qualification required')
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    root=Path(root).resolve();names=sources(root);env=environment();cfg=configuration()
    s=ClosedStudy(root,PARENT)
    try:
        if env!=s.input('qualification-environment'):raise ValueError('parent numerical environment changed')
        changes=parent_changes(s.manifest['sources'],{n:digest((root/n).read_bytes()) for n in names})
    finally:s.close()
    request,tests=checked(root,qualification,sources=names,environment=env,minimum_tests=20,required_tests=[
        'test_boundary_probe_keeps_all_columns_and_differences_inside_each_branch[False]',
        'test_boundary_probe_keeps_all_columns_and_differences_inside_each_branch[True]',
        'test_boundary_probe_charges_before_execution_and_does_not_exceed_cap',
        'test_saved_point_encoding_changes_no_value_or_original_record',
        'test_capture_binding_exits_before_any_fit_or_forecast'])
    base=root/'data/ilvis0-source-point-development'/f'{IDENTITY}-inputs'
    if base.exists() or (root/'data'/IDENTITY).exists():raise ValueError('fresh diagnostic allowance required')
    points=selection(root);base.mkdir(parents=True);inputs={}
    values=dict(points=encoded(points),configuration=encoded(cfg),environment=encoded(env),
        **{'qualification-request':request,'qualification-report':tests,'parent-source-updates':encoded(changes)})
    for i,(name,raw) in enumerate(values.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[name]=str(path.relative_to(root))
    tasks=[dict(identity=p['identity'],input_key='points',native_kind='tangent',
        payload=dict(point_index=i,selection_sha256=p['selection_sha256']),
        limits=work_allowance(p['payload']['draw_seed'])) for i,p in enumerate(points)]
    value=dict(id=IDENTITY,scope=SCOPE,adapter='analysis/lll/timing_boundary_study.py',sources=names,inputs=inputs,
        tasks=tasks,workers=4,threads=1,maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(value));m=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+IDENTITY,allocation=m['allocation'],limits=m['limits'])


def evaluate(task,context):
    if context.manifest['scope']!=SCOPE:raise ValueError('exact saved timing diagnostic scope required')
    from lll.airquantumgrav_inventory import environment
    from lll.stopping_consistency_study import verify_bindings
    from lll.coordinate_optimizer_study import kernels
    from lll.compensated_prediction_release import case_recipe
    from lll.structured_noisy_training import limits
    from lll.studies.artifacts import digest,encoded
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    from lll.timing_boundary_probe import probe
    cfg=json.loads(context.input_path('configuration').read_bytes());env=json.loads(context.input_path('environment').read_bytes())
    verify_bindings(context.root/'source-freeze',context.manifest['sources'],env,environment())
    if cfg!=configuration():raise ValueError('fixed diagnostic configuration required')
    points=json.loads(context.input_path('points').read_bytes());record=points[task['payload']['point_index']]
    checked=dict(record);selection_hash=checked.pop('selection_sha256')
    seed=record['payload']['draw_seed'];r=case_recipe(seed);identity=task['identity']
    if (identity not in identities() or record['identity']!=identity or digest(encoded(checked))!=selection_hash
            or task['payload']['selection_sha256']!=selection_hash or task['limits']!=work_allowance(seed)):
        raise ValueError('unchanged exposed selection and allowance required')
    def provider(evaluate,point,**options):
        return probe(evaluate,point,active=record['fit']['active_parameters'],correction=record['correction'],
            timing_center=record['timing_center'],timing_scale=record['timing_scale'],
            expected_cost=record['fit']['residual_sum_squares'],
            expected_actual_cost_change=record['fit']['stability_probe']['actual_cost_change'],
            expected_linearization=record['fit']['local_linearization'],
            reserve=options['reserve'],check_continue=options['check_continue'],bounds=options['bounds'])
    from lll.saved_point_runtime import run_point
    return run_point(task,context,record,r,maximum_evaluations=64,provider=provider,
                     provider_source='analysis/lll/timing_boundary_study.py')
