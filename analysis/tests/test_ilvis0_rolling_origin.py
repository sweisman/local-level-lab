"""Earlier-only and later forecast inputs stay separated at both cuts."""

import pytest


def _parent():
    return (dict(segment_id='saved', layout=dict(training_epochs=6,
                                                 receiver_epochs=10),
                 times=list(range(10)), values=[[i] for i in range(10)],
                 training_gps=[[i, i+1, i+2] for i in range(6)]),
            dict(segment_id='saved', prediction_gps=[[i, i+1, i+2]
                                                       for i in range(6, 10)]))


def test_equal_horizon_splits_hide_future_receiver_positions():
    from lll.ilvis0_rolling_origin import split_origins

    measurements, scoring = _parent()
    result = split_origins(measurements, scoring)
    assert result['horizon_epochs'] == 3
    assert result['inner']['training']['training_gps'] == measurements['training_gps'][:3]
    assert result['inner']['scoring']['prediction_gps'] == measurements['training_gps'][3:6]
    assert result['outer']['training']['training_gps'] == measurements['training_gps']
    assert result['outer']['scoring']['prediction_gps'] == scoring['prediction_gps'][:3]
    assert 'prediction_gps' not in result['inner']['training']
    assert 'prediction_gps' not in result['outer']['training']
    assert result['common']['values'] == measurements['values']
    assert result['common']['times'] == measurements['times']
    assert not any('gps' in key for key in result['common'])
    assert 'values' not in result['inner']['training']
    assert 'values' not in result['outer']['training']


def test_split_rejects_changed_parent_layout_and_scoring():
    from lll.ilvis0_rolling_origin import split_origins

    measurements, scoring = _parent()
    measurements['layout']['training_epochs'] = 5
    with pytest.raises(ValueError, match='two-thirds'):
        split_origins(measurements, scoring)
    measurements['layout']['training_epochs'] = 6
    scoring['prediction_gps'] = scoring['prediction_gps'][:-1]
    with pytest.raises(ValueError, match='later receiver'):
        split_origins(measurements, scoring)


def test_split_rejects_future_positions_in_fit_input():
    from lll.ilvis0_rolling_origin import split_origins

    measurements, scoring = _parent()
    measurements['prediction_gps'] = scoring['prediction_gps']
    with pytest.raises(ValueError, match='future receiver'):
        split_origins(measurements, scoring)
