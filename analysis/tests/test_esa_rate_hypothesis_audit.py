"""Saved iMAR rates must retain the three distinct integration hypotheses."""
import pytest


def test_left_and_right_rate_integrals_bracket_saved_linear_points():
    from lll.esa_rate_hypothesis_audit import compare_rate_integrals

    times = [0., .001, .002]
    rates = [[0., 0., 0.], [200., 0., 0.], [400., 0., 0.]]
    forces = [[0., 0., 0.], [1000., 0., 0.], [2000., 0., 0.]]
    report = compare_rate_integrals(
        times, rates, forces,
        saved_theta=[[.1, 0., 0.], [.3, 0., 0.]],
        saved_dv=[[.5, 0., 0.], [1.5, 0., 0.]],
        saved_dt=[.001, .001], training_prefix=1)
    assert report['gyro']['left_hold']['training_net'][0] == pytest.approx(-.1)
    assert report['gyro']['right_hold']['full_net'][0] == pytest.approx(.2)
    assert report['accel']['left_hold']['full_net'][0] == pytest.approx(-1.)
    assert report['linear_reconstruction_max_abs'] < 1e-12


def test_changed_saved_linear_increments_are_rejected():
    from lll.esa_rate_hypothesis_audit import compare_rate_integrals

    with pytest.raises(ValueError, match='saved linear'):
        compare_rate_integrals(
            [0., .001, .002], [[0., 0., 0.]]*3, [[0., 0., 0.]]*3,
            saved_theta=[[.01, 0., 0.], [0., 0., 0.]],
            saved_dv=[[0., 0., 0.]]*2, saved_dt=[.001, .001],
            training_prefix=1)
