# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched saved-point arithmetic using the original reconstruction protocol."""
import json
import math
from pathlib import Path

IDENTITY='saved-point-timing-arithmetic-20261026'
SCOPE='four exposed saved points, four arithmetic settings; no nonlinear fits or forecasts'
QUALIFICATION='data/ilvis0-source-point-development/timing-arithmetic-qualification-v3-request.json'
FRAMEWORK_UPDATES=frozenset(('analysis/lll/studies/artifacts.py','analysis/lll/studies/testing.py'))


def configuration(kind='timing'):
    if kind=='timing':
        return dict(kind=kind,id=IDENTITY,scope=SCOPE,qualification=QUALIFICATION,maximum_evaluations=64,
            workers=2,threads=1,maximum_wall_s=3600.,plan='docs/SAVED_POINT_TIMING_PLAN.md')
    if kind=='coordinate-full':
        return dict(kind=kind,id='saved-point-coordinate-precision-20261026',
            scope='four exposed saved points; original replay and compensated complete-column/stopping diagnostic; no fits',
            qualification='data/ilvis0-source-point-development/saved-coordinate-full-qualification-request.json',
            maximum_evaluations=171,workers=4,threads=1,maximum_wall_s=3600.,plan='docs/SAVED_POINT_COORDINATE_PLAN.md')
    raise ValueError('one separately frozen diagnostic configuration required')


def verify_coordinate_gate(report):
    candidate=[r for r in report['rows'] if r['mode']=='compensated']
    if (report['complete']!=18 or report['selected']!=18 or report['failures'] or not report['candidate_qualified']
            or len(candidate)!=6 or not all(r['precision_passed'] for r in candidate)):
        raise ValueError('complete qualified coordinate-control matrix required')


def verify_coordinate_binding(binding,current,environment):
    if (binding.get('environment')!=environment or not binding.get('sources')
            or any(current.get(n)!=sha for n,sha in binding['sources'].items())):
        raise ValueError('qualified coordinate source or environment changed')


def verify_parent(parent,current):
    changes={}
    for name,sha in parent.items():
        if name not in current:raise ValueError('missing parent source: '+name)
        if current[name]!=sha:
            if name not in FRAMEWORK_UPDATES:raise ValueError('original scientific source changed: '+name)
            changes[name]=dict(original_sha256=sha,current_sha256=current[name],
                reason='verified archive pack-size/lookup and local-test socket preflight repairs; no numerical equations')
    return changes


def allowance(r,maximum_evaluations=64):
    if maximum_evaluations not in (64,171):raise ValueError('one declared diagnostic evaluation cap required')
    from lll.saved_point_runtime import allowance as shared
    return shared(r,maximum_evaluations)


def bind_probe(provider,*,raw,expected_sha256):
    from lll.studies.protocols import bind_function
    from lll.studies.artifacts import digest
    from lll import stopping_consistency_study as original
    return bind_function(raw,expected_sha256=expected_sha256,function='calculate_point',
        import_module='lll.stopping_consistency',import_name='probe',provider=provider,
        provider_source_sha256=digest(Path(__file__).read_bytes()),namespace=dict(math=math,Path=Path,
            Captured=original.Captured,verify_replay=original.verify_replay,
            no_nonlinear_fit=original.no_nonlinear_fit,__file__=original.__file__))


def sources(root,kind='timing'):
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    from lll.stopping_consistency_study import PARENT
    s=ClosedStudy(root,PARENT)
    try:parent=set(s.manifest['sources'])
    finally:s.close()
    if kind=='coordinate-full':
        control=ClosedStudy(root,'docs/coordinate-precision-controls')
        try:parent.update(control.manifest['sources'])
        finally:control.close()
    own=['analysis/lll/timing_arithmetic_study.py','analysis/lll/timing_arithmetic_probe.py',
        'analysis/lll/ilvis0_timing_arithmetic.py','analysis/lll/timing_arithmetic_report.py',
        'analysis/tests/test_ilvis0_timing_arithmetic.py','analysis/tests/test_timing_arithmetic_probe.py',
        'analysis/tests/test_timing_arithmetic_study.py','analysis/tests/test_timing_arithmetic_report.py',
        'analysis/tests/test_stopping_consistency.py','analysis/tests/test_stopping_consistency_study.py',
        'analysis/tests/test_coordinate_precision.py','analysis/tests/test_coordinate_precision_controls.py',
        'docs/SAVED_POINT_TIMING_PLAN.md','docs/SAVED_POINT_COORDINATE_PLAN.md']
    return sorted(parent|set(source_closure(root,own)))


def prepare(root,kind='timing'):
    from lll.studies.closed import ClosedStudy
    from lll.studies.runtime import Definition
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    from lll.prediction_calibration_study import case_recipe
    from lll.stopping_consistency_study import PARENT,selection
    root=Path(root).resolve();cfg=configuration(kind);env=environment();names=sources(root,kind)
    directory=root/'data/ilvis0-source-point-development'/f'{cfg["id"]}-inputs'
    if directory.exists() or (root/'data'/cfg['id']).exists():raise ValueError('fresh finite study required')
    required=['test_feasible_timing_branch_matches_right_hand_reference[turning-fast]',
            'test_relative_longitude_recovers_weak_gyro_sensitivity',
            'test_binding_replaces_probe_without_patching_original_module',
            'test_probe_rejects_invalid_work_before_an_extra_evaluation[charge]']
    if kind=='coordinate-full':
        required+=['test_full_precision_probe_retains_every_column_and_original_failed_label[26]',
            'test_full_precision_probe_retains_every_column_and_original_failed_label[27]',
            'test_full_configuration_freezes_new_budget_and_four_threads',
            'test_coordinate_parent_gate_requires_the_complete_matrix',
            'test_coordinate_kernel_binding_rejects_source_or_environment_changes',
            'test_known_answer_derivatives_at_reference_optima[interior-26]',
            'test_known_answer_derivatives_at_reference_optima[interior-27]']
        required+=[f'test_compensated_axis_matches_independent_midpoint_polynomial[large-{axis}]'
            for axis in ('north','east','height')]
        required+=[f'{name}[{profile}-{model}]' for name in (
            'test_compensation_preserves_full_physical_problem','test_compensated_lower_timing_bound_all_physical_cases')
            for profile in (False,True) for model in ('sphere_rotating','sphere_still','flat_still')]
    request,report=checked(root,cfg['qualification'],sources=names,environment=env,
        minimum_tests=60 if kind=='coordinate-full' else 25,required_tests=required)
    parent=ClosedStudy(root,PARENT)
    try:
        old_sources=parent.manifest['sources']
        if env!=parent.input('qualification-environment'):raise ValueError('original numerical environment changed')
    finally:parent.close()
    updates=verify_parent(old_sources,{n:digest((root/n).read_bytes()) for n in names})
    points=selection(root)
    coordinate_gate=None;coordinate_binding=None
    if kind=='coordinate-full':
        from lll.coordinate_precision_controls import inspect
        coordinate_gate=inspect(root,'docs/coordinate-precision-controls');verify_coordinate_gate(coordinate_gate)
        control=ClosedStudy(root,'docs/coordinate-precision-controls')
        try:
            coordinate_binding=dict(manifest_sha256=control.completion['manifest_sha256'],
                sources=control.manifest['sources'],environment=control.input('environment'))
        finally:control.close()
        verify_coordinate_binding(coordinate_binding,{n:digest((root/n).read_bytes()) for n in names},env)
    directory.mkdir(parents=True);inputs={}
    values={'points':encoded(points),'environment':encoded(env),'parent-sources':encoded(old_sources),
        'framework-updates':encoded(updates),'qualification-request':request,'qualification-report':report,
        'configuration':encoded(cfg)}
    if coordinate_gate is not None:
        values['coordinate-gate']=encoded(coordinate_gate)
        values['coordinate-binding']=encoded(coordinate_binding)
    for index,(name,raw) in enumerate(values.items()):
        path=directory/f'input-{index:03d}';atomic(path,raw);inputs[name]=str(path.relative_to(root))
    tasks=[dict(identity=p['identity'],input_key='points',native_kind='tangent',
        payload=dict(point_index=i,selection_sha256=p['selection_sha256']),
        limits=allowance(case_recipe(p['payload']['draw_seed']),cfg['maximum_evaluations'])) for i,p in enumerate(points)]
    definition=dict(id=cfg['id'],scope=cfg['scope'],adapter='analysis/lll/timing_arithmetic_study.py',sources=names,
        inputs=inputs,tasks=tasks,workers=cfg['workers'],threads=cfg['threads'],maximum_wall_s=cfg['maximum_wall_s'])
    atomic(directory/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+cfg['id'],allocation=manifest['allocation'],limits=manifest['limits'],framework_updates=updates)


def evaluate(task,context):
    from lll.airquantumgrav_inventory import environment
    from lll.prediction_calibration_study import case_recipe
    from lll.stopping_consistency_study import point_identity,verify_bindings
    from lll.structured_noisy_study import _kernels
    from lll.structured_noisy_training import limits
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_timing_arithmetic import load,recentered
    from lll.timing_arithmetic_probe import probe,full_precision_probe,MODES
    if context.manifest['scope'] not in (configuration('timing')['scope'],configuration('coordinate-full')['scope']):
        raise ValueError('exact diagnostic scope required')
    cfg=(json.loads(context.input_path('configuration').read_bytes())
        if 'configuration' in context.manifest.get('inputs',{}) else configuration())
    if cfg!=configuration(cfg.get('kind')) or context.manifest['scope']!=cfg['scope']:
        raise ValueError('frozen diagnostic configuration changed')
    full=cfg['kind']=='coordinate-full'
    env=json.loads(context.input_path('environment').read_bytes())
    if full:
        gate=json.loads(context.input_path('coordinate-gate').read_bytes());verify_coordinate_gate(gate)
        binding=json.loads(context.input_path('coordinate-binding').read_bytes())
        if gate['manifest_sha256']!=binding['manifest_sha256']:raise ValueError('coordinate gate manifest differs')
        verify_coordinate_binding(binding,context.manifest['sources'],env)
    verify_bindings(context.root/'source-freeze',context.manifest['sources'],env,environment())
    parent=json.loads(context.input_path('parent-sources').read_bytes())
    if verify_parent(parent,context.manifest['sources'])!=json.loads(context.input_path('framework-updates').read_bytes()):
        raise ValueError('undeclared historical framework substitution')
    points=json.loads(context.input_path('points').read_bytes());record=points[task['payload']['point_index']]
    seed=record['payload']['draw_seed'];case=record['payload']['case'];identity=task['identity'];r=case_recipe(seed)
    if (identity!=point_identity(seed,case['profile'],case['start'])
            or task['payload']['selection_sha256']!=record['selection_sha256']
            or task['limits']!=allowance(r,cfg['maximum_evaluations'])):
        raise ValueError('exact exposed points and separate finite allowances required')
    freeze=digest((context.root/'manifest.json').read_bytes());construction=limits(r,'increment')[1]
    cj=Journal(context.directory/'construction.sqlite',freeze=freeze,limits={identity:construction});cj.start(identity)
    ej=Journal(context.directory/'evaluations.sqlite',freeze=freeze,limits={identity:dict(evaluations=cfg['maximum_evaluations'])});ej.start(identity)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    bj=Journal(directory/'timing-builds.sqlite',freeze=freeze,limits={'worker':dict(builds=1)})
    if not bj.verify()['starts']:bj.start('worker')
    check=lambda:_check_continue(context.root,context.manifest)
    def charge_construction(**work):
        check()
        for key,value in work.items():cj.reserve(identity,key,value)
    def charge_evaluation(**work):
        check()
        if work!={'evaluations':1}:raise ValueError('one complete derivative evaluation charge required')
        ej.reserve(identity,'evaluations')
    state={'mode':'baseline'};budget=None
    try:
        noise,baseline_factory=_kernels(context,env)
        def factory(anchor):
            _,baseline,meta=baseline_factory(anchor)
            if full:
                from lll.ilvis0_coordinate_precision import load as compensated
                right,rm=compensated(directory,gravity_anchor_height_m=anchor,
                    expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'],
                    reserve_build=lambda:bj.reserve('worker','builds'))
            else:
                right,rm=load(directory,right_at_lower=True,relative_longitude=False,gravity_anchor_height_m=anchor,
                    expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'],
                    reserve_build=lambda:bj.reserve('worker','builds'))
            if rm['compiler']!=env['compilers']['c++']:raise ValueError('frozen compiler changed')
            providers=(dict(baseline=baseline,compensated=right) if full else
                dict(baseline=baseline,boundary=right,longitude=recentered(baseline),both=recentered(right)))
            context.save('arithmetic-bindings.json',dict(original=meta,alternative=rm,modes=list(providers)))
            context.save_bytes('timing-build-journal.sqlite',bj.path.read_bytes())
            def dispatch(*args,**kwargs):return providers[state['mode']](*args,**kwargs)
            return None,dispatch,meta
        def matched(evaluate,point,**options):
            selected=full_precision_probe if full else probe
            extra=dict(frozen_probe=options['frozen_probe']) if full else {}
            return selected(evaluate,point,active=record['fit']['active_parameters'],saved_cost=record['fit']['residual_sum_squares'],
                select=lambda mode:state.update(mode=mode),reserve=options['reserve'],
                check_continue=options['check_continue'],bounds=options['bounds'],**extra)
        name='analysis/lll/stopping_consistency_study.py';raw=(context.root/'source-freeze'/name).read_bytes()
        bound,proof=bind_probe(matched,raw=raw,expected_sha256=context.manifest['sources'][name])
        context.save('capture-binding.json',proof)
        with context.prepay_native(native_calls=task['limits']['native_calls'],packet_visits=task['limits']['packet_visits']) as budget:
            protocol='analysis/lll/airquantumgrav_prediction.py'
            result=bound(record,r,kernel_factory=factory,noise_kernel=noise,reserve=budget.reserve,
                reserve_construction=charge_construction,reserve_evaluation=charge_evaluation,
                save=context.save,check_continue=check,protocol_source=(context.root/'source-freeze'/protocol).read_bytes(),
                protocol_sha256=context.manifest['sources'][protocol])
        cj.verify();ej.verify();bj.verify()
        if ej.count(identity,'evaluations')!=result['evaluations']:raise ValueError('evaluation accounting differs')
        return dict(result,stopping_check_executed=full,fit_labels_changed=False)
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())
        context.note_file(cj.path);context.note_file(ej.path)
