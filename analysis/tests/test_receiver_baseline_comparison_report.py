"""Both receiver-only controls must use exactly the same scored epochs."""

import pytest

from lll.receiver_baseline_comparison_report import paired_row
from lll.receiver_only_forecast_report import replay


def _case(segment, north):
    epochs = [{"epoch": i, "time_s": float(80+i),
               "north_error_m": north, "east_error_m": 0.0,
               "up_error_m": 2.0} for i in range(2)]
    result = {"segment_id": segment, "group_id": "group-a",
              "training_epochs": 80, "prediction_epochs": 2,
              "imu_samples_used": 0, "later_positions_used_for_forecast": False,
              "scientific_decision": "abstain", "passed": True}
    return result, epochs, replay(epochs)


def test_pair_requires_identical_group_and_scoring_times():
    linear = _case("segment", 10.0)
    spherical = _case("segment", 4.0)
    row = paired_row(linear, spherical)
    assert row["linear_horizontal_rms_m"] == 10.0
    assert row["spherical_horizontal_rms_m"] == 4.0
    assert row["horizontal_ratio_spherical_to_linear"] == 0.4
    spherical[1][0]["time_s"] = 79.0
    with pytest.raises(ValueError, match="same withheld"):
        paired_row(linear, spherical)
