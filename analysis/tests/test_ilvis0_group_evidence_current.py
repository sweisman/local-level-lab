import pytest

from lll.ilvis0_group_evidence_current import forecast_summary, match_recordings


def test_group_index_deduplicates_overlapping_recorders_and_rejects_cross_group_pair():
    rows = [{'group_id': 'leg-a', 'members': 'imu8;imu21'},
            {'group_id': 'leg-b', 'members': 'other'}]
    index = match_recordings(rows)
    assert index['imu8'] == index['imu21'] == 'leg-a'
    assert index['other'] == 'leg-b'
    rows[1]['members'] = 'imu8;other'
    with pytest.raises(ValueError, match='unique'):
        match_recordings(rows)


def test_group_forecast_keeps_budget_failure_separate_from_accuracy():
    tracks = ('dual_frequency', 'l1_broadcast', 'onboard')

    def scorable(horizontal, passed):
        return dict(status='scorable',
            heldout_rms_by_gps_stream={track: dict(horizontal_rms_m=horizontal, height_rms_m=0.)
                                      for track in tracks},
            error_scores={track: dict(accuracy=dict(passed=passed)) for track in tracks})

    record = dict(segment_id='representative', attempts=dict(sphere_rotating=scorable(11., False),
        flat_geographic_field=scorable(200., False), sphere_still=scorable(5., True),
        flat_still=dict(status='budget_stopped')), shape_by_field=dict(specified='globe', zero='unresolved'),
        globe_field='unresolved')
    result = forecast_summary(record)
    assert result['matched_forecasts_scorable'] == 3
    assert result['matched_shape_at_zero_field'] == 'unresolved'
    assert result['matched_globe_field'] == 'unresolved'
    assert result['matched_models_meeting_position_limits'] == 'sphere_still'
    assert result['matched_non_scorable_models'] == 'flat_still=budget_stopped'
    record['globe_field'] = 'specified'
    with pytest.raises(ValueError, match='ranking'):
        forecast_summary(record)
