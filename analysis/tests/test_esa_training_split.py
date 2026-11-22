"""The shorter ESA development recheck must not stage its scored GPS rows."""

import gzip
import io
import json

import numpy as np
import pytest


def _interval():
    stream = io.BytesIO()
    np.savez(stream, theta=np.arange(36, dtype=float).reshape(12, 3),
             dv=np.zeros((12, 3)), dt=np.ones(12))
    return stream.getvalue()


def _rows():
    return [dict(time_s=float(index + 100), latitude_deg=1.,
                 longitude_deg=2., height_m=float(index))
            for index in range(8)]


def test_shorter_recheck_stages_only_earlier_receiver_rows_and_imu():
    from lll.esa_training_split import partition_development_input

    result = partition_development_input(
        _interval(), gzip.compress(json.dumps(_rows()).encode()),
        np.arange(1., 13.), time_origin_s=99.,
        training_epochs=6, forecast_epochs=8, latency_s=0.)
    staged = json.loads(gzip.decompress(result.training_bytes))
    assert [row['height_m'] for row in staged] == list(range(6))
    assert [row['height_m'] for row in result.scoring_rows] == [6., 7.]
    assert result.times_s.tolist() == list(np.arange(1., 9.))
    with np.load(io.BytesIO(result.interval_bytes), allow_pickle=False) as archive:
        assert archive['dt'].tolist() == [1.] * 8
        assert archive['theta'][-1].tolist() == [21., 22., 23.]


def test_600_200_generated_split_is_unchanged_by_scoring_values():
    from lll.esa_training_split import partition_development_input

    rows = [dict(time_s=float(i + 100), latitude_deg=1.,
                 longitude_deg=2., height_m=float(i)) for i in range(800)]
    times = np.arange(1., 1201.)
    source = io.BytesIO()
    np.savez(source, theta=np.zeros((1200, 3)), dv=np.zeros((1200, 3)),
             dt=np.ones(1200))
    arguments = dict(time_origin_s=99., training_epochs=600,
                     forecast_epochs=800, latency_s=0.)
    first = partition_development_input(
        source.getvalue(), gzip.compress(json.dumps(rows).encode()),
        times, **arguments)
    changed = [dict(row) for row in rows]
    for row in changed[600:]:
        row['height_m'] += 9999.
    second = partition_development_input(
        source.getvalue(), gzip.compress(json.dumps(changed).encode()),
        times, **arguments)
    assert first.interval_bytes == second.interval_bytes
    assert first.training_bytes == second.training_bytes
    assert first.times_s.tolist() == second.times_s.tolist()
    assert first.packet_count == second.packet_count == 800
    assert first.scoring_rows != second.scoring_rows
    assert set(first.fit_material()) == {'interval', 'training', 'forecast_times'}
    assert first.fit_material() == second.fit_material()
    assert len(json.loads(gzip.decompress(first.training_bytes))) == 600
    assert len(first.scoring_rows) == 200


@pytest.mark.parametrize('damage', ('row_time', 'packet_gap', 'nonfinite', 'latency'))
def test_shorter_recheck_rejects_mismatched_or_unsupported_input(damage):
    from lll.esa_training_split import partition_development_input

    rows = _rows()
    interval = _interval()
    latency = 0.
    if damage == 'row_time':
        rows[3]['time_s'] += .25
    elif damage == 'packet_gap':
        stream = io.BytesIO()
        np.savez(stream, theta=np.zeros((12, 3)), dv=np.zeros((12, 3)),
                 dt=np.array([1.] * 6 + [0.] + [1.] * 5))
        interval = stream.getvalue()
    elif damage == 'nonfinite':
        rows[2]['height_m'] = float('nan')
    else:
        latency = 10.
    with pytest.raises(ValueError):
        partition_development_input(
            interval, gzip.compress(json.dumps(rows).encode()),
            np.arange(1., 13.), time_origin_s=99.,
            training_epochs=6, forecast_epochs=8, latency_s=latency)
