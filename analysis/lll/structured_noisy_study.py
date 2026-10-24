# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite lifecycle wiring; calculations stay in shared prediction components."""
import json
from pathlib import Path

from lll.structured_noisy_training import SCOPE,recipe,tasks,limits


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_publication.py','analysis/tests/test_structured_noisy_study.py',
        'analysis/lll/studies/qualification.py','analysis/tests/run_numerical.py',
        'docs/structured-noisy-training/PLAN.md'])


def prepare(root,*,qualification,identity='structured-noisy-training-20261025'):
    import re
    if qualification is None or not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('passing qualification and safe fresh study identity required')
    from lll.airquantumgrav_inventory import environment
    from lll.studies.qualification import checked
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.runtime import Definition
    root=Path(root).resolve();r=recipe();env=environment()
    request,report=checked(root,qualification,sources=qualification_sources(root),environment=env,
        required_tests=['test_two_minute_definition_retains_full_matrix_and_finite_limits',
            'test_worker_prepays_native_work_and_keeps_construction_separate',
            'test_worker_preserves_prepayment_and_artifacts_after_failure',
            'test_adapter_executes_through_the_actual_frozen_loader'],minimum_tests=6)
    parent='data/ilvis0-source-point-development/shared-noisy-protocol-20261025-request.json'
    declared=json.loads(safe_path(root,parent).read_bytes())
    required=[f'test_complete_short_native_noisy_protocol[True-{p}-{m}-{law}-short-noisy-v1]'
        for p in (False,True) for m in (0,1,2) for law in ('increment','point')]
    parent_request,parent_report=checked(root,parent,sources=sorted(declared['sources']),environment=env,
        required_tests=required,minimum_tests=128)
    directory=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if directory.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh finite study required')
    directory.mkdir(parents=True);inputs={}
    for index,(name,raw) in enumerate((('recipe',encoded(r)),('qualification-request',request),
            ('qualification-report',report),('qualification-environment',encoded(env)),
            ('native-parent-request',parent_request),('native-parent-report',parent_report))):
        path=directory/f'input-{index:03d}';atomic(path,raw);inputs[name]=str(path.relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/structured_noisy_study.py',
        sources=qualification_sources(root),inputs=inputs,tasks=tasks(r),workers=r['workers'],threads=r['threads'],
        maximum_wall_s=r['maximum_wall_s'])
    atomic(directory/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,allocation=manifest['allocation'],limits=manifest['limits'])


def _kernels(context,env):
    from lll.ilvis0_noise_step import load as noise_load
    from lll.ilvis0_wide_tangent import load as wide_load,derive
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    builds=Journal(directory/'builds.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={'worker':dict(builds=2)})
    if not builds.verify()['starts']:builds.start('worker')
    hashes=context.manifest['sources'];cpp='analysis/lll/ilvis0_tangent.cpp'
    noise,meta=noise_load(directory,expected_source_sha256=hashes[cpp],
        expected_bridge_sha256=hashes['analysis/lll/ilvis0_noise_bridge.cpp'],
        expected_wide_loader_sha256=hashes['analysis/lll/ilvis0_wide_tangent.py'],
        reserve_build=lambda:builds.reserve('worker','builds'))
    raw=(context.root/'source-freeze'/cpp).read_bytes();sha=digest(derive(raw,expected_sha256=hashes[cpp]))
    def factory(anchor):
        if not (directory/('wide-tangent-'+sha+'.so')).exists():builds.reserve('worker','builds')
        tangent,tm=wide_load(directory,expected_source_sha256=hashes[cpp],gravity_anchor_height_m=anchor)
        if meta['compiler']!=env['compilers']['c++'] or tm['compiler']!=env['compilers']['c++']:
            raise ValueError('native compiler differs from the frozen environment')
        builds.verify();context.save_bytes('worker-build-journal.sqlite',builds.path.read_bytes())
        return None,tangent,dict(tangent=tm,noise_bridge=meta)
    return noise,factory


def evaluate(task,context):
    from lll.airquantumgrav_inventory import environment
    from lll.structured_noisy_training import calculate
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    r=recipe();identity=task['identity'];expected={t['identity']:t for t in tasks(r)}
    if ({k:v for k,v in task.items() if k not in ('index','shard')}!=expected.get(identity)
            or json.loads(context.input_path().read_bytes())!=r or context.manifest['scope']!=SCOPE
            or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()):
        raise ValueError('unchanged finite generated-data study and environment required')
    allowance,construction=limits(r,task['payload']['law'])
    journal=Journal(context.directory/'construction.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={identity:construction});journal.start(identity);budget=None
    def reserve_construction(**work):
        _check_continue(context.root,context.manifest)
        for key,value in work.items():journal.reserve(identity,key,value)
    try:
        noise,factory=_kernels(context,environment())
        with context.prepay_native(native_calls=allowance['native_calls'],packet_visits=allowance['packet_visits']) as budget:
            result=calculate(task['payload'],r,kernel_factory=factory,noise_kernel=noise,
                reserve=budget.reserve,reserve_construction=reserve_construction,save=context.save,
                check_continue=lambda:_check_continue(context.root,context.manifest))
        journal.verify()
        if (any(journal.count(identity,k)!=v for k,v in construction.items())
                or result['native_calls']!=budget.snapshot()['attempted']['native_calls']):
            raise ValueError('complete native/construction work differs from its saved accounting')
        return dict(result,**construction)
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())
        context.note_file(journal.path)
