# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local planar known-answer control for withheld IMU prediction ambiguity.

This is a mathematical software control, not a model of any recorded flight.
"""

import math
from pathlib import Path


def paired_forecasts(*,training_s=800,future_s=120,rate_hz=300,
                     speed_mps=80.,rate_dph=1.):
    """Equal recorded IMU/training GPS, different motion after GPS is withheld.

    One platform turns at a constant rate and has an ideal IMU. The other
    continues straight but develops equal gyro and lateral-force errors.
    The errors switch on at the withholding boundary; no claim is made that
    a particular instrument has this behavior.
    """
    if (type(training_s) is not int or not 1<=training_s<=1200 or
            type(future_s) is not int or not 1<=future_s<=400 or
            type(rate_hz) is not int or not 1<=rate_hz<=300 or
            not all(type(value) in (int,float) and math.isfinite(value) and
                    value>0 for value in (speed_mps,rate_dph)) or
            speed_mps>300 or rate_dph>10):
        raise ValueError('finite positive bounded training, future, speed and rate required')
    import numpy as np
    rate=math.radians(rate_dph)/3600.
    t=np.arange(-training_s*rate_hz,future_s*rate_hz+1,dtype=float)/rate_hz
    future=t>0
    gyro=np.zeros((len(t),3),dtype=float)
    gyro[future,2]=rate
    force=np.zeros_like(gyro)
    force[:,2]=9.80665
    force[future,1]=speed_mps*rate
    straight_gyro=np.zeros_like(gyro)
    straight_force=np.zeros_like(force)
    straight_force[:,2]=9.80665
    training_t=np.arange(-training_s,1,dtype=float)
    future_t=np.arange(1,future_s+1,dtype=float)
    training_position=np.zeros((len(training_t),3),dtype=float)
    training_position[:,0]=speed_mps*training_t
    straight_position=np.zeros((len(future_t),3),dtype=float)
    straight_position[:,0]=speed_mps*future_t
    turning_position=np.zeros_like(straight_position)
    turning_position[:,0]=speed_mps*np.sin(rate*future_t)/rate
    turning_position[:,1]=2*speed_mps*np.sin(rate*future_t/2)**2/rate
    return dict(version='esa-forecast-ambiguity-control-v1',
                imu_time_s=t,future_receiver_time_s=future_t,
                training_s=training_s,future_s=future_s,rate_hz=rate_hz,
                speed_mps=float(speed_mps),rate_dph=float(rate_dph),
                turning=dict(measured_gyro_rads=gyro,
                    measured_force_mps2=force,
                    training_receiver_position_m=training_position,
                    true_gyro_rads=gyro.copy(),true_force_mps2=force.copy(),
                    gyro_sensor_error_rads=np.zeros_like(gyro),
                    force_sensor_error_mps2=np.zeros_like(force),
                    future_receiver_position_m=turning_position),
                straight=dict(measured_gyro_rads=gyro.copy(),
                    measured_force_mps2=force.copy(),
                    training_receiver_position_m=training_position.copy(),
                    true_gyro_rads=straight_gyro,
                    true_force_mps2=straight_force,
                    gyro_sensor_error_rads=gyro.copy(),
                    force_sensor_error_mps2=force-straight_force,
                    future_receiver_position_m=straight_position),
                end_separation_m=float(np.linalg.norm(
                    turning_position[-1]-straight_position[-1])),
                original_reads=0,protected_reads=0)


def summarize_control(**options):
    import hashlib
    import numpy as np
    case=paired_forecasts(**options)
    turn,straight=case['turning'],case['straight']
    imu_fields=('measured_gyro_rads','measured_force_mps2')
    imu_equal=all(np.array_equal(turn[name],straight[name])
                  for name in imu_fields)
    receiver_equal=np.array_equal(turn['training_receiver_position_m'],
                                   straight['training_receiver_position_m'])
    if not imu_equal or not receiver_equal:
        raise ValueError('equal observed streams required')
    return dict(version=case['version'],
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                training_s=case['training_s'],future_s=case['future_s'],
                rate_hz=case['rate_hz'],speed_mps=case['speed_mps'],
                hypothetical_rate_dph=case['rate_dph'],
                hypothetical_lateral_force_error_mps2=float(
                    case['speed_mps']*math.radians(case['rate_dph'])/3600),
                recorded_imu_identical=imu_equal,
                training_receiver_identical=receiver_equal,
                future_receiver_withheld=True,
                error_switches_on_at_withholding_boundary=True,
                end_separation_m=case['end_separation_m'],
                imu_samples=len(case['imu_time_s']),
                training_receiver_reports=len(turn['training_receiver_position_m']),
                original_reads=0,protected_reads=0,native_calls=0,
                error_bound_measured_from_instrument=False,
                coverage_calibrated=False,scientific_decision='abstain')


def publish(root):
    from .studies.artifacts import atomic,encoded
    result=summarize_control()
    base=Path(root).resolve()/'docs/prediction-observed-development'
    atomic(base/'FORECAST_AMBIGUITY_CONTROL.json',encoded(result))
    page=('# What can identical recorded inputs predict?\n\n'
        'This local planar software control gives two paths exactly the same '
        '800 seconds of earlier receiver positions and the same recorded IMU '
        'stream throughout. After receiver positions are withheld, one path '
        'turns gently and its IMU is ideal. The other continues straight while '
        'a new gyro error and matching lateral-force error produce the same '
        'recorded IMU readings. At 80 m/s and an illustrative 1°/hour rate, '
        'their positions separate by {:.2f} m after 120 seconds.\n\n'
        'The new errors start exactly when positions are withheld. This is an '
        'adversarial possibility, **not** an estimate of either archived IMU, '
        'a likely aircraft event or a calibrated error limit. It shows why a '
        'short forecast still needs independently justified limits on changing '
        'sensor error and unmodeled aircraft motion. No aircraft data or '
        'physical-model fit entered this calculation.\n\n'
        '[Configuration and source hash](FORECAST_AMBIGUITY_CONTROL.json) · '
        '[Observed error qualification](OBSERVED_ERROR_PLAN.md).\n').format(
            result['end_separation_m'])
    atomic(base/'FORECAST_AMBIGUITY_CONTROL.md',page.encode())
    return result


def main(argv=None):
    import argparse
    import json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    result=publish(args.root)
    print(json.dumps(dict(end_separation_m=result['end_separation_m'],
                          original_reads=result['original_reads'],
                          protected_reads=result['protected_reads']),sort_keys=True))


if __name__=='__main__':main()
