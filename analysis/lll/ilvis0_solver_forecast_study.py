# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated known-answer forecast comparison for bounded solvers."""

import json
from pathlib import Path

ID='ilvis0-generated-solver-forecast-v1-20261118'
PLAN='docs/prediction-group-transfer/GENERATED_SOLVER_FORECAST_PLAN.md'
REQUEST='docs/prediction-group-transfer/generated-solver-qualification-request.json'
REPORT='docs/prediction-group-transfer/generated-solver-qualification-tests.xml'
RECOVERY='docs/prediction-group-transfer/remaining-recovery-request.json'
SCOPE=('independent generated 12-second geographic controls; earlier-only '
       'six-parameter fits and eight-epoch withheld forecast; no archive data')
MODELS=('sphere_rotating','sphere_still','flat_still')
CLOCKS=('nominal','variable')
STRATEGIES=('original','verified')
STARTS=('zero','opposed')
POLICY=dict(training_epochs=16,prediction_epochs=8,tangent_sweeps=200,
            value_sweeps=2,objective_excess_limit=.01,
            maximum_cross_solver_path_spread_m=.1,
            original_reads=0,protected_reads=0)


def tasks():
    return [dict(identity=f'{model}-{clock}-{strategy}-{start}',
                 input_key='policy',
                 payload=dict(model=model,clock=clock,
                              strategy=strategy,start=start),
                 limits=dict(native_calls=202,
                             packet_visits=2400*(200*16+16+24),
                             bound_calls=0,bound_steps=0))
            for model in MODELS for clock in CLOCKS
            for strategy in STRATEGIES for start in STARTS]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_solver_forecast_study.py',
        'analysis/lll/ilvis0_solver_forecast_controls.py',
        'analysis/lll/ilvis0_geographic_controls.py',
        'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_ilvis0_solver_forecast_study.py',
        'analysis/tests/test_ilvis0_solver_forecast_controls.py',PLAN])


def required_tests():
    return ('test_training_cut_cannot_pass_later_receiver_positions_to_solver',
            'test_pair_gate_requires_all_four_stops_and_close_later_paths',
            'test_grid_has_exact_six_fixtures_four_starts_and_finite_charges',
            'test_freeze_contains_native_c_and_cpp_and_recovery_checks',
            'test_generated_evaluator_saves_path_before_scoring_and_charges_native',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=runtime_environment(),
                   output=REQUEST,report=REPORT)


def prepare(root,*,qualification):
    import shutil
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources,REQUIRED_TESTS
    root=Path(root).resolve()
    base=safe_path(root,'data/'+ID+'-inputs')
    if (base.exists() or safe_path(root,'data/'+ID).exists() or
            shutil.disk_usage(root).free<5*1024**3):
        raise ValueError('fresh study and five GiB free space required')
    env=runtime_environment()
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,RECOVERY,
        sources=qualification_sources(root),environment=env,
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    base.mkdir(parents=True)
    material=dict(policy=encoded(POLICY),qualification_request=request,
                  qualification_report=report,recovery_request=recovery,
                  recovery_report=recovery_report)
    inputs={}
    for key,raw in material.items():
        path=base/key;atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/ilvis0_solver_forecast_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(),
        workers=4,threads=1,maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,tasks=24,
                allocation=manifest['allocation'],limits=manifest['limits'])


class _ChargedTraining:
    def __init__(self,problem,context,packet_count):
        self.problem=problem;self.context=context;self.packet_count=packet_count
        self.bounds=problem.bounds

    def residual_tangent(self,point,model):
        self.context.charge(native_calls=1,
                            packet_visits=self.packet_count*16)
        return self.problem.residual_tangent(point,model)


def evaluate(task,context):
    import numpy as np
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_shape import fit_shape_candidate,load_tangent
    from .ilvis0_solver_verified_stop import fit_candidate as verified_fit
    from . import ilvis0_geographic_controls as geographic
    from .ilvis0_solver_forecast_controls import split_fixture
    policy=json.loads(context.input_path().read_bytes())
    declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if (policy!=POLICY or declared not in tasks() or
            context.manifest['scope']!=SCOPE):
        raise ValueError('unchanged finite generated control required')
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel,kernel_meta=load_kernel(directory)
    tangent,tangent_meta=load_tangent(directory)
    for name,meta in (('ilvis0_native.c',kernel_meta),
                      ('ilvis0_tangent.cpp',tangent_meta)):
        if context.manifest['sources']['analysis/lll/'+name]!=meta['source_sha256']:
            raise ValueError('compiled native source differs from freeze')
    payload=task['payload']
    fixture=geographic.fixture(payload['model'],payload['clock'])
    train,query,later_truth=split_fixture(fixture)
    packet_count=len(fixture['dt'])
    if packet_count!=2400:
        raise ValueError('unchanged 2400-packet analytic fixture required')
    train_problem=geographic.problem(train,kernel,tangent)
    counted=_ChargedTraining(train_problem,context,packet_count)
    truth=geographic.truth_point(fixture,train_problem)
    start=(np.zeros(len(truth)) if payload['start']=='zero' else
           -.8*np.sign(truth))
    solver=fit_shape_candidate if payload['strategy']=='original' else verified_fit
    fit=solver(counted,payload['model'],start=start,maximum_evaluations=200)
    context.save('fit.json',fit)
    context.charge(native_calls=1,packet_visits=packet_count*16)
    reference=train_problem.predict(truth,payload['model'])
    reference_residual=train_problem.whiten(reference-train['gps'])
    known_cost=float(reference_residual@reference_residual)
    query_problem=geographic.problem(query,kernel,tangent)
    context.charge(native_calls=1,packet_visits=packet_count*24)
    predicted=query_problem.predict(
        np.asarray(fit['normalized_parameters'],float),payload['model'])
    context.save('later-path.json',dict(coordinates=predicted[16:].tolist(),
        metric=fixture['metric'].tolist(),training_epochs=16,
        later_receiver_positions_used=False))
    error=float(np.max(np.linalg.norm(
        (predicted[16:]-later_truth)*fixture['metric'],axis=1)))
    return dict(passed=bool(fit['converged'] and
                            fit['residual_sum_squares']<=known_cost+.01),
        converged=bool(fit['converged']),
        training_cost=float(fit['residual_sum_squares']),
        known_cost=known_cost,later_truth_maximum_error_m=error,
        evaluations=fit['evaluations'],model=payload['model'],
        clock=payload['clock'],strategy=payload['strategy'],
        start=payload['start'],withheld_positions_used_in_fit=False,
        original_reads=0,protected_reads=0,scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    args=parser.parse_args(argv)
    root=Path('.').resolve()
    if args.action=='request':result=request_qualification(root)
    elif args.action=='prepare':result=prepare(root,qualification=REQUEST)
    else:
        from .ilvis0_control_shards import launch
        summary=launch(root/'data'/ID,reserved_threads=0)
        result={k:summary[k] for k in ('state','completed','total','passed','charged')}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
