# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh generated coverage check of a wider fixed simultaneous range."""

import hashlib
import json
from pathlib import Path

from .esa_integrated_drift_v2_pilot import POLICY as CASE_POLICY
from .esa_integrated_drift_v2_validation import POLICY as EARLIER_POLICY
from .esa_nonaliased_motion_pilot import POLICY as MOTION_POLICY
from .esa_paired_vibration_control import POLICY as PAIRED_POLICY
from .studies.artifacts import encoded


ID = 'esa-generated-threshold-42-20261118'
HERE = 'docs/prediction-observed-development/threshold-42-validation'
POLICY = dict(
    version='esa-generated-threshold-42-validation-v1',
    seeds=list(range(2026112400, 2026112656)),
    generated_case_policy_sha256=hashlib.sha256(encoded(CASE_POLICY)).hexdigest(),
    duration_s=CASE_POLICY['duration_s'], rate_hz=CASE_POLICY['rate_hz'],
    training_epochs=CASE_POLICY['training_epochs'],
    forecast_epochs=CASE_POLICY['forecast_epochs'],
    maximum_imu_packets=CASE_POLICY['maximum_imu_packets'],
    simultaneous_z=4.2,
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


def evaluate(task, context):
    from .esa_motion_error_controls import make_control
    from .esa_generated_imu_propagation import propagate_generated
    from .esa_integrated_drift_v2_pilot import forecast_from_earlier, score_future

    raw = context.input_path('policy').read_bytes()
    requested = {key: value for key, value in task.items()
                 if key not in ('index', 'shard')}
    prior_seeds = (set(CASE_POLICY['seeds']) |
                   set(EARLIER_POLICY['seeds']) |
                   set(MOTION_POLICY['seeds']) |
                   set(PAIRED_POLICY['seeds']))
    if (json.loads(raw) != POLICY or requested not in tasks() or
            set(POLICY['seeds']) & prior_seeds or
            POLICY['generated_case_policy_sha256'] !=
                hashlib.sha256(encoded(CASE_POLICY)).hexdigest()):
        raise ValueError('unchanged independent generated cohort required')
    seed = task['payload']['seed']
    vibration = task['payload']['vibration']
    case = make_control(duration_s=POLICY['duration_s'],
                        rate_hz=POLICY['rate_hz'], seed=seed,
                        vibration=vibration, errors=True)
    if len(case['imu_time_s']) != POLICY['maximum_imu_packets']:
        raise ValueError('declared generated packet allowance changed')
    propagated = propagate_generated(case)
    forecast = forecast_from_earlier(propagated, CASE_POLICY)
    context.save('conditional-forecast.json', forecast)
    original_score = score_future(propagated, forecast, CASE_POLICY)
    maximum = original_score['maximum_absolute_standardized_error']
    outcome = dict(original_score)
    outcome.pop('simultaneous_95_contained')
    outcome.update(seed=seed, vibration=vibration,
                   threshold_z=POLICY['simultaneous_z'],
                   range_contained=maximum <= POLICY['simultaneous_z'],
                   validation_policy_sha256=hashlib.sha256(raw).hexdigest(),
                   generated_case_policy_sha256=
                       POLICY['generated_case_policy_sha256'])
    context.save('outcome.json', outcome)
    return dict(passed=True, technical_complete=True,
                maximum_absolute_standardized_error=maximum,
                range_contained=outcome['range_contained'],
                forecast_epochs=outcome['forecast_epochs'],
                original_reads=0, protected_reads=0, earth_model_fits=0,
                generated_coverage_qualified=False,
                scientific_decision='abstain')


def write_definition(root):
    """Seal one finite source/input/task plan before preparation."""
    from .studies.artifacts import atomic

    root = Path(root).resolve()
    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('prepared definition cannot be rewritten')
    policy_path = HERE+'/policy.json'
    definition_path = HERE+'/definition.json'
    definition = dict(id=ID,
        scope='fresh generated threshold check; no aircraft originals',
        workers=1, threads=1, maximum_wall_s=2400,
        adapter='analysis/lll/esa_threshold_42_validation.py',
        sources=[
            'analysis/lll/esa_threshold_42_validation.py',
            'analysis/lll/esa_threshold_42_report.py',
            'analysis/lll/esa_integrated_drift_v2_pilot.py',
            'analysis/lll/esa_integrated_drift_v2_validation.py',
            'analysis/lll/esa_nonaliased_motion_pilot.py',
            'analysis/lll/esa_paired_vibration_control.py',
            'analysis/lll/esa_integrated_drift_pilot.py',
            'analysis/lll/esa_motion_error_controls.py',
            'analysis/lll/esa_generated_imu_propagation.py',
            'analysis/lll/integrated_drift_v2.py',
            'analysis/lll/state_space_covariance.py',
            'analysis/lll/ilvis0_error_model.py',
            'analysis/tests/test_esa_threshold_42_validation.py',
            'analysis/tests/test_esa_threshold_42_report.py',
            'analysis/tests/test_esa_integrated_drift_v2_pilot.py',
            'analysis/tests/test_esa_integrated_drift_v2_validation.py',
            'analysis/tests/test_integrated_drift_v2.py',
            'analysis/tests/test_esa_generated_imu_propagation.py',
            HERE+'/PLAN.md'],
        inputs={'policy': policy_path}, tasks=tasks())
    for name, payload in ((policy_path, POLICY),
                          (definition_path, definition)):
        path = root/name
        content = encoded(payload)
        if path.exists():
            if path.read_bytes() != content:
                raise ValueError('existing generated freeze differs')
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
