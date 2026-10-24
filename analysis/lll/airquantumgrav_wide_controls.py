# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer long controls for the wider native tangent; no observed fits."""
from lll.airquantumgrav_inventory import environment
from lll.airquantumgrav_gravity_controls import tasks,construction_limits,calculate

SCOPE='generated wider-tangent known-correction controls; no observed/protected reads or fits'


def recipe():
    from lll.airquantumgrav_gravity_controls import recipe as base
    return dict(base(),version='esa-wide-tangent-controls-v1',maximum_wall_s=7200.)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_wide_controls.py','analysis/lll/airquantumgrav_wide_report.py',
        'analysis/tests/test_airquantumgrav_wide_controls.py','analysis/tests/test_airquantumgrav_wide_report.py',
        'analysis/tests/test_ilvis0_wide_tangent.py','analysis/tests/test_ilvis0_precision_value.py',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp','docs/esa-wide-tangent-controls/PLAN.md'])


def required_tests():
    return ['test_wide_controls_standalone_loader_and_finite_matrix',
        'test_wide_controls_require_qualification_before_inputs','test_wide_controls_reject_unguarded_environment_before_inputs',
        'test_wide_controls_keep_original_accuracy_refinement_and_calibration_rules',
        'test_wide_controls_execute_shared_generated_pipeline_with_exact_native_kinds',
        'test_wide_controls_report_rejects_open_study_before_audit',
        'test_wide_controls_report_does_not_claim_solver_or_observed_qualification',
        'test_wide_tangent_requires_bound_source_and_keeps_clock_values_binary64',
        'test_wide_residual_and_independent_straight_motion_derivative_survive_coordinate_cast',
        'test_wide_forecast_uses_no_later_coordinates_and_keeps_all_columns']+[
        f'test_wide_every_derivative_matches_finite_difference_and_independent_binary64_reference[{p}-{m}]'
        for p in (False,True) for m in recipe()['models']]


def prepare(root,*,qualification,identity='esa-wide-tangent-controls-20261024'):
    if qualification is None:raise ValueError('source-bound wider-tangent qualification required')
    import re
    from pathlib import Path
    from lll.compute_budget import environment as threads
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.studies.closed import ClosedStudy
    from lll.airquantumgrav_height_training import qualified_parents
    env=environment();r=recipe()
    if env['numerical_environment']!=threads(workers=r['workers'],threads=r['threads']):raise ValueError('declared thread environment required')
    root=Path(root).resolve()
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh identity required')
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh wider controls required')
    sources=qualification_sources(root);request,tests=checked(root,qualification,sources=sources,environment=env,
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    # The current helper adds receiver conversion functions. The existing
    # qualified compatibility check verifies all five original physical helper
    # bodies plus unchanged truth and numerical source dependencies.
    compatibility=qualified_parents(root)
    parent=ClosedStudy(root,'docs/esa-gravity-controls')
    try:
        receipt=parent.read('evidence-receipt.json');key='artifacts/publication/verified-report.json'
        report=parent.read(key,receipt['artifacts'][key])
        if not report['qualified'] or report['passed']!=48:raise ValueError('qualified original physical controls required')
        for name in set(sources)&parent.manifest['sources'].keys():
            if (name!='analysis/lll/airquantumgrav_observation_truth.py'
                    and digest((root/name).read_bytes())!=parent.manifest['sources'][name]):
                raise ValueError('shared physical source changed: '+name)
        proof=dict(manifest_sha256=parent.completion['manifest_sha256'],summary_sha256=parent.completion['summary_sha256'],
            report_sha256=receipt['artifacts'][key],same_physical_bounds_and_targets=True,
            qualified_compatibility=compatibility)
    finally:parent.close()
    base.mkdir(parents=True);inputs={}
    materials=[('recipe',encoded(r)),('qualification-environment',encoded(env)),('qualification-request',request),
        ('qualification-report',tests),('qualified-parent',encoded(proof))]
    for i,(key,raw) in enumerate(materials):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_wide_controls.py',sources=sources,inputs=inputs,
        tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,cases=48,limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import json
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_wide_tangent import load
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    declared={k:v for k,v in task.items() if k not in ('index','shard')};r=recipe()
    if ({t['identity']:t for t in tasks()}.get(task['identity'])!=declared
            or json.loads(context.input_path().read_bytes())!=r or context.manifest['scope']!=SCOPE
            or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()
            or set(context.manifest['inputs'])!={'recipe','qualification-environment','qualification-request','qualification-report','qualified-parent'}):
        raise ValueError('unchanged generated-only wider-control scope required')
    counts=construction_limits(r);journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:counts});journal.start(task['identity'])
    try:
        spec=task['payload'];anchor=None if spec['gravity_model']=='constant' else (1500. if spec['height_profile']=='climb' else 3500.)
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
        kernel,km=load_kernel(directory,gravity_anchor_height_m=anchor)
        tangent,tm=load(directory,gravity_anchor_height_m=anchor,
            expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
        env=environment()
        if (km['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_native.c']
                or km['compiler']!=env['compilers']['cc'] or tm['compiler']!=env['compilers']['c++']):
            raise ValueError('frozen original value and wider tangent compilers required')
        context.save('compilation.json',dict(value=km,tangent=tm))
        def reserve_construction(**work):
            _check_continue(context.root,context.manifest)
            for key,value in work.items():journal.reserve(task['identity'],key,value)
        result=calculate(spec,r,kernel=kernel,tangent=tangent,reserve=context.charge,
            reserve_construction=reserve_construction,save=context.save,check_continue=lambda:_check_continue(context.root,context.manifest))
        journal.verify()
        if any(journal.count(task['identity'],k)!=v for k,v in counts.items()):raise ValueError('complete construction accounting required')
        return result
    finally:context.note_file(journal.path)
