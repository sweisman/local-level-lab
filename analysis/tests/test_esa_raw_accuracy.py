# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_raw_forecast_requires_original_future_clock_and_no_position_updates():
    from lll.esa_raw_accuracy import raw_positions

    future = list(range(400, 520))
    archive = dict(training_epochs=400, prediction_epochs=120,
                   prediction_receiver_positions_used=False,
                   continuous_propagation_without_gps_reset=True,
                   times_s=list(range(520)), coordinates=[[0., 0., 0.]] * 520)
    assert raw_positions(archive, future) == [[0., 0., 0.]] * 120
    with pytest.raises(ValueError, match='clock'):
        raw_positions(archive, future[1:] + [520])
    archive['prediction_receiver_positions_used'] = True
    with pytest.raises(ValueError, match='without later positions'):
        raw_positions(archive, future)
