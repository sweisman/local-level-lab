"""Known-motion checks for a receiver-course / recorded-gyro diagnostic."""

import numpy as np
import pytest
import hashlib
import io
import json
from pathlib import Path

from lll.esa_gnss_motion_context import compare_course_rate
from lll.esa_motion_error_controls import analytic_path, make_control


def test_known_turn_matches_course_rate_after_fixed_gyro_offset():
    receiver_time = np.arange(0., 40.01, .2)
    imu_time = np.arange(.005, 40., .01)
    angle = lambda t: 3.1 + .2*np.sin(2*np.pi*t/20.)
    rate = lambda t: .2*(2*np.pi/20.)*np.cos(2*np.pi*t/20.)
    speed = 80.
    receiver = np.column_stack((speed*np.cos(angle(receiver_time)),
                                speed*np.sin(angle(receiver_time))))
    gyro = np.column_stack((np.zeros(len(imu_time)),
                            np.zeros(len(imu_time)),
                            rate(imu_time)+.003))
    result = compare_course_rate(imu_time, gyro, receiver_time, receiver,
                                 np.arange(6., 34., 2.), half_window_s=1.)
    assert result['count'] == 14
    assert result['correlation'] > .999
    assert result['demeaned_rms_difference_dph'] < 15.
    assert abs(result['mean_imu_minus_course_dph']-.003*180/np.pi*3600) < 20.


def test_gaps_abstain_and_input_contract_is_strict():
    t = np.arange(0., 12.01, .2)
    rate = np.column_stack((np.ones(len(t))*50, np.zeros(len(t))))
    imu_t = np.arange(.005, 12., .01)
    gyro = np.zeros((len(imu_t), 3))
    sparse_t = np.delete(t, np.arange(20, 27))
    sparse_rate = np.delete(rate, np.arange(20, 27), axis=0)
    result = compare_course_rate(imu_t, gyro, sparse_t, sparse_rate,
                                 np.array([5.]), half_window_s=1.)
    assert result['count'] == 0
    assert result['status'] == 'insufficient_support'
    assert result['rejected'] == [{'center_s': 5., 'reason': 'receiver_support'}]
    with pytest.raises(ValueError):
        compare_course_rate(imu_t[::-1], gyro, t, rate,
                            np.array([5.]), half_window_s=1.)
    with pytest.raises(ValueError):
        compare_course_rate(imu_t, gyro, t, rate,
                            np.array([5.]), half_window_s=0.)


@pytest.mark.parametrize('span_s', [2, 10])
def test_analytic_aircraft_control_separates_known_motion_from_imu_error(span_s):
    receiver_t = np.arange(0., 120.001, .2)
    receiver_velocity = analytic_path(receiver_t)['velocity_neu_mps'][:, :2]
    centers = np.arange(10., 110., 2.)
    results = []
    for errors in (False, True):
        control = make_control(duration_s=120, rate_hz=300,
                               seed=20261115, errors=errors)
        result = compare_course_rate(
            control['imu_time_s'],
            control['measured_dtheta_rad']/control['imu_dt_s'],
            receiver_t, receiver_velocity, centers,
            half_window_s=span_s/2)
        assert result['count'] == len(centers)
        assert result['sensor_noise_identified'] is False
        assert result['scientific_decision'] == 'abstain'
        results.append(result)
    # The independently checked analytic path has no crab or roll. Its exact
    # motion aligns to the GNSS course to far better than the noisy control.
    assert results[0]['demeaned_rms_difference_dph'] < .01
    assert 1. < results[1]['demeaned_rms_difference_dph'] < 2.


def test_study_adapter_preserves_training_boundary_and_abstention(tmp_path):
    from lll.esa_gnss_motion_context_study import evaluate, tasks, POLICY

    repo_root = Path(__file__).resolve().parents[2]
    imu_t = np.arange(.005, 399., .01)
    receiver_t = np.arange(-5., 399.01, .2)
    angle = lambda t: .05*np.sin(2*np.pi*t/30.)
    gyro = np.column_stack((np.zeros(len(imu_t)), np.zeros(len(imu_t)),
                            .05*(2*np.pi/30.)*np.cos(2*np.pi*imu_t/30.)))
    receiver = np.column_stack((80*np.cos(angle(receiver_t)),
                                80*np.sin(angle(receiver_t))))
    buffer = io.BytesIO()
    np.savez_compressed(buffer, imu_time_s=imu_t, gyro_body_rads=gyro,
                        receiver_time_s=receiver_t, receiver_ne_mps=receiver,
                        center_time_s=np.arange(400, dtype=float))
    staged = buffer.getvalue()
    paths = {'staged':tmp_path/'staged.npz', 'binding':tmp_path/'binding.json',
             'policy':tmp_path/'policy.json'}
    paths['staged'].write_bytes(staged)
    paths['binding'].write_text(json.dumps(dict(
        version='esa-gnss-motion-context-input-v1',
        staged_sha256=hashlib.sha256(staged).hexdigest(),
        source_sha256=hashlib.sha256((repo_root/'analysis/lll/esa_gnss_motion_preparation.py')
                                     .read_bytes()).hexdigest(),
        imu_samples=len(imu_t), receiver_samples=len(receiver_t),
        last_training_s=399., later_receiver_reports_decoded=0,
        protected_group_reads=0, earth_model_fits=0)))
    paths['policy'].write_text(json.dumps(POLICY))

    class Context:
        root = repo_root/'data'/'test-study'
        saved = {}

        def input_path(self, key):
            return paths[key]

        def save(self, name, value):
            self.saved[name] = value

    context = Context()
    result = evaluate(tasks()[0], context)
    assert result['passed']
    assert result['scientific_decision'] == 'abstain'
    assert result['technical_support'] >= 350
    assert context.saved['motion.json']['rows'][-1]['stop_s'] <= 399.
