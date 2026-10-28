# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite optimizer qualification using shared generated prediction components."""
import json
from pathlib import Path

IDENTITY='compensated-optimizer-qualification-20261026'
SCOPE='48 exposed-family generated optimizer controls; no calibration or original/protected inputs'
PARENT='docs/saved-point-coordinate-precision'
ARITHMETIC=('analysis/lll/ilvis0_coordinate_precision.py','analysis/lll/ilvis0_timing_arithmetic.py',
    'analysis/lll/native_tangent.py','analysis/lll/native_build.py','analysis/lll/ilvis0_tangent.cpp')


def recipe():
    return dict(version='compensated-optimizer-qualification-v1',seeds=[281474976810725,281474976810726],
        role='exposed_development_optimizer_qualification',workers=4,threads=1,maximum_wall_s=7200.,
        maximum_evaluations=200,retries=0)


def case_recipe(seed):
    from lll.prediction_calibration_study import case_recipe as original
    if type(seed) is not int or seed not in recipe()['seeds']:raise ValueError('exposed development seed required')
    return dict(original(seed),workers=4,threads=1,maximum_wall_s=7200.)


def tasks():
    from lll.structured_noisy_training import tasks as cases
    return [dict(identity=f"development-seed-{seed}-{case['identity']}",input_key='recipe',native_kind='tangent',
        payload=dict(draw_seed=seed,case=case['payload']),limits=case['limits'])
        for seed in recipe()['seeds'] for case in cases(case_recipe(seed))]


def verify_gate(report,binding,current,environment):
    if (report.get('complete')!=4 or report.get('selected')!=4 or report.get('failures')
            or report.get('candidate_checks_qualified') is not True or len(report.get('rows',[]))!=4
            or len(report.get('curves',[]))!=315
            or not all(r['repeatable'] and r['derivatives_agree'] and r['candidate_stopping_passed'] for r in report['rows'])
            or not all(0<=c['error_ratio']<=1 for c in report['curves'])
            or not binding.get('sources') or binding.get('environment')!=environment
            or any(current.get(k)!=v for k,v in binding['sources'].items())):
        raise ValueError('complete qualified unchanged arithmetic and environment required')


def qualification_sources(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    s=ClosedStudy(root,PARENT)
    try:names=set(s.manifest['sources'])
    finally:s.close()
    own=['analysis/lll/coordinate_optimizer_study.py','analysis/lll/coordinate_optimizer_report.py',
        'analysis/tests/test_coordinate_optimizer_study.py','analysis/tests/test_coordinate_optimizer_report.py',
        'analysis/tests/test_coordinate_optimizer_protocol.py','analysis/tests/test_structured_noisy_study.py',
        'docs/COMPENSATED_OPTIMIZER_PLAN.md']
    return sorted(names|set(source_closure(root,own)))


def prepare(root,*,qualification):
    if qualification is None:raise ValueError('source-bound optimizer software qualification required')
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.closed import ClosedStudy
    from lll.studies.runtime import Definition
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    from lll.timing_arithmetic_report import inspect
    from lll.stopping_consistency_study import selection
    root=Path(root).resolve();base=root/'data/ilvis0-source-point-development'/f'{IDENTITY}-inputs'
    if base.exists() or (root/'data'/IDENTITY).exists():raise ValueError('fresh finite qualification required')
    names=qualification_sources(root);env=environment();gate=inspect(root,PARENT)
    parent=ClosedStudy(root,PARENT)
    try:
        binding=dict(sources={k:parent.manifest['sources'][k] for k in ARITHMETIC},
            environment=parent.input('environment'),manifest_sha256=parent.completion['manifest_sha256'],
            summary_sha256=parent.completion['summary_sha256'])
        old=parent.manifest['sources']
    finally:parent.close()
    current={k:digest((root/k).read_bytes()) for k in names}
    verify_gate(gate,binding,current,env)
    updates={k:dict(original_sha256=v,current_sha256=current.get(k)) for k,v in old.items() if current.get(k)!=v}
    allowed={'analysis/lll/structured_noisy_study.py','analysis/tests/test_structured_noisy_study.py',
        'analysis/lll/studies/artifacts.py','analysis/lll/studies/testing.py'}
    if not set(updates)<=allowed:raise ValueError('parent scientific source changed')
    required=['test_optimizer_matrix_retains_exposed_seeds_starts_and_original_caps',
        'test_shared_case_runner_uses_explicit_provider_without_changing_default',
        'test_worker_preserves_prepayment_and_artifacts_after_failure',
        'test_optimizer_preparation_requires_qualification_before_inputs',
        'test_optimizer_report_preserves_failed_or_missing_start_pairs',
        'test_optimizer_frozen_adapter_calls_shared_runner_and_retains_failure',
        'test_optimizer_worker_rejects_changes_before_work[source]',
        'test_optimizer_worker_rejects_changes_before_work[environment]']
    required += [f'test_compensated_short_protocol[{int(p)}-{m}-{law}]'
        for p in (False,True) for m in (0,1,2) for law in ('increment','point')]
    request,report=checked(root,qualification,sources=names,environment=env,minimum_tests=30,required_tests=required)
    values=dict(recipe=encoded(recipe()),**{'qualification-environment':encoded(env),
        'qualification-request':request,'qualification-report':report,'arithmetic-gate':encoded(gate),
        'arithmetic-binding':encoded(binding),'parent-source-updates':encoded(updates),'saved-points':encoded(selection(root))})
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(values.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    r=recipe();definition=dict(id=IDENTITY,scope=SCOPE,adapter='analysis/lll/coordinate_optimizer_study.py',
        sources=names,inputs=inputs,tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+IDENTITY,allocation=m['allocation'],limits=m['limits'])


def kernels(context,env):
    from lll.ilvis0_noise_step import load as noise_load
    from lll.ilvis0_coordinate_precision import load
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    builds=Journal(directory/'builds.sqlite',freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={'worker':dict(builds=2)})
    if not builds.verify()['starts']:builds.start('worker')
    reserve=lambda:builds.reserve('worker','builds');hashes=context.manifest['sources']
    noise,nm=noise_load(directory,expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'],
        expected_bridge_sha256=hashes['analysis/lll/ilvis0_noise_bridge.cpp'],
        expected_wide_loader_sha256=hashes['analysis/lll/ilvis0_wide_tangent.py'],reserve_build=reserve)
    def factory(anchor):
        kernel,meta=load(directory,reserve_build=reserve,gravity_anchor_height_m=anchor,
            expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'])
        if nm['compiler']!=env['compilers']['c++'] or meta['compiler']!=env['compilers']['c++']:
            raise ValueError('frozen compiler required')
        builds.verify();context.save_bytes('worker-build-journal.sqlite',builds.path.read_bytes())
        return None,kernel,dict(tangent=meta,noise_bridge=nm)
    return noise,factory


def evaluate(task,context):
    from lll.airquantumgrav_inventory import environment
    from lll.studies.source_binding import verify
    from lll.studies.artifacts import encoded
    from lll.structured_noisy_study import run_case
    declared=json.loads(context.input_path('qualification-request').read_bytes())['sources']
    verify(context.root/'source-freeze',declared=declared,manifest=context.manifest['sources'])
    if (context.manifest['scope']!=SCOPE or json.loads(context.input_path().read_bytes())!=recipe()
            or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()
            or {k:v for k,v in task.items() if k not in ('index','shard')}!={t['identity']:t for t in tasks()}.get(task['identity'])):
        raise ValueError('unchanged finite optimizer identity, scope and environment required')
    gate=json.loads(context.input_path('arithmetic-gate').read_bytes())
    binding=json.loads(context.input_path('arithmetic-binding').read_bytes())
    verify_gate(gate,binding,context.manifest['sources'],environment())
    p=task['payload'];seed=p['draw_seed'];spec=p['case']
    result=run_case(task,context,r=case_recipe(seed),payload=spec,kernel_provider=kernels)
    points=json.loads(context.input_path('saved-points').read_bytes());matched=[]
    for point in points:
        if point['payload']['draw_seed']==seed and point['payload']['case']==spec:
            for name,value in point['artifacts'].items():
                if (context.directory/name).read_bytes()!=encoded(value):raise ValueError('saved input/error binding changed: '+name)
            matched.append(point['identity'])
    context.save('original-binding-replay.json',dict(matched_identities=matched,exact=True,original_labels_changed=False))
    return dict(result,draw_seed=seed,role=recipe()['role'],original_labels_changed=False,
        original_binding_replays=len(matched),confidence_calibrated=False)
