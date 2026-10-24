# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only ESA precision comparison at two already frozen points."""
from lll.airquantumgrav_inventory import environment,METADATA,validate_context

PARENT='docs/esa-stopping-resolution'
SCOPE='ESA saved-point scalar precision diagnostic; no fits, forecasts, later or protected data'


def recipe():
    from lll.airquantumgrav_resolution import recipe as original
    r=original()
    return dict(r,version='esa-scalar-precision-v2',maximum_sweeps=4,fractions=[0.,1.],
        modes=['double-legacy','double-stable','long-double-stable'])


def tasks():
    from lll.airquantumgrav_resolution import tasks as original
    r=recipe()
    return [dict(t,native_kind='value',limits=dict(native_calls=4,packet_visits=4*r['packets']*r['epochs'],bound_calls=0,bound_steps=0))
        for t in original()]


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_precision.py',
        'analysis/lll/airquantumgrav_precision_report.py','analysis/tests/test_airquantumgrav_precision.py',
        'analysis/tests/test_airquantumgrav_precision_report.py','analysis/tests/test_ilvis0_precision_value.py',
        'analysis/lll/ilvis0_tangent.cpp','docs/esa-precision-diagnostic/PLAN.md'])


def required_tests():
    return ['test_precision_adapter_imports_under_the_standalone_worker_loader',
        'test_precision_study_has_24_identities_and_only_96_value_sweeps',
        'test_precision_prepare_requires_qualification_before_reading_inputs',
        'test_precision_prepare_rejects_unguarded_environment_before_reading_inputs',
        'test_precision_compare_interface_excludes_later_data_or_optimization',
        'test_precision_comparison_charges_before_native_and_keeps_original_labels',
        'test_precision_comparison_rejects_reference_mismatch_without_extra_calls',
        'test_precision_derivation_requires_exact_source_and_supported_precision',
        'test_precision_longitude_wrap_preserves_small_residual_and_branch_convention',
        'test_precision_extended_residual_keeps_sub_ulp_accumulated_motion',
        'test_precision_calculate_rejects_bad_mode_and_unsupported_points_before_native',
        'test_precision_report_rejects_open_study_before_numerical_audit',
        'test_precision_saved_array_audit_rejects_changed_points_labels_and_costs']+[
        f'test_precision_double_matches_frozen_tangent_values_and_legacy_residual[{p}-{m}]'
        for p in (False,True) for m in recipe()['models']]+[
        f'test_precision_training_adapter_reproduces_saved_tangent_at_both_points[{policy}-{p}-{m}]'
        for policy in recipe()['policies'] for p in (False,True) for m in recipe()['models']]


def prepare(root,*,qualification,identity='esa-precision-diagnostic-v2-20261024'):
    if qualification is None:raise ValueError('source-bound precision qualification required')
    import io
    import json
    import re
    from pathlib import Path
    from lll.compute_budget import environment as threads
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    r=recipe();env=environment()
    if env['numerical_environment']!=threads(workers=r['workers'],threads=r['threads']):
        raise ValueError('declared thread environment required')
    root=Path(root).resolve()
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
        raise ValueError('fresh safe precision study identity required')
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh precision scope required')
    names=sources(root);request,tests=checked(root,qualification,sources=names,environment=env,
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    import numpy as np
    parent=ClosedStudy(root,PARENT)
    try:
        receipt=parent.read('evidence-receipt.json');key='artifacts/publication/verified-report.json'
        report=parent.read(key,receipt['artifacts'][key])
        if (not report['verified'] or report['total']!=24 or parent.summary['completed']!=24
                or not parent.summary['passed'] or parent.input('qualification-environment')!=env):
            raise ValueError('verified closed diagnostic and unchanged environment required')
        for name in set(names)&parent.manifest['sources'].keys():
            if digest((root/name).read_bytes())!=parent.manifest['sources'][name]:
                raise ValueError('parent numerical dependency changed: '+name)
        keys={'interval','training','layout','working-errors','source-recipe','context'}|set(METADATA)
        materials={key:parent.input(key,raw=True) for key in keys};checks={}
        if validate_context(**{key:json.loads(materials[key]) for key in METADATA})!=json.loads(materials['context']):
            raise ValueError('development membership changed')
        for task in tasks():
            identity_=task['identity'];fit=parent.input('point-'+identity_,raw=True)
            if parent.tasks[identity_]['payload']!=task['payload']:raise ValueError('same source identity required')
            raw=[]
            for index in (0,2):
                data=parent.artifact(identity_,f'sweep-{index:02d}.npz',raw=True)
                with np.load(io.BytesIO(data),allow_pickle=False) as a:
                    raw.append((a['point'].copy(),a['residual'].copy()))
            if not np.array_equal(raw[0][0],json.loads(fit)['normalized_parameters']):
                raise ValueError('unchanged fitted point required')
            stream=io.BytesIO();np.savez_compressed(stream,points=np.array([a[0] for a in raw]),
                residuals=np.array([a[1] for a in raw]))
            materials['point-'+identity_]=fit;materials['reference-'+identity_]=stream.getvalue()
            checks[identity_]=dict(point_sha256=digest(fit),reference_sha256=digest(stream.getvalue()))
        proof=dict(manifest_sha256=parent.completion['manifest_sha256'],summary_sha256=parent.completion['summary_sha256'],
            report_sha256=receipt['artifacts'][key],inputs={k:digest(v) for k,v in materials.items()},identities=checks)
    finally:parent.close()
    materials.update({'recipe':encoded(r),'source-proof':encoded(proof),'qualification-environment':encoded(env),
        'qualification-request':request,'qualification-report':tests})
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(sorted(materials.items())):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_precision.py',sources=names,inputs=inputs,
        tasks=tasks(),workers=r['workers'],threads=r['threads'],maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,total=24,limits=manifest['limits'],allocation=manifest['allocation'])


def evaluate(task,context):
    import gzip
    import json
    import numpy as np
    from lll.airquantumgrav_resolution import make_problem
    from lll.ilvis0_precision_value import load,compare
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    read=lambda key:json.loads(context.input_path(key).read_bytes())
    declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if ({v['identity']:v for v in tasks()}.get(task['identity'])!=declared or read('recipe')!=recipe()
            or read('qualification-environment')!=environment() or context.manifest['scope']!=SCOPE):
        raise ValueError('unchanged finite precision scope required')
    allowed={'interval','training','layout','working-errors','source-recipe','context','recipe','source-proof',
        'qualification-environment','qualification-request','qualification-report'}|set(METADATA)|{
            prefix+t['identity'] for prefix in ('point-','reference-') for t in tasks()}
    if set(context.manifest['inputs'])!=allowed:raise ValueError('explicit training-only precision inputs required')
    proof=read('source-proof')
    if any(context.manifest['inputs'][key]['sha256']!=sha for key,sha in proof['inputs'].items()):
        raise ValueError('frozen input binding changed')
    binding=validate_context(**{key:read(key) for key in METADATA})
    if binding!=read('context'):raise ValueError('development membership changed')
    rows=json.loads(gzip.decompress(context.input_path('training').read_bytes()));layout=read('layout')
    if len(rows)!=recipe()['epochs'] or len(layout['times_s'])!=len(rows):raise ValueError('earlier800 positions required')
    with np.load(context.input_path(),allow_pickle=False) as a:arrays={k:a[k] for k in ('theta','dv','dt')}
    spec=task['payload'];problem,weights=make_problem(arrays,rows,layout,read('source-recipe'),
        **{k:spec[k] for k in ('model','profile','policy_id')},kernel=None,tangent=None)
    if weights.configuration!=read('working-errors')[spec['policy_id']]['configuration']:
        raise ValueError('parent working weights changed')
    fit=read('point-'+task['identity'])
    if fit['active_parameters']!=list(problem.bounds.active) or fit['model']!=spec['model']:
        raise ValueError('all original columns and model required')
    with np.load(context.input_path('reference-'+task['identity']),allow_pickle=False) as a:
        points=a['points'].copy();residuals=a['residuals'].copy()
    context.save('input-binding.json',dict(group_id=binding['group_id'],original_reads=0,protected_reads=0,
        later_receiver_reads=0,source_proof_sha256=digest(context.input_path('source-proof').read_bytes()),
        inputs=proof['inputs']))
    def factory(precision):
        kernel,meta=load(context.root/'shards'/f'{context.shard:03d}'/'kernels',precision=precision,
            gravity_anchor_height_m=rows[0]['height_m'],
            expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
        if meta['compiler']!=environment()['compilers']['c++']:raise ValueError('frozen compiler required')
        return kernel,meta
    return dict(compare(problem,points,source_residuals=residuals,source_converged=fit['converged'],model=spec['model'],
        kernel_factory=factory,reserve=context.charge,save=context.save,save_bytes=context.save_bytes,
        check_continue=lambda:_check_continue(context.root,context.manifest)),**spec,group_id=binding['group_id'])
