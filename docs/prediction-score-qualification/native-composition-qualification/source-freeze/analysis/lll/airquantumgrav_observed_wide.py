# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately frozen ESA revision using the qualified explicit wide provider."""
from lll.airquantumgrav_inventory import environment,METADATA,validate_context
from lll.airquantumgrav_observed_height import UNCHANGED_INPUTS,tasks,require_qualification

SCOPE='observed ESA recording-187 matched wider prediction; no original or protected reads'
BASELINE_PROTOCOL_SOURCES=('airquantumgrav_prediction.py','airquantumgrav_observed.py','airquantumgrav_observed_height.py')


def recipe(*,maximum_wall_s):
    import math
    from lll.airquantumgrav_observed_height import recipe as original
    if (type(maximum_wall_s) not in (int,float) or not math.isfinite(maximum_wall_s)
            or not 0<maximum_wall_s<=28800.):
        raise ValueError('explicit finite cooperative wall allowance at most eight hours required')
    return dict(original(),version='esa-observed-wide-pilot-v1',maximum_wall_s=float(maximum_wall_s))


def qualification_sources(root):
    from lll.ilvis0_wide_observed import SOURCES
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_observed_wide.py',
        'analysis/lll/airquantumgrav_observed_wide_report.py',
        'analysis/tests/test_airquantumgrav_observed_wide.py',
        'analysis/tests/test_airquantumgrav_observed_wide_report.py',
        'analysis/tests/test_prediction_audit.py',
        'analysis/tests/test_ilvis0_wide_observed_binding.py',
        'analysis/tests/test_ilvis0_wide_observed_prediction.py',
        'analysis/tests/run_numerical.py','analysis/lll/studies/testing_after.py',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp',
        'docs/esa-observed-wide-pilot/PLAN.md',*['analysis/lll/'+name for name in SOURCES]])


def required_tests():
    return ['test_observed_wide_standalone_loader_keeps_original_matrix_and_limits',
        'test_observed_wide_requires_qualification_before_inputs',
        'test_observed_wide_requires_explicit_finite_wall_allowance',
        'test_observed_wide_rejects_unguarded_environment_before_inputs',
        'test_observed_wide_cannot_use_partial_or_unverified_training_qualification',
        'test_observed_wide_freezes_every_dynamically_bound_protocol',
        'test_observed_wide_baseline_checks_observed_protocols_not_unused_generated_wrapper',
        'test_observed_wide_report_rejects_unfinished_before_numerical_imports',
        'test_observed_wide_compilation_verifies_actual_derived_source_without_relabeled_hashes',
        'test_saved_training_fit_retains_nonconvergence_and_every_column',
        'test_saved_prediction_checks_complete_independence_and_exact_native_accounting',
        'test_saved_start_sensitivity_is_descriptive_and_retains_failed_starts',
        'test_saved_start_sensitivity_keeps_incomplete_pairs_unavailable',
        'test_saved_start_sensitivity_rejects_mismatched_queries_instead_of_truncating',
        'test_wide_observed_protocol_preserves_original_signatures_and_shared_functions',
        'test_wide_observed_binding_rejects_missing_or_changed_source_before_calculation']+[
        f'test_wide_observed_forecast_independence_inputs_columns_and_accounting[{policy}-{profile}]'
        for policy in ('reported-short-v1','reported-persistent-v1') for profile in (False,True)]


def prepare(root,*,qualification,maximum_wall_s,identity='esa-observed-wide-pilot-20261024'):
    if qualification is None:raise ValueError('source-bound observed revision qualification required')
    import json
    import re
    from pathlib import Path
    from lll.compute_budget import environment as thread_environment
    from lll.airquantumgrav_observed import _verified_report
    from lll.airquantumgrav_observed_height import verify_baseline
    from lll.ilvis0_wide_observed import SOURCES,bind
    from lll.studies.artifacts import ArchiveStore,atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    r=recipe(maximum_wall_s=maximum_wall_s);env=environment()
    if env['numerical_environment']!=thread_environment(workers=r['workers'],threads=r['threads']):
        raise ValueError('declared thread environment required')
    root=Path(root).resolve()
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('safe fresh observed revision identity required')
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh observed revision allowance required')
    sources=qualification_sources(root)
    request,tests=checked(root,qualification,sources=sources,environment=env,
        required_tests=required_tests(),minimum_tests=56)
    parent=ClosedStudy(root,'docs/esa-wide-training-controls')
    try:
        controls=_verified_report(parent);require_qualification(controls)
        for name in set(sources)&parent.manifest['sources'].keys():
            if digest((root/name).read_bytes())!=parent.manifest['sources'][name]:
                raise ValueError('qualified wider training dependency changed: '+name)
        if parent.input('qualification-environment')!=env:raise ValueError('qualified numerical environment changed')
        receipt=parent.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
        parent_binding=dict(manifest_sha256=parent.completion['manifest_sha256'],
            summary_sha256=parent.completion['summary_sha256'],report_sha256=receipt['artifacts'][name])
    finally:parent.close()
    baseline=ClosedStudy(root,'docs/esa-observed-height-pilot')
    try:
        receipt=baseline.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
        report=baseline.read(name,receipt['artifacts'][name])
        verify_baseline(report,baseline.completion,
            selector_sha256=digest((root/'analysis/lll/ilvis0_forecast_publication.py').read_bytes()))
        for name in BASELINE_PROTOCOL_SOURCES:
            path='analysis/lll/'+name
            if digest((root/path).read_bytes())!=baseline.manifest['sources'][path]:
                raise ValueError('original matched protocol changed: '+name)
        materials={key:baseline.input(key,raw=True) for key in UNCHANGED_INPUTS}
        baseline_binding=dict(manifest_sha256=baseline.completion['manifest_sha256'],
            summary_sha256=baseline.completion['summary_sha256'],report_sha256=receipt['artifacts']['artifacts/publication/verified-report.json'],
            unchanged_input_sha256={key:baseline.manifest['inputs'][key]['sha256'] for key in UNCHANGED_INPUTS})
    finally:baseline.close()
    store=ArchiveStore(root)
    try:metadata={key:store.read(name) for key,name in METADATA.items()}
    finally:store.close()
    binding=validate_context(**{key:json.loads(value) for key,value in metadata.items()})
    if binding!=json.loads(materials['context']):raise ValueError('prepared development membership changed')
    calculate,protocol=bind(expected_sources={name:digest((root/'analysis/lll'/name).read_bytes()) for name in SOURCES})
    task_list=tasks(json.loads(materials['layout']))
    materials.update(metadata)
    materials.update({key:encoded(value) for key,value in [('recipe',r),('qualified-controls',controls),
        ('qualified-parent',parent_binding),('baseline-binding',baseline_binding),('protocol-binding',protocol),
        ('qualification-environment',env)]})
    materials.update({'qualification-request':request,'qualification-report':tests})
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(materials.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    definition=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_observed_wide.py',sources=sources,
        inputs=inputs,tasks=task_list,workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+identity,total=len(task_list),limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import gzip
    import json
    import numpy as np
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_wide_tangent import load as load_tangent
    from lll.ilvis0_wide_observed import SOURCES,bind
    from lll.ilvis0_control_shards import _check_continue
    read=lambda key:json.loads(context.input_path(key).read_bytes())
    r=read('recipe');layout=read('layout');declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if (r!=recipe(maximum_wall_s=r['maximum_wall_s']) or context.manifest['scope']!=SCOPE
            or {v['identity']:v for v in tasks(layout)}.get(task['identity'])!=declared
            or read('qualification-environment')!=environment()):raise ValueError('unchanged frozen observed revision required')
    require_qualification(read('qualified-controls'))
    if read('baseline-binding')['unchanged_input_sha256']!={key:context.manifest['inputs'][key]['sha256'] for key in UNCHANGED_INPUTS}:
        raise ValueError('original prepared measurements or split changed')
    binding=validate_context(**{key:read(key) for key in METADATA})
    if binding!=read('context'):raise ValueError('explicit development membership changed')
    calculate,protocol=bind(expected_sources={name:context.manifest['sources']['analysis/lll/'+name] for name in SOURCES})
    if protocol!=read('protocol-binding'):raise ValueError('explicit wide provider differs from freeze')
    context.save('protocol-binding.json',protocol)
    with np.load(context.input_path(),allow_pickle=False) as archive:arrays={key:archive[key] for key in ('theta','dv','dt')}
    query=read('query-layout');training=json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    count=int(np.searchsorted(np.cumsum(arrays['dt']),query['times_s'][799]+r['limits']['time_offset'],side='left'))+1
    if (len(arrays['dt'])!=layout['native_packets'] or count!=layout['training_prefix_packets']
            or len(training)!=800 or len(query['times_s'])!=1200):raise ValueError('unchanged raw input and prefix required')
    context.save('input-binding.json',dict(group_id=binding['group_id'],layout=layout,
        input_sha256={key:value['sha256'] for key,value in context.manifest['inputs'].items()},original_reads=0,protected_reads=0))
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';env=environment()
    def factory(anchor):
        value,vm=load_kernel(directory,gravity_anchor_height_m=anchor)
        tangent,tm=load_tangent(directory,gravity_anchor_height_m=anchor,
            expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
        if (vm['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_native.c']
                or vm['compiler']!=env['compilers']['cc'] or tm['compiler']!=env['compilers']['c++']):
            raise ValueError('frozen native sources and compilers required')
        return value,tangent,dict(value=vm,tangent=dict(tm,gravity_model=r['gravity_model']))
    result=calculate(task['payload'],r,arrays=arrays,training_rows=training,layout=query,
        open_scoring=lambda:json.loads(gzip.decompress(context.input_path('scoring').read_bytes())),kernel_factory=factory,
        reserve=context.charge,save=context.save,check_continue=lambda:_check_continue(context.root,context.manifest))
    if result['weight_configuration']!=read('working-errors')[task['payload']['policy_id']]['configuration']:
        raise ValueError('training weights differ from prepared source')
    return dict(result,group_id=binding['group_id'])
