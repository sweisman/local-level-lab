"""Saved receiver-only scores must replay from signed epoch errors."""

import pytest

from lll.receiver_only_forecast_report import replay


def test_replay_recovers_all_saved_error_summaries():
    epochs = [
        {"epoch": 0, "time_s": 10.0, "north_error_m": 3.0,
         "east_error_m": 4.0, "up_error_m": 0.0},
        {"epoch": 1, "time_s": 11.0, "north_error_m": 0.0,
         "east_error_m": 0.0, "up_error_m": -5.0},
    ]
    values = replay(epochs)
    assert values["horizontal_rms_m"] == pytest.approx(5 / 2**0.5)
    assert values["three_dimensional_rms_m"] == pytest.approx(5.0)
    assert values["maximum_horizontal_m"] == 5.0
    assert values["maximum_absolute_up_m"] == 5.0


def test_replay_rejects_missing_or_nonfinite_saved_epochs():
    with pytest.raises(ValueError, match="epoch"):
        replay([])
    with pytest.raises(ValueError, match="epoch"):
        replay([{"epoch": 1, "time_s": 10.0, "north_error_m": float("nan"),
                 "east_error_m": 0.0, "up_error_m": 0.0}])
