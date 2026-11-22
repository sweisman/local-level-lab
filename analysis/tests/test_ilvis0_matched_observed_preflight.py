"""Frozen task grid and allowance for the recorded matched preflight."""

from lll.ilvis0_matched_observed_preflight import tasks
from lll.ilvis0_matched_training import MATCHED_MODELS


def test_preflight_assigns_each_model_the_same_recording_allowance():
    rows = [dict(segment_id=segment, training_epochs=50, scoring_epochs=25,
                 clocks={'nominal_200Hz': {'training_packets': 10_000,
                                           'forecast_packets': 15_000}})
            for segment in ('recording-one', 'recording-two')]
    grid = tasks(rows)
    assert len(grid) == 8
    for row in rows:
        chosen = [item for item in grid if item['segment_id'] == row['segment_id']]
        assert {item['model'] for item in chosen} == set(MATCHED_MODELS)
        assert all(item['limits'] == dict(native_calls=31, bound_calls=0, bound_steps=0,
            packet_visits=30*10_000*50+15_000*75) for item in chosen)
        assert all(item['input_key'] == row['segment_id']+'-packets' for item in chosen)
