# SPDX-License-Identifier: AGPL-3.0-or-later
"""Corrected early-covariance replay for the single-pass ESA forecast."""
import json
import math
from pathlib import Path

from . import esa_conditional_forecast_v2_study as single_pass


ID='esa-conditional-forecast-development-v3-20261114'
FAILED='data/esa-conditional-forecast-development-v2-20261114'
SCOPE=single_pass.SCOPE
INPUT_KEYS=single_pass.INPUT_KEYS
REQUEST='docs/prediction-observed-development/qualification/conditional-forecast-v3-request.json'
REPORT='docs/prediction-observed-development/qualification/conditional-forecast-v3-tests.xml'


def tasks():
    return single_pass.tasks()


def replay_training_prefix(operator,saved,*,training_epochs,expected_cost,expected_logdet):
    """Replay the saved early Gaussian cost with the full operator's prefix."""
    import numpy as np
    from .ilvis0_precision_value import longitude_residual

    difference=np.asarray(saved.get('training_coordinate_difference'),dtype=float)
    if (type(training_epochs) is not int or training_epochs<2 or
            difference.shape!=(training_epochs,3) or
            not np.all(np.isfinite(difference)) or
            not math.isfinite(expected_cost) or expected_cost<0 or
            not math.isfinite(expected_logdet)):
        raise ValueError('complete finite saved early residual and reference required')
    earlier=-difference.copy();earlier[:,1]=longitude_residual(earlier[:,1])
    prefix=operator.prefix(training_epochs)
    actual_logdet=float(prefix.log_determinant)
    if (not math.isfinite(actual_logdet) or
            abs(actual_logdet-expected_logdet)>max(1e-6,1e-10*abs(expected_logdet))):
        raise ValueError('training covariance log-determinant differs')
    white=np.asarray(prefix.whiten(earlier.ravel()),dtype=float)
    cost=float(white@white)
    if (white.shape!=(3*training_epochs,) or not math.isfinite(cost) or
            abs(cost-expected_cost)>max(1e-6,1e-8*expected_cost)):
        raise ValueError('saved early whitened cost differs')
    return dict(training_epochs=training_epochs,
                residual_sum_squares=cost,
                error_log_determinant=actual_logdet,
                saved_residual_sum_squares=expected_cost,
                saved_error_log_determinant=expected_logdet,
                prefix_configuration=prefix.configuration,
                replay_passed=True)


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),single_pass.sources(root)+[
        'analysis/lll/esa_conditional_forecast_v3_study.py',
        'analysis/tests/test_esa_conditional_forecast_v3_study.py',
        'docs/prediction-observed-development/CONDITIONAL_FORECAST_V3_PLAN.md'])


def required_tests():
    return ('test_prefix_replay_uses_cost_and_logdet_not_unlike_hashes',
            'test_full_operator_prefix_replays_separate_early_operator',
            'test_corrected_study_keeps_one_early_only_task',
            'test_corrected_study_requires_new_qualification',
            'test_single_pass_conditions_only_on_saved_early_residuals',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),
        environment=require_guarded_environment(environment()),
        output=REQUEST,report=REPORT)


def prepare(root,*,qualification=None):
    if qualification is None:
        raise ValueError('new source-bound qualification required')
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root=Path(root).resolve();base=safe_path(root,'data/'+ID+'-inputs')
    if base.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh corrected conditional identity required')
    env=require_guarded_environment(environment())
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),minimum_tests=len(required_tests()))
    failed=ClosedStudy(root,FAILED)
    try:
        envelope=failed.envelope('single-pass-receiver-conditional')
        if (failed.completion['state']!='terminal' or
                failed.completion['manifest_sha256']!=
                '50dac4db79e96f360cbc2d9ec5c2c929dfd4a8b1812f14de2cd25c4e838f650a' or
                envelope['result'].get('reason')!='full operator changes sealed training prefix' or
                envelope['charged']['native_calls']!=450_000 or
                set(failed.manifest['inputs'])!=set(INPUT_KEYS)):
            raise ValueError('exact preserved single-pass prefix failure required')
        staged={key:failed.input(key,raw=True) for key in INPUT_KEYS[:11]}
        staged.update({'qualification-environment':encoded(env),
                       'qualification-request':request,'qualification-report':report})
    finally:
        failed.close()
    if set(staged)!=set(INPUT_KEYS):
        raise ValueError('exact early-only corrected input set required')
    base.mkdir(parents=True);inputs={}
    for number,key in enumerate(INPUT_KEYS):
        path=base/f'input-{number:03d}';atomic(path,staged[key])
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/esa_conditional_forecast_v3_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(),workers=1,threads=1,
        maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=1,allocation=manifest['allocation'])


def evaluate(task,context):
    prior=json.loads(context.input_path('weighted-error-operator').read_bytes())
    fit=json.loads(context.input_path('weighted-fit').read_bytes())
    saved=json.loads(context.input_path('weighted-forecast').read_bytes())
    def gate(operator,expected_configuration):
        if expected_configuration!=prior['operator_configuration']:
            raise ValueError('saved original training operator differs')
        result=replay_training_prefix(operator,saved,training_epochs=800,
            expected_cost=fit['residual_sum_squares'],
            expected_logdet=prior['error_log_determinant'])
        context.save('prefix-replay.json',result)
        return True
    return single_pass.evaluate(task,context,prefix_gate=gate)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    if args.action=='request':result=request_qualification(root)
    elif args.action=='prepare':result=prepare(root,qualification=REQUEST)
    else:
        from .ilvis0_control_shards import launch
        result=launch(root/'data'/ID,reserved_threads=0)
    print(result);return result


if __name__=='__main__':
    main()
