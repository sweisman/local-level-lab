# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite fresh-seed generated pilot for the changing-gyro-bias error law."""

import hashlib
import json
from pathlib import Path


ID = 'esa-generated-integrated-drift-v2-20261117'
HERE = 'docs/prediction-observed-development/integrated-drift-v2-pilot'
POLICY = dict(version='esa-generated-integrated-drift-pilot-v2',
    seeds=list(range(2026111700, 2026111716)),
    duration_s=120, rate_hz=100, training_epochs=61,
    total_epochs=121, forecast_epochs=60, maximum_imu_packets=12000,
    acceleration_psd=(.01**2+.02**2)/100,
    jerk_psd=.0003**2+9.80665**2*(.0001**2+.0002**2)/100,
    snap_psd=9.80665**2*(2e-6)**2,
    receiver_random_walk_psd=.01**2,
    receiver_white_std_m=.03,
    initial_receiver_offset_std_m=.01,
    initial_inertial_state_known=True,
    maximum_operator_bytes=500000,
    nominal_z_95=1.959963984540054,
    simultaneous_95_z=3.6351881983520586,
    original_reads=0, protected_reads=0, earth_model_fits=0,
    law_adequacy_qualified=False, scientific_decision='abstain')


def tasks():
    return [dict(identity=f'seed-{seed}', input_key='policy',
                 payload=dict(seed=seed, vibration=(seed % 2 == 0)),
                 native_kind='value',
                 limits=dict(native_calls=0, packet_visits=0,
                             bound_calls=0, bound_steps=0))
            for seed in POLICY['seeds']]


def forecast_from_earlier(propagated, policy):
    """Seal a conditional forecast before reading later receiver positions."""
    import numpy as np
    from .esa_integrated_drift_pilot import _histories
    from .integrated_drift_v2 import integrated_drift_v2_operator
    if policy != POLICY:
        raise ValueError('unchanged fixed candidate policy required')
    predicted, receiver = _histories(propagated, policy)
    count = policy['training_epochs']
    operator = integrated_drift_v2_operator(
        np.arange(policy['total_epochs'], dtype=float), origin_s=0.,
        acceleration_psd=policy['acceleration_psd'],
        jerk_psd=policy['jerk_psd'], snap_psd=policy['snap_psd'],
        initial_position_std_m=0., initial_velocity_std_mps=0.,
        initial_acceleration_std_mps2=0., initial_jerk_std_mps3=0.,
        receiver_random_walk_psd=policy['receiver_random_walk_psd'],
        initial_receiver_offset_std_m=
            policy['initial_receiver_offset_std_m'],
        receiver_loading=np.broadcast_to(
            np.eye(3)*policy['receiver_white_std_m'],
            (policy['total_epochs'], 3, 3)),
        maximum_bytes=policy['maximum_operator_bytes'])
    earlier = predicted[:count]-receiver[:count]
    _, state = operator.apply_block(earlier.reshape(-1), first_epoch=0)
    future = operator.conditional_marginals(state=state)
    sigma = np.sqrt(np.diagonal(future['covariance'], axis1=1, axis2=2))
    if (future['forecast_epochs'] != policy['forecast_epochs'] or
            not np.all(np.isfinite(sigma)) or np.any(sigma <= 0)):
        raise ValueError('complete positive earlier-only forecast required')
    return dict(version=policy['version'], training_epochs=count,
                forecast_epochs=policy['forecast_epochs'],
                earlier_residual_neu_m=earlier.tolist(),
                future_mean_neu_m=future['mean'].tolist(),
                future_sigma_neu_m=sigma.tolist(),
                operator_configuration=operator.configuration,
                operator_storage_bytes=operator.storage_bytes,
                later_receiver_positions_used=False,
                true_initial_state_supplied=True,
                observed_error_law_qualified=False,
                scientific_decision='abstain')


def score_future(propagated, forecast, policy):
    """Score the saved fixed forecast at all later receiver epochs."""
    import numpy as np
    from .esa_integrated_drift_pilot import _histories
    if (policy != POLICY or forecast.get('version') != policy['version'] or
            forecast.get('training_epochs') != policy['training_epochs'] or
            forecast.get('later_receiver_positions_used') is not False):
        raise ValueError('same frozen earlier-only forecast required')
    predicted, receiver = _histories(propagated, policy)
    mean = np.asarray(forecast['future_mean_neu_m'], dtype=float)
    sigma = np.asarray(forecast['future_sigma_neu_m'], dtype=float)
    shape = (policy['forecast_epochs'], 3)
    if (mean.shape != shape or sigma.shape != shape or
            not np.all(np.isfinite(mean)) or
            not np.all(np.isfinite(sigma)) or np.any(sigma <= 0)):
        raise ValueError('complete finite fixed forecast required')
    cut = policy['training_epochs']
    residual = predicted[cut:]-receiver[cut:]
    standardized = (residual-mean)/sigma
    inside_marginal = np.abs(standardized) <= policy['nominal_z_95']
    maximum = float(np.max(np.abs(standardized)))
    return dict(version=policy['version'], forecast_epochs=shape[0],
                later_residual_neu_m=residual.tolist(),
                standardized_later_error_neu=standardized.tolist(),
                maximum_absolute_standardized_error=maximum,
                marginal_95_fraction_neu=
                    np.mean(inside_marginal, axis=0).tolist(),
                whole_period_marginal_95_contained=bool(
                    np.all(inside_marginal)),
                simultaneous_95_contained=maximum <=
                    policy['simultaneous_95_z'],
                later_receiver_reports_scored=shape[0],
                earth_model_fits=0, law_adequacy_qualified=False,
                scientific_decision='abstain')


def evaluate(task, context):
    from .esa_motion_error_controls import make_control
    from .esa_generated_imu_propagation import propagate_generated
    raw = context.input_path('policy').read_bytes()
    policy = json.loads(raw)
    requested = {key: value for key, value in task.items()
                 if key not in ('index', 'shard')}
    if policy != POLICY or requested not in tasks():
        raise ValueError('unchanged generated pilot task and policy required')
    case = make_control(duration_s=policy['duration_s'],
                        rate_hz=policy['rate_hz'],
                        seed=task['payload']['seed'],
                        vibration=task['payload']['vibration'], errors=True)
    if len(case['imu_time_s']) != policy['maximum_imu_packets']:
        raise ValueError('declared generated packet allowance changed')
    propagated = propagate_generated(case)
    forecast = forecast_from_earlier(propagated, policy)
    context.save('conditional-forecast.json', forecast)
    outcome = score_future(propagated, forecast, policy)
    outcome.update(seed=task['payload']['seed'],
                   vibration=task['payload']['vibration'],
                   policy_sha256=hashlib.sha256(raw).hexdigest())
    context.save('outcome.json', outcome)
    return dict(passed=True, technical_complete=True,
                maximum_absolute_standardized_error=outcome[
                    'maximum_absolute_standardized_error'],
                simultaneous_95_contained=outcome['simultaneous_95_contained'],
                forecast_epochs=outcome['forecast_epochs'],
                original_reads=0, protected_reads=0, earth_model_fits=0,
                law_adequacy_qualified=False, scientific_decision='abstain')


def write_definition(root):
    """Write one idempotent policy and finite study definition."""
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('prepared study definition cannot be rewritten')
    policy_path = HERE+'/policy.json'
    definition_path = HERE+'/definition.json'
    definition = dict(id=ID,
        scope='generated software controls only; no aircraft originals',
        workers=1, threads=1, maximum_wall_s=1200,
        adapter='analysis/lll/esa_integrated_drift_v2_pilot.py',
        sources=[
            'analysis/lll/esa_integrated_drift_v2_pilot.py',
            'analysis/lll/esa_integrated_drift_pilot.py',
            'analysis/lll/esa_motion_error_controls.py',
            'analysis/lll/esa_generated_imu_propagation.py',
            'analysis/lll/integrated_drift_v2.py',
            'analysis/lll/state_space_covariance.py',
            'analysis/lll/ilvis0_error_model.py',
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
                raise ValueError('existing generated pilot freeze differs')
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
