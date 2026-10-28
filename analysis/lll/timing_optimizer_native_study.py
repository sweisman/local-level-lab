# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four original-start regressions through shared generated prediction components."""
import json
import math
from pathlib import Path
from contextlib import contextmanager

IDENTITY='timing-optimizer-regression-20261027'
PLAN='docs/TIMING_OPTIMIZER_NATIVE_PLAN.md'
SCOPE='four exposed original-start timing-aware optimizer regressions; no calibration, original or protected data'
GATE='docs/timing-stopping-qualification'
GATE_MANIFEST='8b7b952d4aecde84351d5ab8e04457af3fa11460179a7a34005926f1f2a4fd05'
GATE_SUMMARY='9e81958e32c932328e37d58b82e1ed011fb82a79c27e637fb760e8b8fd5c4f58'
PARENT='docs/saved-timing-cell-native'
PARENT_MANIFEST='d114851a6630a3127dc0d033e98ea64b51c2e2ab8af818f9acebd54967f53eb1'
PARENT_SUMMARY='2e08bd09271f7717efccaa226f00797a41eb2f8a45f66bbf1a2f463348ed5251'
SEEDS=(281474977010692,281474977010693)
ORIGINAL_POPULATION='61b5a76d0eb4adaf14cb217fa400339bcd7e21f0c22e9d92b82625202b63f828'
NUMERICAL=tuple('analysis/lll/'+n+'.py' for n in ('timing_cells','timing_intervals','ilvis0_timing_stop',
    'ilvis0_solver_trust_v2','ilvis0_near_zero','ilvis0_solver_position','ilvis0_solver_refinement'))
ADAPTERS=('analysis/lll/structured_noisy_training.py','analysis/lll/structured_noisy_study.py',
    'analysis/lll/ilvis0_training_forecast.py','analysis/tests/test_timing_cells.py')


def configuration():
    return dict(id=IDENTITY,scope=SCOPE,workers=4,threads=1,maximum_wall_s=3600.,
        maximum_evaluations=200,linear_solves_per_fit=620,retries=0,maximum_fits=4,
        conditional_accuracy_diagnostic_only=True)


def reference_count(policy):
    count=getattr(policy,'expected_point_count',4)
    if type(count) is not int or count<1:
        raise ValueError('explicit positive original-reference count required')
    return count


def case_recipe(seed):
    from lll.compensated_prediction_release import case_recipe as original
    if type(seed) is not int or seed not in SEEDS:raise ValueError('original exposed regression seed required')
    return original(seed)


def tasks():
    from lll.structured_noisy_training import tasks as matrix
    rows=[]
    for seed in SEEDS:
        for t in matrix(case_recipe(seed)):
            p=t['payload']
            if p['law']=='point' and p['model']=='sphere_rotating' and p['profile'] is True:
                rows.append(dict(identity=f"timing-seed-{seed}-point-sphere_rotating-1-{p['start']}",
                    input_key='points',native_kind='tangent',payload=dict(draw_seed=seed,case=p),limits=t['limits']))
    return rows


def computational_payload(original,*,population=ORIGINAL_POPULATION):
    if (set(original)!={'draw_seed','case','population_sha256','role'} or original['role']!='calibration'
            or original['population_sha256']!=population):
        raise ValueError('unchanged original calibration provenance required')
    return {k:original[k] for k in ('draw_seed','case')}


def verify_gate(report,binding,current,environment,*,expected=None):
    expected=(dict(complete=40,fit_passed=32,pairs=8,manifest_sha256=GATE_MANIFEST,
        summary_sha256=GATE_SUMMARY) if expected is None else expected)
    if (report.get('verified') is not True or report.get('analytical_qualified') is not True
            or report.get('complete')!=expected['complete'] or report.get('fit_passed')!=expected['fit_passed'] or report.get('controls_correct')!=8
            or report.get('failures') or len(report.get('pairs',[]))!=expected['pairs']
            or not all(p['agreement'] for p in report['pairs'])
            or report.get('manifest_sha256')!=expected['manifest_sha256'] or report.get('summary_sha256')!=expected['summary_sha256']
            or set(binding.get('sources',{}))!=set(NUMERICAL) or binding.get('environment')!=environment
            or any(current.get(k)!=v for k,v in binding['sources'].items())):
        raise ValueError('complete unchanged analytical qualification and numerical environment required')


def protocol(context,*,reserve_linear,check_continue,raw=None,expected_sha256=None):
    from lll.studies.protocols import bind_function
    from lll.ilvis0_training_forecast import fit_training
    from lll.ilvis0_timing_stop import fit_candidate
    name='analysis/lll/airquantumgrav_prediction.py';own='analysis/lll/timing_optimizer_native_study.py'
    if raw is None:raw=(context.root/'source-freeze'/name).read_bytes()
    expected=context.manifest['sources'][name]
    if expected_sha256 is not None and expected_sha256!=expected:raise ValueError('frozen training protocol required')
    def solver(*args,**kwargs):
        fit=fit_candidate(*args,**kwargs,reserve_linear=reserve_linear,check_continue=check_continue)
        ordinary=dict(fit['stability_policy'])
        fit.update(ordinary_stability_policy=ordinary,stability_policy=dict(ordinary,
            stopping='all feasible local timing cells; original cost/stationarity/physical limits',
            final_verification_reserve=36,near_zero_policy_unchanged=True))
        return fit
    def training(problem,model,**kwargs):
        if kwargs.get('stopping')!='near_zero' or kwargs.get('maximum_evaluations')!=200:
            raise ValueError('original stopping composition and total fit allowance required')
        return fit_training(problem,model,**kwargs,solver_provider=solver)
    bound,proof=bind_function(raw,expected_sha256=expected,function='train_and_forecast',
        import_module='lll.ilvis0_training_forecast',import_name='fit_training',provider=training,
        provider_source_sha256=context.manifest['sources'][own],namespace=dict(math=math))
    context.save('protocol-binding.json',proof);return bound


def selection(root):
    from lll.studies.closed import ClosedStudy
    s=ClosedStudy(root,PARENT)
    try:
        if s.completion['manifest_sha256']!=PARENT_MANIFEST or s.completion['summary_sha256']!=PARENT_SUMMARY:
            raise ValueError('original four-point input source required')
        points=s.input('points')
        if (len(points)!=4 or [computational_payload(p['payload']) for p in points]!=[t['payload'] for t in tasks()]
                or [p['saved_converged'] for p in points]!=[True,True,False,False]):
            raise ValueError('all original controls and failures in original order required')
        return points,s.manifest['sources']
    finally:s.close()


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/timing_optimizer_native_study.py','analysis/lll/timing_optimizer_native_report.py',
        'analysis/tests/test_timing_optimizer_native_study.py','analysis/tests/test_timing_optimizer_native_report.py',
        'analysis/tests/test_timing_native_providers.py','analysis/tests/test_structured_noisy_study.py',
        'analysis/tests/test_ilvis0_timing_stop.py','analysis/tests/test_timing_optimizer_hooks.py',
        'analysis/tests/test_timing_intervals.py','analysis/tests/test_timing_cells.py',
        'analysis/tests/test_ilvis0_solver_trust_v2.py','analysis/tests/test_ilvis0_near_zero.py',PLAN])


def prepare(root,*,qualification,definition=None):
    if qualification is None:raise ValueError('source-bound native regression qualification required')
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded,atomic
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    import sys
    policy=sys.modules[__name__] if definition is None else definition
    root=Path(root).resolve();names=policy.sources(root);env=environment();gate=policy.gate_report(root)
    s=ClosedStudy(root,policy.GATE)
    try:binding=dict(sources={k:s.manifest['sources'][k] for k in NUMERICAL},
        environment=s.input(getattr(policy,'gate_environment_input','environment')))
    finally:s.close()
    current={k:digest((root/k).read_bytes()) for k in names};policy.verify_gate(gate,binding,current,env)
    points,parent_sources=getattr(policy,'selection',selection)(root)
    changes={k:dict(original_sha256=v,current_sha256=current[k]) for k,v in parent_sources.items()
        if k in current and current[k]!=v}
    if not set(changes)<=set(getattr(policy,'allowed_source_updates',NUMERICAL+ADAPTERS)):
        raise ValueError('original physical/noise or other source changed')
    request,report=checked(root,qualification,sources=names,environment=env,minimum_tests=100,required_tests=[
        'test_timing_native_definition_is_four_original_cases_with_unexpanded_shared_caps',
        'test_timing_native_gate_rejects_changed_or_incomplete_analytical_evidence[source]',
        'test_timing_native_bound_protocol_keeps_original_start_and_failed_fit',
        'test_shared_case_explicit_training_provider_preserves_default_and_budget[True]',
        'test_training_protocol_provider_keeps_truth_guard_and_original_default[True]',
        'test_counted_training_solver_provider_preserves_full_native_charge[True-near_zero]']
        +getattr(policy,'required_tests',[]))
    base=root/'data/ilvis0-source-point-development'/f'{policy.IDENTITY}-inputs'
    if base.exists() or (root/'data'/policy.IDENTITY).exists():raise ValueError('fresh separate native allowance required')
    values=dict(configuration=encoded(policy.configuration()),points=encoded(points),
        **{'qualification-environment':encoded(env),'qualification-request':request,'qualification-report':report,
            'analytical-gate':encoded(gate),'analytical-binding':encoded(binding),'parent-source-updates':encoded(changes)})
    base.mkdir(parents=True);inputs={}
    for i,(name,raw) in enumerate(values.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[name]=str(path.relative_to(root))
    definition=dict(id=policy.IDENTITY,scope=policy.SCOPE,adapter=policy.ADAPTER if definition is not None else 'analysis/lll/timing_optimizer_native_study.py',sources=names,
        inputs=inputs,tasks=policy.tasks(),workers=4,threads=1,maximum_wall_s=policy.configuration()['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+policy.IDENTITY,allocation=m['allocation'],limits=m['limits'])


def gate_report(root):
    from lll.timing_stopping_report import inspect
    return inspect(root,GATE)


def evaluate(task,context):
    return run_task(task,context)


@contextmanager
def timing_case_context(task,context):
    """Shared counted solver scope; validate work before scoring a case."""
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll.ilvis0_control_shards import _check_continue
    identity=task['identity'];journal=Journal(context.directory/'timing-linear.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={identity:dict(linear_solves=620)})
    journal.start(identity);check=lambda:_check_continue(context.root,context.manifest)
    def reserve():check();journal.reserve(identity,'linear_solves')
    try:
        yield dict(training_provider=protocol(context,reserve_linear=reserve,check_continue=check))
        journal.verify();fit=json.loads((context.directory/'fit.json').read_bytes())
        if fit['linear_solves']!=journal.count(identity,'linear_solves'):
            raise ValueError('linear solve accounting differs')
    finally:context.note_file(journal.path)


def run_task(task,context,*,definition=None):
    from types import SimpleNamespace
    policy=(SimpleNamespace(SCOPE=SCOPE,configuration=configuration,tasks=tasks,verify_gate=verify_gate)
        if definition is None else definition)
    if context.manifest['scope']!=policy.SCOPE:raise ValueError('exact four-regression scope required')
    from lll.studies.source_binding import verify
    from lll.studies.artifacts import encoded
    from lll.airquantumgrav_inventory import environment
    from lll.structured_noisy_study import run_case
    from lll.coordinate_optimizer_study import kernels
    declared=json.loads(context.input_path('qualification-request').read_bytes())['sources']
    verify(context.root/'source-freeze',declared=declared,manifest=context.manifest['sources'])
    if (json.loads(context.input_path('configuration').read_bytes())!=policy.configuration()
            or json.loads(context.input_path('qualification-environment').read_bytes())!=environment()
            or {k:v for k,v in task.items() if k not in ('index','shard')}!={t['identity']:t for t in policy.tasks()}.get(task['identity'])):
        raise ValueError('exact frozen cases, environment and native allowance required')
    policy.verify_gate(json.loads(context.input_path('analytical-gate').read_bytes()),
        json.loads(context.input_path('analytical-binding').read_bytes()),context.manifest['sources'],environment())
    points=json.loads(context.input_path('points').read_bytes())
    matches=[p for p in points if getattr(policy,'computational_payload',computational_payload)(p['payload'])==task['payload']]
    required=getattr(policy,'require_original_match',True)
    if len(points)!=reference_count(policy) or len(matches)>1 or required and len(matches)!=1:
        raise ValueError('original regression input binding required')
    with timing_case_context(task,context) as options:
        result=run_case(task,context,r=getattr(policy,'case_recipe',case_recipe)(task['payload']['draw_seed']),payload=task['payload']['case'],
            kernel_provider=kernels,**options)
        for old in matches:
            for name,value in old['artifacts'].items():
                if (context.directory/name).read_bytes()!=encoded(value):raise ValueError('original input/error binding changed: '+name)
        replay=dict(exact=True,original_identity=matches[0]['identity'] if matches else None,
            original_fit_converged=matches[0]['saved_converged'] if matches else None,original_labels_changed=False)
        if not required:replay['matched_identities']=[p['identity'] for p in matches]
        context.save('original-binding-replay.json',replay)
        return dict(result,original_labels_changed=False,original_binding_replays=len(matches),confidence_calibrated=False)
