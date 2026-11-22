# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the alternate time join and receiver perturbation bookkeeping."""

import numpy as np
import pytest

from lll import esa_direction_holdout_field_range as field
from lll import esa_direction_holdout_receiver as receiver


def test_matching_preserves_original_windows_and_unmatched_rows():
    windows = [dict(receiver_times_s=[start+i for i in range(400)]) for start in (1., 500.)]
    source = [dict(time_s=t+.001, gps_week=2269) for w in windows for t in w['receiver_times_s'] if t != 700.]
    matches = receiver.match_selected(windows, receiver.bounded_rows(source, len(source)))
    assert matches[0] == source[:400]
    assert matches[1][200] is None
    assert matches[1][201]['time_s'] == 701.001
    assert matches[1][-1]['time_s'] == 899.001
    with pytest.raises(ValueError, match='row count'):
        receiver.match_selected(windows, receiver.bounded_rows(source, len(source)+1))


def test_replayed_zero_field_error_uses_the_alternate_prediction(monkeypatch):
    vectors = np.column_stack((np.linspace(0., .04, 16), np.zeros(16), np.ones(16)))
    saved = np.asarray(field.direction_pair_angles_deg(vectors[8:]))+.01
    monkeypatch.setattr(field.forecast, 'paired_supports', lambda *a, **kw: [(0, (), dict(velocity=0, position=0))]*16)
    monkeypatch.setattr(field, 'rate_operator', lambda _: (None, None))
    monkeypatch.setattr(field, '_predicted_vectors', lambda *a, **kw: {
        name: dict(globe=vectors, disc=vectors) for name in field.FIELDS})
    late = iter(vectors[8:].tolist()*4)

    class Node:
        def __init__(self, value):
            self.value = value

        def average(self, frame):
            return self.value

        def rate_bound(self, rate, anchor):
            return 0.

        start = 0.

    monkeypatch.setattr(field, 'support', lambda *a: Node(next(late)))
    sealed = {m: {name: dict(globe=saved, disc=saved) for name in field.FIELDS} for m in field.forecast.METHODS}
    measured = dict(observed_deg={'11': {'uncorrected': saved}}, scores={'11': {m: {
        name: {'uncorrected': {'earlier_reference_rms_deg': .005}} for name in field.FIELDS} for m in field.forecast.METHODS}})
    result = field.profile_width([0.], [[0., 0., 0.]], [], 11, np.array([0., 1.]), 0.,
        {name: [None, None] for name in field.SHAPE_MODELS.values()}, sealed, measured, sample_time=[.001])
    method = result['velocity']
    assert method['fixed_prediction_shift_from_air1_rms_deg']['globe']['zero_field'] == pytest.approx(.01)
    output = method['corrections']['uncorrected']['by_shape']['globe']['fixed_field_errors']['zero_field']
    assert output['error_rms_deg'] == pytest.approx(.01)
    assert not output['within_reference']
