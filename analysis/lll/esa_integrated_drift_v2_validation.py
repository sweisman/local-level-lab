# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent generated coverage check for the frozen changing-drift law."""

import hashlib
import json
from pathlib import Path

from .esa_integrated_drift_v2_pilot import POLICY as CASE_POLICY
from .studies.artifacts import encoded


ID = 'esa-generated-integrated-drift-v2-validation-20261117'
HERE = 'docs/prediction-observed-development/integrated-drift-v2-validation'
POLICY = dict(version='esa-generated-integrated-drift-v2-validation-v1',
    seeds=list(range(2026111800, 2026112056)),
    generated_case_policy_sha256=hashlib.sha256(encoded(CASE_POLICY)).hexdigest(),
    duration_s=CASE_POLICY['duration_s'], rate_hz=CASE_POLICY['rate_hz'],
    training_epochs=CASE_POLICY['training_epochs'],
    forecast_epochs=CASE_POLICY['forecast_epochs'],
    maximum_imu_packets=CASE_POLICY['maximum_imu_packets'],
    simultaneous_95_z=CASE_POLICY['simultaneous_95_z'],
    stratum_histories=128, maximum_stratum_failures=1,
    one_sided_alpha_per_stratum=.025,
    maximum_joint_failure_probability=.05,
    original_reads=0, protected_reads=0, earth_model_fits=0,
    scientific_decision='abstain')


def tasks():
    return [dict(identity=f'seed-{seed}', input_key='policy',
                 payload=dict(seed=seed, vibration=(seed % 2 == 0)),
                 native_kind='value',
                 limits=dict(native_calls=0, packet_visits=0,
                             bound_calls=0, bound_steps=0))
            for seed in POLICY['seeds']]


def failure_upper_bound(failures, count, alpha):
    """Exact one-sided binomial upper probability after whole-history counts."""
    from scipy.stats import beta
    if (type(failures) is not int or type(count) is not int or
            not 0 <= failures <= count or count < 1 or
            isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or
            not 0 < alpha < 1):
        raise ValueError('finite whole-history counts and confidence required')
    if failures == count:
        return 1.
    return float(beta.ppf(1-alpha, failures+1, count-failures))


def evaluate(task, context):
    from .esa_motion_error_controls import make_control
    from .esa_generated_imu_propagation import propagate_generated
    from .esa_integrated_drift_v2_pilot import (
        forecast_from_earlier, score_future)
    raw = context.input_path('policy').read_bytes()
    policy = json.loads(raw)
    requested = {key: value for key, value in task.items()
                 if key not in ('index', 'shard')}
    if (policy != POLICY or requested not in tasks() or
            policy['generated_case_policy_sha256'] !=
                hashlib.sha256(encoded(CASE_POLICY)).hexdigest() or
            set(policy['seeds']) & set(CASE_POLICY['seeds'])):
        raise ValueError('unchanged independent generated cohort required')
    case = make_control(duration_s=policy['duration_s'],
                        rate_hz=policy['rate_hz'],
                        seed=task['payload']['seed'],
                        vibration=task['payload']['vibration'], errors=True)
    if len(case['imu_time_s']) != policy['maximum_imu_packets']:
        raise ValueError('declared generated packet allowance changed')
    propagated = propagate_generated(case)
    forecast = forecast_from_earlier(propagated, CASE_POLICY)
    context.save('conditional-forecast.json', forecast)
    outcome = score_future(propagated, forecast, CASE_POLICY)
    outcome.update(seed=task['payload']['seed'],
                   vibration=task['payload']['vibration'],
                   validation_policy_sha256=hashlib.sha256(raw).hexdigest(),
                   generated_case_policy_sha256=
                       policy['generated_case_policy_sha256'])
    context.save('outcome.json', outcome)
    return dict(passed=True, technical_complete=True,
                maximum_absolute_standardized_error=outcome[
                    'maximum_absolute_standardized_error'],
                simultaneous_95_contained=outcome['simultaneous_95_contained'],
                forecast_epochs=outcome['forecast_epochs'],
                original_reads=0, protected_reads=0, earth_model_fits=0,
                generated_coverage_qualified=False,
                scientific_decision='abstain')


def write_definition(root):
    """Write the single finite study definition before preparation."""
    from .studies.artifacts import atomic
    root = Path(root).resolve()
    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('prepared study definition cannot be rewritten')
    policy_path = HERE+'/policy.json'
    definition_path = HERE+'/definition.json'
    definition = dict(id=ID,
        scope='independent generated coverage check; no aircraft originals',
        workers=1, threads=1, maximum_wall_s=2400,
        adapter='analysis/lll/esa_integrated_drift_v2_validation.py',
        sources=[
            'analysis/lll/esa_integrated_drift_v2_validation.py',
            'analysis/lll/esa_integrated_drift_v2_pilot.py',
            'analysis/lll/esa_integrated_drift_pilot.py',
            'analysis/lll/esa_motion_error_controls.py',
            'analysis/lll/esa_generated_imu_propagation.py',
            'analysis/lll/integrated_drift_v2.py',
            'analysis/lll/state_space_covariance.py',
            'analysis/lll/ilvis0_error_model.py',
            'analysis/tests/test_esa_integrated_drift_v2_validation.py',
            'analysis/tests/test_esa_integrated_drift_v2_pilot.py',
            'analysis/tests/test_integrated_drift_v2.py',
            'analysis/tests/test_esa_generated_imu_propagation.py'],
        inputs={'policy': policy_path}, tasks=tasks())
    for name, payload in ((policy_path, POLICY),
                          (definition_path, definition)):
        path = root/name
        content = encoded(payload)
        if path.exists():
            if path.read_bytes() != content:
                raise ValueError('existing generated validation freeze differs')
        else:
            atomic(path, content)
    return definition_path


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('define',))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    print(write_definition(args.root))


if __name__ == '__main__':
    main()
