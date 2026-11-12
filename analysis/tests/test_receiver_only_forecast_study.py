"""The saved-input receiver baseline keeps future positions out of forecasting."""

import json

import numpy as np
import pytest

from lll.receiver_only_forecast_study import evaluate, recipe, tasks


def _layout():
    return {"segment_id": "test", "receiver_epochs": 120,
            "training_epochs": 80, "prediction_epochs": 40,
            "group_id": "group-test"}


def test_task_grid_has_three_zero_native_tasks():
    layouts = [dict(_layout(), segment_id=name, group_id="group-" + name)
               for name in ("a", "b", "c")]
    grid = tasks(layouts)
    assert len(grid) == 3
    assert len({row["identity"] for row in grid}) == 3
    assert all(row["limits"] == {"native_calls": 0, "packet_visits": 0,
                                  "bound_calls": 0, "bound_steps": 0} for row in grid)


def test_worker_saves_forecast_before_opening_separate_score(tmp_path):
    times = np.arange(120.0)
    positions = np.column_stack((0.3 + times * 1e-6,
                                 0.2 + times * 2e-6, 1000.0 + times * 0.1))
    material = {"segment_id": "test", "layout": _layout(),
                "training_times": times[:80].tolist(),
                "future_times": times[80:].tolist(),
                "training_gps": positions[:80].tolist()}
    scoring = {"segment_id": "test", "prediction_gps": positions[80:].tolist()}
    for name, value in (("test-training", material), ("test-scoring", scoring),
                        ("recipe", recipe())):
        (tmp_path / name).write_text(json.dumps(value))

    class Context:
        def __init__(self):
            self.saved = []

        def input_path(self, key=None):
            if key == "test-scoring":
                assert "forecast.json" in self.saved
            return tmp_path / (key or "test-training")

        def save(self, name, value):
            self.saved.append(name)

    context = Context()
    result = evaluate(tasks([dict(_layout(), segment_id=name, group_id="group-" + name)
                             for name in ("test", "b", "c")])[0], context)
    assert result["passed"] is True
    assert result["prediction"]["horizontal_rms_m"] < 1e-5
    assert result["scientific_decision"] == "abstain"
    assert context.saved.index("forecast.json") < context.saved.index("scores.json")


def test_worker_rejects_imu_values_in_training_input(tmp_path):
    material = {"segment_id": "test", "layout": _layout(),
                "training_times": list(range(80)), "future_times": list(range(80, 120)),
                "training_gps": [[0, 0, 0]] * 80, "values": [[0]]}
    (tmp_path / "test-training").write_text(json.dumps(material))
    (tmp_path / "recipe").write_text(json.dumps(recipe()))

    class Context:
        def input_path(self, key=None):
            return tmp_path / (key or "test-training")

    with pytest.raises(ValueError, match="training-only"):
        evaluate(tasks([dict(_layout(), segment_id=name, group_id="group-" + name)
                        for name in ("test", "b", "c")])[0], Context())
