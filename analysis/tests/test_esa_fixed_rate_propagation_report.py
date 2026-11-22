"""Saved trajectory comparisons retain every rate interpretation."""
import numpy as np
import pytest


def test_report_compares_all_methods_without_selecting_by_receiver_error():
    from lll.esa_fixed_rate_propagation_report import compare

    base = np.array([[.5, .2, 1000.], [.5, .200001, 1000.],
                     [.5, .200002, 1000.], [.5, .200003, 1000.]])
    routes = {'linear_points': base,
              'left_hold': base+np.array([0., 1e-6, 0.]),
              'right_hold': base+np.array([0., -1e-6, 2.])}
    report = compare(routes, base, training_epochs=2)
    assert set(report['methods']) == set(routes)
    assert report['methods']['linear_points']['difference_from_baseline'][
        'prediction']['horizontal_rms_m'] == 0.
    assert report['methods']['left_hold']['difference_from_baseline'][
        'prediction']['horizontal_rms_m'] > 0.
    assert report['methods']['right_hold']['receiver_error'][
        'prediction']['vertical_rms_m'] == pytest.approx(2.)
    assert report['preferred_sampling_method'] is None
    assert report['scientific_decision'] == 'abstain'


def test_missing_method_is_rejected():
    from lll.esa_fixed_rate_propagation_report import compare

    rows = np.array([[.5, .2, 0.], [.5, .21, 0.], [.5, .22, 0.]])
    with pytest.raises(ValueError, match='three sealed'):
        compare({'linear_points': rows}, rows, training_epochs=2)
