# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh-seed matched-noise generated vibration diagnostic."""

import hashlib
import json
from pathlib import Path

from .esa_integrated_drift_v2_pilot import POLICY as CASE_POLICY
from .studies.artifacts import encoded


ID = 'esa-generated-paired-vibration-20261118'
HERE = 'docs/prediction-observed-development/paired-vibration-control'
POLICY = dict(version='esa-generated-paired-vibration-v1',
    seeds=list(range(2026112100, 2026112116)),
    generated_case_policy_sha256=hashlib.sha256(encoded(CASE_POLICY)).hexdigest(),
    duration_s=CASE_POLICY['duration_s'], rate_hz=CASE_POLICY['rate_hz'],
    maximum_imu_packets_per_pair=2*CASE_POLICY['maximum_imu_packets'],
    maximum_receiver_reports_per_pair=2*CASE_POLICY['total_epochs'],
    simultaneous_95_z=CASE_POLICY['simultaneous_95_z'],
    original_reads=0, protected_reads=0, earth_model_fits=0,
    generated_coverage_qualified=False, scientific_decision='abstain')

ERROR_KEYS = ('gyro_white_rads', 'force_white_mps2', 'gyro_bias_rads',
              'force_bias_mps2', 'coupled_gyro_rads',
              'coupled_force_mps2', 'receiver_error_neu_m')


def tasks():
    return [dict(identity=f'seed-{seed}', input_key='policy',
                 payload=dict(seed=seed), native_kind='value',
                 limits=dict(native_calls=0, packet_visits=0,
                             bound_calls=0, bound_steps=0))
            for seed in POLICY['seeds']]


def evaluate(task, context):
    import numpy as np
    from .esa_motion_error_controls import make_control
    from .esa_generated_imu_propagation import propagate_generated
    from .esa_integrated_drift_v2_pilot import (
        forecast_from_earlier, score_future)

    raw = context.input_path('policy').read_bytes()
    requested = {key: value for key, value in task.items()
                 if key not in ('index', 'shard')}
    if (json.loads(raw) != POLICY or requested not in tasks() or
            POLICY['generated_case_policy_sha256'] !=
                hashlib.sha256(encoded(CASE_POLICY)).hexdigest() or
            set(POLICY['seeds']) & set(CASE_POLICY['seeds'])):
        raise ValueError('unchanged fresh paired generated policy required')
    seed = task['payload']['seed']
    cases = [make_control(duration_s=POLICY['duration_s'],
                          rate_hz=POLICY['rate_hz'], seed=seed,
                          vibration=vibration, errors=True)
             for vibration in (False, True)]
    if (sum(len(case['imu_time_s']) for case in cases) !=
            POLICY['maximum_imu_packets_per_pair'] or
            sum(len(case['receiver_time_s']) for case in cases) !=
            POLICY['maximum_receiver_reports_per_pair'] or
            any(not np.array_equal(cases[0][key], cases[1][key])
                for key in ERROR_KEYS) or
            np.array_equal(cases[0]['truth_gyro_body_rads'],
                           cases[1]['truth_gyro_body_rads'])):
        raise ValueError('complete matched-noise distinct-motion pair required')
    propagated = [propagate_generated(case) for case in cases]
    forecasts = [forecast_from_earlier(item, CASE_POLICY)
                 for item in propagated]
    context.save('forecasts.json', forecasts)
    scores = [score_future(item, forecast, CASE_POLICY)
              for item, forecast in zip(propagated, forecasts, strict=True)]
    outcomes = [dict(vibration=vibration, **score)
                for vibration, score in zip((False, True), scores, strict=True)]
    context.save('outcomes.json', dict(seed=seed,
        policy_sha256=hashlib.sha256(raw).hexdigest(),
        generated_case_policy_sha256=POLICY['generated_case_policy_sha256'],
        matched_error_draws=True, outcomes=outcomes,
        original_reads=0, protected_reads=0, earth_model_fits=0,
        generated_coverage_qualified=False,
        scientific_decision='abstain'))
    return dict(passed=True, technical_complete=True,
                seed=seed, matched_error_draws=True,
                max_standardized_error_off=scores[0][
                    'maximum_absolute_standardized_error'],
                max_standardized_error_on=scores[1][
                    'maximum_absolute_standardized_error'],
                simultaneous_95_contained_off=scores[0][
                    'simultaneous_95_contained'],
                simultaneous_95_contained_on=scores[1][
                    'simultaneous_95_contained'],
                original_reads=0, protected_reads=0, earth_model_fits=0,
                generated_coverage_qualified=False,
                scientific_decision='abstain')


def write_definition(root):
    """Write one idempotent finite definition before study preparation."""
    from .studies.artifacts import atomic
    root = Path(root).resolve()
    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('prepared paired study definition cannot be rewritten')
    policy_path = HERE+'/policy.json'
    definition_path = HERE+'/definition.json'
    definition = dict(id=ID,
        scope='paired generated vibration software control; no aircraft originals',
        workers=1, threads=1, maximum_wall_s=900,
        adapter='analysis/lll/esa_paired_vibration_control.py',
        sources=[
            'analysis/lll/esa_paired_vibration_control.py',
            'analysis/lll/esa_integrated_drift_v2_pilot.py',
            'analysis/lll/esa_integrated_drift_pilot.py',
            'analysis/lll/esa_motion_error_controls.py',
            'analysis/lll/esa_generated_imu_propagation.py',
            'analysis/lll/integrated_drift_v2.py',
            'analysis/lll/state_space_covariance.py',
            'analysis/lll/ilvis0_error_model.py',
            'analysis/tests/test_esa_paired_vibration_control.py',
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
                raise ValueError('existing paired study freeze differs')
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
