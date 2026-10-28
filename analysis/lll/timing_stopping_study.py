# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small definitions and evaluator for finite analytical optimizer qualification."""
import json
from pathlib import Path

IDENTITY='timing-stopping-qualification-20261027'
PLAN='docs/TIMING_STOPPING_PLAN.md'
SCOPE='32 analytical optimizer fits and eight direct controls; zero native, original or protected observations'


def configuration():
    return dict(id=IDENTITY,scope=SCOPE,workers=1,threads=1,maximum_wall_s=600.,
        fit_evaluations=200,probe_evaluations=36,maximum_analytical_evaluations=6688,
        maximum_linear_solves=20000,linear_iterations=100,maximum_fits=32,maximum_probes=8)


def case_table(fit_cases=None):
    from lll.ilvis0_timing_controls import FIT_CASES,PROBES,fit_reference,starts,probe_reference
    rows=[]
    for name in FIT_CASES if fit_cases is None else fit_cases:
        reference=fit_reference(name)
        for index,start in enumerate(starts(len(reference['optimum']))):
            rows.append(dict(identity=f'fit-{name}-start-{index}',kind='fit',case=name,start=start,
                start_index=index,reference=reference))
    for name in PROBES:rows.append(dict(identity='probe-'+name,kind='probe',case=name,reference=probe_reference(name)))
    return rows


def work_limits(row):
    return dict(evaluations=200 if row['kind']=='fit' else 36,
        linear_solves=620 if row['kind']=='fit' else 0 if row['case']=='budget_failure' else 17)


def tasks(cases=None):
    from lll.studies.artifacts import digest,encoded
    return [dict(identity=r['identity'],input_key='cases',native_kind='tangent',
        payload=dict(case_index=i,case_sha256=digest(encoded(r))),
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)) for i,r in enumerate(case_table() if cases is None else cases)]


def fit_metrics(row,fit):
    import numpy as np
    ref=row['reference'];p=np.asarray(fit['normalized_parameters'],float)
    r=np.asarray(fit['local_linearization']['residual'],float);target=np.asarray(ref['residual'],float)
    if (p.shape!=(len(ref['optimum']),) or r.shape!=target.shape
            or not np.all(np.isfinite(p)) or not np.all(np.isfinite(r))):raise ValueError('complete finite fit required')
    cost=float(r@r);objective_error=abs(cost-ref['cost']);prediction_error=float(np.linalg.norm(r-target))
    parameter_error=float(np.max(abs(p-np.asarray(ref['optimum'])))) if ref['unique'] else None
    passed=bool(fit['converged'] and fit['stability_verified'] and np.all(abs(p)<=1)
        and cost==fit['residual_sum_squares'] and objective_error<=ref['objective_tolerance']
        and prediction_error<=ref['prediction_tolerance']
        and (not ref['unique'] or parameter_error<=ref['parameter_tolerance']))
    return dict(passed=passed,objective_error=objective_error,prediction_error=prediction_error,
        identifiable_parameter_error=parameter_error)


def run_case(row,*,reserve_evaluation,reserve_linear,save_evaluation,check_continue):
    import numpy as np
    from lll import ilvis0_timing_controls as controls
    from lll.ilvis0_timing_stop import fit_candidate,verify
    from lll.timing_intervals import local_cells
    original=controls.problem_for(row['case']);calls=0;solves=0;budget_attempted=False
    class Counted:
        def __getattr__(self,key):return getattr(original,key)
        def residual_tangent(self,u,model):
            nonlocal calls
            check_continue();reserve_evaluation();calls+=1
            r,j,b=original.residual_tangent(u,model)
            save_evaluation(dict(number=calls,point=np.asarray(u,float).tolist(),residual=r.tolist(),jacobian=j.tolist(),boundaries=b))
            return r,j,b
    def linear():
        nonlocal solves,budget_attempted
        check_continue();budget_attempted=True;reserve_linear();solves+=1
    def physical(delta):
        scale=row['reference'].get('physical_scale',1.)
        return np.c_[np.asarray(delta)*scale,np.zeros((len(delta),2))]
    counted=Counted();result=dict(identity=row['identity'],kind=row['kind'],case=row['case'],native_calls=0,
        confidence_calibrated=False,scientific_decision='abstain')
    if row['kind']=='fit':
        fit=fit_candidate(counted,'control',start=row['start'],maximum_evaluations=200,
            physical_step=physical,reserve_linear=linear,check_continue=check_continue)
        if fit['evaluations']!=calls or fit['linear_solves']!=solves:raise ValueError('fit accounting differs')
        result.update(fit=fit,**fit_metrics(row,fit))
    else:
        ref=row['reference'];point=np.asarray(ref['point'],float);r,j,_=counted.residual_tangent(point,'control')
        g=local_cells(counted.dt,counted.gps_times,scale=counted.bounds.limits['time_offset'],point=float(point[0]))
        def fresh(u,*,fresh=False):
            if not fresh:raise ValueError('fresh direct verification required')
            return counted.residual_tangent(u,'control')
        try:
            probe=verify(point,r,j,fresh,physical,active=counted.bounds.active,cells=g['cells'],
                reserve_linear=linear,check_continue=check_continue)
            rejected=False
        except ValueError as error:
            if not (ref['expected_budget_rejection'] and budget_attempted and solves==0
                    and str(error)=='frozen resource allowance exceeded'):raise
            probe=dict(passed=False,reason='budget_exhausted_before_solve');rejected=True
        evidence=(any(c.get('cost_stable') is False for c in probe.get('cells',[]))
            if row['case'] in ('ramp_zero','ramp_shifted') else
            any(c.get('position_stable') is False for c in probe.get('cells',[]))
            if row['case']=='physical_failure' else
            len(probe.get('cells',[]))==len(g['cells']) if ref['expected_acceptance'] else True)
        result.update(passed=bool(probe['passed'] is ref['expected_acceptance'] and evidence
            and rejected is ref['expected_budget_rejection'] and probe['reason']==ref['expected_reason']),probe=probe,geometry=g,
            expected_acceptance=ref['expected_acceptance'],budget_rejected=rejected)
    return dict(result,evaluations=calls,linear_solves=solves)


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/timing_stopping_study.py','analysis/lll/timing_stopping_report.py',
        'analysis/tests/test_timing_stopping_study.py','analysis/tests/test_timing_stopping_report.py',
        'analysis/tests/test_ilvis0_timing_stop.py','analysis/tests/test_timing_optimizer_hooks.py',
        'analysis/tests/test_timing_intervals.py','analysis/tests/test_timing_cells.py',
        'analysis/tests/test_ilvis0_solver_trust_v2.py','analysis/tests/test_ilvis0_near_zero.py',PLAN])


def prepare(root,*,qualification,definition=None):
    if qualification is None:raise ValueError('source-bound software qualification required')
    from lll.studies.qualification import checked
    from lll.studies.artifacts import atomic,encoded
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    import sys
    policy=sys.modules[__name__] if definition is None else definition
    root=Path(root).resolve();env=environment();names=policy.sources(root)
    request,tests=checked(root,qualification,sources=names,environment=env,minimum_tests=100,
        required_tests=['test_timing_runner_reserves_before_each_residual_and_preserves_all_evidence',
            'test_timing_direct_budget_control_really_rejects_before_linear_work',
            'test_timing_verifier_rejects_nonminimum_even_if_one_side_looks_stable',
            'test_core_linear_reservations_precede_every_actual_solve',
            'test_frozen_timing_adapter_enumerates_exact_controls_without_package_context',
            'test_timing_geometry_rejects_unsupported_inputs_or_too_many_cells[overflow]'])
    base=root/'data/ilvis0-source-point-development'/f'{policy.IDENTITY}-inputs'
    if base.exists() or (root/'data'/policy.IDENTITY).exists():raise ValueError('fresh separate analytical qualification required')
    values=dict(cases=encoded(policy.case_table()),configuration=encoded(policy.configuration()),environment=encoded(env),
        **{'qualification-request':request,'qualification-report':tests})
    base.mkdir(parents=True);inputs={}
    for i,(name,raw) in enumerate(values.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[name]=str(path.relative_to(root))
    definition=dict(id=policy.IDENTITY,scope=policy.SCOPE,adapter=policy.ADAPTER if definition is not None else 'analysis/lll/timing_stopping_study.py',sources=names,
        inputs=inputs,tasks=policy.tasks(),workers=1,threads=1,maximum_wall_s=600.)
    atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+policy.IDENTITY,allocation=m['allocation'],limits=m['limits'])


def evaluate(work,context):
    return run_task(work,context,scope=SCOPE,configuration=configuration(),cases=case_table(),tasks=tasks())


def run_task(work,context,*,scope,configuration,cases,tasks):
    if context.manifest['scope']!=scope:raise ValueError('exact analytical qualification scope required')
    import os
    from lll.studies.artifacts import digest,encoded
    from lll.studies.source_binding import verify
    from lll.studies.journal import Journal
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import _check_continue
    declared=json.loads(context.input_path('qualification-request').read_bytes())['sources']
    verify(context.root/'source-freeze',declared=declared,manifest=context.manifest['sources'])
    rows=json.loads(context.input_path('cases').read_bytes());index=work['payload']['case_index']
    if (json.loads(context.input_path('configuration').read_bytes())!=configuration
            or json.loads(context.input_path('environment').read_bytes())!=environment() or rows!=cases
            or type(index) is not int or not 0<=index<len(cases)
            or {k:v for k,v in work.items() if k not in ('index','shard')}!=tasks[index]):
        raise ValueError('exact analytical table, environment and zero-native tasks required')
    row=rows[index];identity=work['identity'];journal=Journal(context.directory/'analytical-work.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={identity:work_limits(row)})
    journal.start(identity);check=lambda:_check_continue(context.root,context.manifest)
    trace=context.directory/'values.jsonl'
    def save_value(value):
        with trace.open('ab') as stream:stream.write(encoded(value));stream.flush();os.fsync(stream.fileno())
    try:
        result=run_case(row,reserve_evaluation=lambda:journal.reserve(identity,'evaluations'),
            reserve_linear=lambda:journal.reserve(identity,'linear_solves'),save_evaluation=save_value,check_continue=check)
        journal.verify()
        if any(journal.count(identity,key)!=result[key] for key in ('evaluations','linear_solves')):
            raise ValueError('analytical work accounting differs')
        context.save('control.json',result);return result
    finally:
        context.note_file(journal.path)
        if trace.exists():context.note_file(trace)
