# SPDX-License-Identifier: AGPL-3.0-or-later
import gzip
import json
from types import SimpleNamespace

import pytest


def test_receiver_header_reader_does_not_require_the_inertial_tail():
    from lll.ilvis0_remaining_gps_baseline import receiver_header

    header = receiver_header(gzip.compress(b'{"layout":{},"segment_id":"x","times":[1,2],"values":['))
    assert header == dict(layout={}, segment_id='x', times=[1, 2])
    with pytest.raises(ValueError):
        receiver_header(gzip.compress(b'{"segment_id":"x","times":[1,2]}'))


def test_gps_forecast_is_saved_before_later_coordinates_are_opened(tmp_path, monkeypatch):
    from lll import ilvis0_control_shards as lifecycle
    from lll.ilvis0_remaining_gps_baseline import evaluate

    training = dict(segment_id='x', group_id='group', origin='inner',
                    training_times=list(range(60)), training_gps=[[0., 0., 1000.]]*60,
                    future_times=list(range(60, 75)))
    scoring = dict(segment_id='x', prediction_gps=[[0., 0., 1005.]]*15, imu=None)
    records = {}
    charges = []
    monkeypatch.setattr(lifecycle, '_check_continue', lambda *_: None)

    class Context(lifecycle.TaskContext):
        def __init__(self, task):
            self.root = tmp_path
            self.task = task
            self.manifest = {}
            self.journal = SimpleNamespace(read=lambda _: charges, append=lambda _, row: charges.append(row))

        def _writable(self):
            pass

        def input_path(self, key=None):
            if key is not None:
                assert records['forecast.json']['coordinates'] == [[0., 0., 1000.]]*15
            path = tmp_path / ('scoring.json' if key else 'training.json')
            path.write_text(json.dumps(scoring if key else training))
            return path

        def save(self, name, value):
            records[name] = value

    task = dict(identity='x-inner', payload=dict(segment_id='x', origin='inner'),
                limits=dict(bound_calls=1, bound_steps=0, native_calls=0, packet_visits=0))
    result = evaluate(task, Context(task))
    assert charges == [dict(identity='x-inner', phase='diagnostic', kind='value', bound_steps=0)]
    assert result['gps']['horizontal_rms_m'] == 0.
    assert result['gps']['up_rms_m'] == 5.
    assert result['imu'] is None
