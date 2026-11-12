"""Spherical receiver control preserves the saved scoring boundary."""

import json

import numpy as np

from lll.receiver_only_geodesic_study import evaluate, recipe


def test_geodesic_worker_saves_forecast_before_scoring(tmp_path):
    radius = 6378137.0
    times = np.arange(120.0)
    positions = np.column_stack((np.zeros(len(times)),
                                 0.1 + 180.0*times/radius,
                                 np.full(len(times), 10000.0)))
    layout = {"segment_id": "example", "group_id": "group-example",
              "receiver_epochs": 120, "training_epochs": 80,
              "prediction_epochs": 40}
    training = {"segment_id": "example", "layout": layout,
                "training_times": times[:80].tolist(),
                "future_times": times[80:].tolist(),
                "training_gps": positions[:80].tolist()}
    scoring = {"segment_id": "example", "prediction_gps": positions[80:].tolist()}
    for name, value in (("example-training", training), ("example-scoring", scoring),
                        ("recipe", recipe())):
        (tmp_path/name).write_text(json.dumps(value))

    class Context:
        def __init__(self):
            self.saved = []

        def input_path(self, key=None):
            if key == "example-scoring":
                assert self.saved[0] == "forecast.json"
            return tmp_path/(key or "example-training")

        def save(self, name, value):
            self.saved.append(name)

    context = Context()
    result = evaluate({"identity": "example", "input_key": "example-training",
                       "payload": {"segment_id": "example"}}, context)
    assert result["passed"] is True
    assert result["prediction"]["horizontal_rms_m"] < 1e-4
    assert result["imu_samples_used"] == 0
    assert result["scientific_decision"] == "abstain"
