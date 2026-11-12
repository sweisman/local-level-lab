"""Saved forecast dependence is descriptive and uses exact receiver epochs."""

import pytest


def _series():
    rows = [dict(time_s=100. + i, latitude_deg=0., longitude_deg=0.,
                 height_m=100., position_variance_m2=[1., 1., 1.])
            for i in range(23)]
    scores = dict(times_s=[float(i) for i in range(23)],
                  receiver_coordinates=[[0., 0., 100.]] * 23,
                  errors_neu_m=[[float(i) + (1. if i % 2 else -1.),
                                 -float(i) + (1. if i % 2 else -1.),
                                 2.] for i in range(23)])
    return scores, rows


def test_detrended_structure_separates_drift_from_short_lag_noise():
    from lll.esa_saved_error_structure import summarize_structure

    scores, rows = _series()
    value = summarize_structure(scores, rows, training_epochs=3, lags=(1, 5))
    assert value['prediction_epochs'] == 20
    assert value['axes']['north']['slope_m_per_minute'] == pytest.approx(60., abs=1.)
    assert value['axes']['north']['raw_lag_correlation']['1'] > .8
    assert value['axes']['north']['detrended_lag_correlation']['1'] < -.8
    assert value['axes']['height']['raw_lag_correlation']['1'] is None
    assert value['cross_axis_detrended']['north:east'] > .9
    assert value['scientific_decision'] == 'abstain'


def test_structure_rejects_changed_receiver_join():
    from lll.esa_saved_error_structure import summarize_structure

    scores, rows = _series()
    rows[7]['height_m'] += 1.
    with pytest.raises(ValueError, match='coordinate'):
        summarize_structure(scores, rows, training_epochs=3, lags=(1,))


def test_lag_configuration_must_fit_withheld_series():
    from lll.esa_saved_error_structure import summarize_structure

    scores, rows = _series()
    with pytest.raises(ValueError, match='lags'):
        summarize_structure(scores, rows, training_epochs=3, lags=(20,))


def test_structure_requires_one_second_receiver_cadence_for_lag_labels():
    from lll.esa_saved_error_structure import summarize_structure

    scores, rows = _series()
    for index in range(4, len(rows)):
        scores['times_s'][index] += .5
        rows[index]['time_s'] += .5
    with pytest.raises(ValueError, match='one-second'):
        summarize_structure(scores, rows, training_epochs=3, lags=(1,))


def test_training_to_withheld_rms_ratio_and_zero_denominator():
    from lll.esa_saved_error_structure import summarize_structure

    scores, rows = _series()
    scores['errors_neu_m'] = ([[2., -1., 0.]] * 3 +
                              [[6., -2., 4.]] * 20)
    value = summarize_structure(scores, rows, training_epochs=3, lags=(1,))
    assert value['axes']['north']['training_rms_m'] == 2.
    assert value['axes']['north']['withheld_rms_m'] == 6.
    assert value['axes']['north']['withheld_to_training_rms'] == 3.
    assert value['axes']['east']['withheld_to_training_rms'] == 2.
    assert value['axes']['height']['withheld_to_training_rms'] is None
