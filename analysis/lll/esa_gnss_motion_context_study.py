# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two prepaid, training-only ESA GNSS/IMU motion-context comparisons."""

import hashlib
import io
import json
from pathlib import Path


POLICY = dict(version='esa-gnss-motion-context-v1',
              half_windows_s=[1., 5.],
              maximum_imu_gap_s=.02,
              maximum_receiver_gap_s=.3,
              maximum_receiver_match_s=.11,
              minimum_supported_centers=350,
              maximum_imu_samples=120000,
              maximum_receiver_samples=2100,
              training_centers=400,
              native_calls=0, earth_model_fits=0,
              protected_reads=0, scientific_decision='abstain')


def tasks():
    return [dict(identity=f'span-{int(2*half)}s', input_key='staged',
                 payload=dict(half_window_s=half), native_kind='value',
                 limits=dict(native_calls=0, packet_visits=0,
                             bound_calls=0, bound_steps=0))
            for half in POLICY['half_windows_s']]


def evaluate(task, context):
    import numpy as np
    from .esa_gnss_motion_context import compare_course_rate

    policy = json.loads(context.input_path('policy').read_bytes())
    binding = json.loads(context.input_path('binding').read_bytes())
    raw = context.input_path('staged').read_bytes()
    requested = {k:v for k,v in task.items() if k not in ('index','shard')}
    if (policy != POLICY or requested not in tasks() or
            binding.get('version') != 'esa-gnss-motion-context-input-v1' or
            binding.get('staged_sha256') != hashlib.sha256(raw).hexdigest() or
            binding.get('source_sha256') != hashlib.sha256(
                (Path(context.root).parents[1]/'analysis/lll/esa_gnss_motion_preparation.py')
                .read_bytes()).hexdigest() or
            binding.get('later_receiver_reports_decoded') != 0 or
            binding.get('protected_group_reads') != 0 or
            binding.get('earth_model_fits') != 0):
        raise ValueError('unchanged earlier-only motion input and policy required')
    with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in (
            'imu_time_s', 'gyro_body_rads', 'receiver_time_s',
            'receiver_ne_mps', 'center_time_s')}
    if (len(arrays['imu_time_s']) != binding['imu_samples'] or
            len(arrays['imu_time_s']) > policy['maximum_imu_samples'] or
            len(arrays['receiver_time_s']) != binding['receiver_samples'] or
            len(arrays['receiver_time_s']) > policy['maximum_receiver_samples'] or
            len(arrays['center_time_s']) != policy['training_centers'] or
            arrays['center_time_s'][-1] != binding['last_training_s'] or
            arrays['receiver_time_s'][-1] > binding['last_training_s']+.002 or
            arrays['imu_time_s'][-1] > binding['last_training_s']):
        raise ValueError('bounded training-only arrays required')
    result = compare_course_rate(
        arrays['imu_time_s'], arrays['gyro_body_rads'],
        arrays['receiver_time_s'], arrays['receiver_ne_mps'],
        arrays['center_time_s'], half_window_s=task['payload']['half_window_s'],
        maximum_imu_gap_s=policy['maximum_imu_gap_s'],
        maximum_receiver_gap_s=policy['maximum_receiver_gap_s'],
        maximum_receiver_match_s=policy['maximum_receiver_match_s'])
    result.update(policy_version=policy['version'],
                  half_window_s=task['payload']['half_window_s'],
                  staged_sha256=binding['staged_sha256'],
                  original_reads=0, protected_reads=0,
                  earth_model_fits=0, sensor_noise_identified=False,
                  scientific_decision='abstain')
    context.save('motion.json', result)
    return dict(passed=result['count'] >= policy['minimum_supported_centers'],
                technical_support=result['count'],
                rejected_centers=len(result['rejected']),
                native_calls=0, original_reads=0, protected_reads=0,
                earth_model_fits=0, sensor_noise_identified=False,
                scientific_decision='abstain')
