# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched generated training controls using the explicit wider problem factory."""
from lll.airquantumgrav_inventory import environment
from lll.airquantumgrav_height_training import tasks,construction_limits

SCOPE='generated wider training/forecast qualification; no original/protected reads or observed starts'


def recipe():
    from lll.airquantumgrav_height_training import recipe as original
    return dict(original(),version='esa-wide-training-controls-v1')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_wide_training_controls.py',
        'analysis/lll/airquantumgrav_wide_training_report.py','analysis/tests/test_airquantumgrav_wide_training_controls.py',
        'analysis/tests/test_airquantumgrav_wide_training_report.py',
        'analysis/tests/test_ilvis0_wide_training_binding.py','analysis/tests/test_study_protocol_binding.py',
        'analysis/tests/test_airquantumgrav_wide_training_prediction.py','analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp','docs/esa-wide-training-controls/PLAN.md'])


def required_tests():
    return ['test_wide_training_standalone_loader_and_original_finite_matrix',
        'test_wide_training_preparation_requires_qualification_before_inputs',
        'test_wide_training_preparation_rejects_unguarded_environment_before_inputs',
        'test_wide_training_keeps_generated_truth_starts_physics_and_targets',
        'test_wide_training_report_rejects_open_study_before_numerical_imports',
        'test_wide_training_render_keeps_qualification_distinct_from_aircraft_findings',
        'test_wide_training_reuses_qualified_protocols_without_global_patches',
        'test_protocol_binding_changes_only_explicit_import_and_leaves_shared_names_untouched',
        'test_protocol_binding_rejects_unbound_source_before_execution']+[
        f'test_wide_training_no_later_position_influence_and_exact_accounting[{policy}-{profile}]'
        for policy in recipe()['policies'] for profile in (False,True)]


def prepare(root,*,qualification,identity='esa-wide-training-controls-20261024'):
    if qualification is None:raise ValueError('source-bound full training qualification required')
    import re
    from pathlib import Path
    from lll.compute_budget import environment as threads
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.closed import ClosedStudy
    from lll.studies.runtime import Definition
    from lll.ilvis0_wide_training import SOURCES,bind
    r=recipe();env=environment()
    if env['numerical_environment']!=threads(workers=r['workers'],threads=r['threads']):raise ValueError('declared thread environment required')
    root=Path(root).resolve()
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh identity required')
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh generated training scope required')
    sources=qualification_sources(root);request,tests=checked(root,qualification,sources=sources,environment=env,
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    parent=ClosedStudy(root,'docs/esa-wide-tangent-controls')
    try:
        receipt=parent.read('evidence-receipt.json');key='artifacts/publication/verified-report.json'
        report=parent.read(key,receipt['artifacts'][key])
        if not report['verified'] or not report['qualified'] or report['passed']!=48:
            raise ValueError('all 48 long known-motion controls must qualify first')
        for name in set(sources)&parent.manifest['sources'].keys():
            if digest((root/name).read_bytes())!=parent.manifest['sources'][name]:
                raise ValueError('qualified wider numerical dependency changed: '+name)
        proof=dict(manifest_sha256=parent.completion['manifest_sha256'],summary_sha256=parent.completion['summary_sha256'],
            report_sha256=receipt['artifacts'][key])
    finally:parent.close()
    original={name:digest((root/'analysis/lll'/name).read_bytes()) for name in SOURCES}
    run,calculate,binding=bind(expected_sources=original)
    base.mkdir(parents=True);inputs={}
    materials=[('recipe',encoded(r)),('qualification-environment',encoded(env)),('qualification-request',request),
        ('qualification-report',tests),('qualified-parent',encoded(proof)),('protocol-binding',encoded(binding))]
    for i,(key,raw) in enumerate(materials):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_wide_training_controls.py',sources=sources,inputs=inputs,
        tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,cases=24,limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import json
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_wide_tangent import load
    from lll.ilvis0_wide_training import SOURCES,bind
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    r=recipe();read=lambda key:json.loads(context.input_path(key).read_bytes())
    declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if ({t['identity']:t for t in tasks()}.get(task['identity'])!=declared or read('recipe')!=r
            or read('qualification-environment')!=environment() or context.manifest['scope']!=SCOPE
            or set(context.manifest['inputs'])!={'recipe','qualification-environment','qualification-request','qualification-report',
                'qualified-parent','protocol-binding'}):raise ValueError('unchanged generated-only wider training scope required')
    expected={name:context.manifest['sources']['analysis/lll/'+name] for name in SOURCES}
    run,calculate,binding=bind(expected_sources=expected)
    if binding!=read('protocol-binding'):raise ValueError('explicit factory substitution differs from its freeze')
    context.save('protocol-binding.json',binding)
    counts=construction_limits(r);journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:counts});journal.start(task['identity'])
    try:
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';env=environment()
        def factory(anchor):
            value,vm=load_kernel(directory,gravity_anchor_height_m=anchor)
            tangent,tm=load(directory,gravity_anchor_height_m=anchor,
                expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
            if (vm['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_native.c']
                    or vm['compiler']!=env['compilers']['cc'] or tm['compiler']!=env['compilers']['c++']):
                raise ValueError('frozen native sources and compilers required')
            return value,tangent,dict(value=vm,tangent=dict(tm,gravity_model='inverse-square-height-v1'))
        def reserve_construction(**work):
            _check_continue(context.root,context.manifest)
            for key,value in work.items():journal.reserve(task['identity'],key,value)
        result=calculate(task['payload'],r,kernel_factory=factory,reserve=context.charge,
            reserve_construction=reserve_construction,save=context.save,
            check_continue=lambda:_check_continue(context.root,context.manifest))
        journal.verify()
        if any(journal.count(task['identity'],key)!=value for key,value in counts.items()):raise ValueError('construction charges differ')
        return result
    finally:context.note_file(journal.path)
