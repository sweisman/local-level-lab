"""A longer ESA horizon reuses a sealed calibration and an exact forecast prefix."""

import pytest
import numpy as np
import gzip
import io
import json
from test_ilvis0_forecast import forecast_fixture, forecast_kernels


def test_extension_tasks_are_fixed_point_and_finite():
    from lll.esa_training_split_extension import tasks

    planned = tasks()
    assert [task['identity'] for task in planned] == ['increment', 'point']
    assert all(task['payload']['optimize'] is False for task in planned)
    assert all(task['limits']['native_calls'] == 500_000 for task in planned)


def test_extension_requires_qualification_before_staging(tmp_path):
    from lll.esa_training_split_extension import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path)


def test_extension_rejects_changed_task_before_input_read():
    from types import SimpleNamespace
    from lll.esa_training_split_extension import SCOPE, INPUT_KEYS, tasks, evaluate

    task = dict(tasks()[0], index=0, shard=0)
    task['payload'] = dict(task['payload'], optimize=True)
    context = SimpleNamespace(manifest=dict(scope=SCOPE,
        inputs={key: {} for key in INPUT_KEYS}))
    with pytest.raises(ValueError, match='unchanged fixed-fit'):
        evaluate(task, context)


def test_extension_prefix_rejects_a_micrometre_change():
    from lll.esa_training_split_extension import check_prefix

    original = [[0.7, 0.2, 100.], [0.7, 0.2, 101.]]
    longer = original + [[0.7, 0.2, 102.]]
    assert check_prefix(longer, original, count=2) == pytest.approx(0.)
    longer[1] = [0.7, 0.2, 101.000002]
    with pytest.raises(ValueError, match='prefix'):
        check_prefix(longer, original, count=2)


def test_generated_native_extension_preserves_shorter_prefix(forecast_kernels):
    from lll.esa_training_split_extension import check_prefix
    from lll.ilvis0_forecast import native_forecast

    train, _, theta, dv, dt, times = forecast_fixture(
        forecast_kernels, False, 'header_elapsed')
    point = np.zeros(len(train.bounds.active))
    shorter = times[:7]
    count = int(np.searchsorted(np.cumsum(dt),
        shorter[-1] + train.bounds.limits.get('time_offset', 0.),
        side='left')) + 1
    common = dict(maximum_interval_s=.0075,
                  reserve=lambda **charge: None)
    first = native_forecast(train, point, 'sphere_rotating',
        theta=theta[:count], dv=dv[:count], dt=dt[:count],
        times=shorter, **common)
    longer = native_forecast(train, point, 'sphere_rotating',
        theta=theta, dv=dv, dt=dt, times=times, **common)
    assert check_prefix(longer['coordinates'], first['coordinates'],
                        count=len(shorter)) < 1e-6


def test_600_400_extension_stages_no_scoring_receiver_values():
    from lll.esa_training_split import partition_development_input

    rows = [dict(time_s=float(i + 100), latitude_deg=1.,
                 longitude_deg=2., height_m=float(i)) for i in range(1200)]
    interval = io.BytesIO()
    np.savez(interval, theta=np.zeros((1200, 3)),
             dv=np.zeros((1200, 3)), dt=np.ones(1200))
    arguments = dict(time_origin_s=99., training_epochs=600,
                     forecast_epochs=1000, latency_s=0.)
    def stage(source):
        return partition_development_input(interval.getvalue(),
            gzip.compress(json.dumps(source).encode()),
            np.arange(1., 1201.), **arguments)
    first = stage(rows)
    changed = [dict(row) for row in rows]
    for row in changed[600:1000]:
        row['height_m'] += 9999.
    second = stage(changed)
    assert first.fit_material() == second.fit_material()
    assert first.scoring_rows != second.scoring_rows
    assert len(first.scoring_rows) == 400
    assert first.packet_count == 1000
