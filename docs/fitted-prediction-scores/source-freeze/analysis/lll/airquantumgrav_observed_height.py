# SPDX-License-Identifier: AGPL-3.0-or-later
"""Height-gravity variant of the shared, training-only ESA observed pilot."""
from lll.airquantumgrav_inventory import environment,METADATA,validate_context

SCOPE='observed ESA recording-187 matched height-gravity prediction; no original or protected reads'
UNCHANGED_INPUTS=('interval','training','scoring','query-layout','working-errors',
    'source-validation','context','layout','verified-preparation')


def recipe():
    from lll.airquantumgrav_observed import recipe as base
    return dict(base(),version='esa-observed-height-pilot-v1',gravity_model='inverse-square-height-v1',
        gravity_anchor_source='first_training_receiver_height')


def tasks(layout):
    from lll.airquantumgrav_observed import tasks as base
    return base(layout)


def require_qualification(report):
    if (report.get('verified') is not True or report.get('qualified') is not True
            or report.get('total')!=24 or report.get('passed')!=24):
        raise ValueError('complete verified and qualified 24-case height-training report required')


def verify_baseline(report,completion,*,selector_sha256):
    # The selector was frozen by the original publication, not its fit manifest.
    if (report.get('verified') is not True or report.get('total')!=24
            or report.get('manifest_sha256')!=completion['manifest_sha256']
            or report.get('summary_sha256')!=completion['summary_sha256']
            or report.get('primary_selector_source_sha256')!=selector_sha256):
        raise ValueError('verified hash-bound baseline and unchanged published selector required')


def calculate(spec,r,*,arrays,training_rows,layout,open_scoring,kernel_factory,reserve,save,check_continue):
    import math
    from lll.airquantumgrav_observed import calculate as base
    if (r.get('gravity_model')!='inverse-square-height-v1'
            or r.get('gravity_anchor_source')!='first_training_receiver_height'
            or not training_rows or len(training_rows)!=layout['training_epochs']):
        raise ValueError('declared height gravity and complete earlier observations required')
    anchor=float(training_rows[0]['height_m'])
    if not math.isfinite(anchor) or anchor<=-6371000.:raise ValueError('finite earlier gravity anchor required')
    save('gravity-binding.json',dict(gravity_model=r['gravity_model'],gravity_anchor_height_m=anchor,
        gravity_anchor_source=r['gravity_anchor_source'],predicted_midpoint_height=True,extra_parameters=0,
        later_receiver_heights_used=False))
    check_continue();kernel,tangent,compilation=kernel_factory(anchor);save('compilation.json',compilation)
    result=base(spec,r,arrays=arrays,training_rows=training_rows,layout=layout,open_scoring=open_scoring,
        kernel=kernel,tangent=tangent,reserve=reserve,save=save,check_continue=check_continue)
    return dict(result,gravity_model=r['gravity_model'],gravity_anchor_height_m=anchor,
        gravity_anchor_source=r['gravity_anchor_source'])


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_observed_height.py',
        'analysis/lll/airquantumgrav_observed_height_report.py',
        'analysis/tests/test_airquantumgrav_observed_height.py',
        'analysis/tests/test_airquantumgrav_observed_height_numeric.py',
        'analysis/tests/test_airquantumgrav_observed_height_report.py',
        'analysis/tests/test_airquantumgrav_observed_report.py',
        'analysis/tests/test_airquantumgrav_prediction.py',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp',
        'docs/esa-observed-height-pilot/PLAN.md'])


def required_tests():
    return ['test_observed_height_changes_only_declared_gravity_variant',
        'test_observed_height_requires_qualification_before_reading_inputs',
        'test_observed_height_rejects_verified_but_unqualified_parent',
        'test_observed_height_binds_selector_to_published_baseline_report',
        'test_observed_height_report_rejects_open_before_numerical_imports',
        'test_observed_height_gravity_binding_rejects_mismatched_anchor_or_mode',
        'test_height_comparison_keeps_missing_and_failed_baseline_starts',
        'test_weighted_prediction_interface_has_no_later_receiver_input']+[
        f'test_observed_height_anchor_and_forecast_ignore_later_positions[{policy}-{profile}]'
        for policy in recipe()['policies'] for profile in (False,True)]


def prepare(root,*,qualification,identity='esa-observed-height-pilot-20261023'):
    if qualification is None:raise ValueError('passing source-bound observed-height qualification required')
    import re
    import json
    from pathlib import Path
    from lll.compute_budget import environment as thread_environment
    from lll.airquantumgrav_observed import _verified_report
    from lll.studies.artifacts import ArchiveStore,atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh observed height allowance required')
    r=recipe();env=environment()
    if env['numerical_environment']!=thread_environment(workers=r['workers'],threads=r['threads']):raise ValueError('declared thread environment required')
    sources=qualification_sources(root)
    request,report=checked(root,qualification,sources=sources,environment=env,required_tests=required_tests(),minimum_tests=len(required_tests()))
    parent=ClosedStudy(root,'docs/esa-height-training-controls')
    try:
        controls=_verified_report(parent);require_qualification(controls)
        for filename in ('airquantumgrav_prediction.py','airquantumgrav_error_policy.py','ilvis0_training_forecast.py',
                'ilvis0_forecast.py','ilvis0_near_zero.py','ilvis0_shape.py','ilvis0_estimator.py','ilvis0_exploratory.py',
                'ilvis0_forward.py','ilvis0_solver_trust_v2.py','ilvis0_solver_position.py','ilvis0_solver_refinement.py',
                'ilvis0_solver_boundary.py','ilvis0_native.c','ilvis0_tangent.cpp','ilvis0_error_model.py','models.py'):
            name='analysis/lll/'+filename
            if digest((root/name).read_bytes())!=parent.manifest['sources'].get(name):raise ValueError('qualified numerical source changed: '+filename)
        if parent.input('qualification-environment')!=env:raise ValueError('qualified environment changed')
    finally:parent.close()
    original=ClosedStudy(root,'docs/esa-development-pilot')
    try:
        for filename in ('airquantumgrav_observed.py','airquantumgrav_scoring.py'):
            name='analysis/lll/'+filename
            if digest((root/name).read_bytes())!=original.manifest['sources'].get(name):
                raise ValueError('matched original calculation or selection changed: '+filename)
        receipt=original.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
        baseline=original.read(name,receipt['artifacts'][name])
        verify_baseline(baseline,original.completion,
            selector_sha256=digest((root/'analysis/lll/ilvis0_forecast_publication.py').read_bytes()))
        materials={key:original.input(key,raw=True) for key in UNCHANGED_INPUTS}
        baseline_binding=dict(manifest_sha256=original.completion['manifest_sha256'],summary_sha256=original.completion['summary_sha256'],
            unchanged_input_sha256={key:original.manifest['inputs'][key]['sha256'] for key in UNCHANGED_INPUTS})
    finally:original.close()
    store=ArchiveStore(root)
    try:metadata={key:store.read(name) for key,name in METADATA.items()}
    finally:store.close()
    binding=validate_context(**{key:json.loads(raw) for key,raw in metadata.items()})
    if binding!=json.loads(materials['context']):raise ValueError('prepared development membership changed')
    task_list=tasks(json.loads(materials['layout']))
    materials.update(metadata);materials.update({key:encoded(value) for key,value in
        [('recipe',r),('qualified-controls',controls),('qualification-environment',env),('baseline-binding',baseline_binding)]})
    materials.update({'qualification-request':request,'qualification-report':report})
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(materials.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_observed_height.py',sources=sources,inputs=inputs,
        tasks=task_list,workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,total=len(task_list),limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import gzip
    import json
    import numpy as np
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_control_shards import _check_continue
    load=lambda key:json.loads(context.input_path(key).read_bytes())
    r=recipe();layout=load('layout');declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if ({v['identity']:v for v in tasks(layout)}.get(task['identity'])!=declared or load('recipe')!=r
            or context.manifest['scope']!=SCOPE or load('qualification-environment')!=environment()):raise ValueError('unchanged qualified height task required')
    require_qualification(load('qualified-controls'))
    baseline=load('baseline-binding')
    if baseline['unchanged_input_sha256']!={key:context.manifest['inputs'][key]['sha256'] for key in UNCHANGED_INPUTS}:
        raise ValueError('original prepared measurements or split changed')
    binding=validate_context(**{key:load(key) for key in METADATA})
    if binding!=load('context'):raise ValueError('explicit development membership changed')
    with np.load(context.input_path(),allow_pickle=False) as archive:arrays={key:archive[key] for key in ('theta','dv','dt')}
    query=load('query-layout');training=json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    count=int(np.searchsorted(np.cumsum(arrays['dt']),query['times_s'][799]+r['limits']['time_offset'],side='left'))+1
    if (len(arrays['dt'])!=layout['native_packets'] or count!=layout['training_prefix_packets']
            or len(training)!=800 or len(query['times_s'])!=1200):raise ValueError('unchanged raw input and prefix required')
    context.save('input-binding.json',dict(group_id=binding['group_id'],layout=layout,
        input_sha256={key:value['sha256'] for key,value in context.manifest['inputs'].items()},original_reads=0,protected_reads=0))
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';env=environment()
    def factory(anchor):
        kernel,km=load_kernel(directory,gravity_anchor_height_m=anchor);tangent,tm=load_tangent(directory,gravity_anchor_height_m=anchor)
        for filename,meta,compiler in [('ilvis0_native.c',km,'cc'),('ilvis0_tangent.cpp',tm,'c++')]:
            if (meta['source_sha256']!=context.manifest['sources']['analysis/lll/'+filename]
                    or meta['compiler']!=env['compilers'][compiler]):raise ValueError('compiled height source differs from freeze')
        return kernel,tangent,dict(value=km,tangent=tm)
    result=calculate(task['payload'],r,arrays=arrays,training_rows=training,layout=query,
        open_scoring=lambda:json.loads(gzip.decompress(context.input_path('scoring').read_bytes())),kernel_factory=factory,
        reserve=context.charge,save=context.save,check_continue=lambda:_check_continue(context.root,context.manifest))
    if result['weight_configuration']!=load('working-errors')[task['payload']['policy_id']]['configuration']:
        raise ValueError('training weights differ from prepared source')
    return dict(result,group_id=binding['group_id'])
