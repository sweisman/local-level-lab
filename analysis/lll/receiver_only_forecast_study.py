# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite saved-input receiver-only baseline for the three NASA pilot tracks."""


IDENTITY = "receiver-only-forecast-baseline-v1"
PARENT_MANIFEST = "f9499a0eee0c3f9c9f997b88e1fd2e6fb9e032ff7572a5a52cd3a719bd930dbb"
PARENT_SUMMARY = "293d8de4cc3ed0efd6dc86d6807b9609195bd366742a7ede6ad3ec44e97e392d"


def recipe():
    return {
        "version": IDENTITY,
        "parent": "docs/ilvis0-retrospective-prediction-pilot-v2",
        "window_s": 60.0,
        "minimum_window_points": 30,
        "training_cut": "floor(2*N/3)",
        "workers": 1,
        "threads": 1,
        "maximum_wall_s": 600.0,
        "native_calls": 0,
        "original_reads": 0,
        "protected_reads": 0,
        "scientific_decision": "abstain",
    }


def tasks(layouts):
    if len(layouts) != 3 or len({row["segment_id"] for row in layouts}) != 3:
        raise ValueError("three original pilot recordings required")
    result = []
    for row in layouts:
        n = row["receiver_epochs"]
        cut = row["training_epochs"]
        if (type(n) is not int or n < 90 or type(cut) is not int
                or cut != 2*n//3 or row["prediction_epochs"] != n-cut
                or not row["group_id"]):
            raise ValueError("unchanged supported receiver split required")
        segment = row["segment_id"]
        result.append({
            "identity": segment,
            "input_key": segment + "-training",
            "payload": {"segment_id": segment},
            "limits": {"native_calls": 0, "packet_visits": 0,
                       "bound_calls": 0, "bound_steps": 0},
        })
    return result


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        "analysis/lll/receiver_only_forecast_study.py",
        "analysis/lll/receiver_only_forecast.py",
        "analysis/tests/test_receiver_only_forecast_study.py",
        "analysis/tests/test_receiver_only_forecast.py",
        "docs/receiver-only-forecast-baseline/PLAN.md",
    ])


def prepare(root, *, qualification):
    import gzip
    import json
    from pathlib import Path
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.artifacts import atomic, encoded, safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition

    root = Path(root).resolve()
    required = [
        "test_linear_track_is_predicted_without_future_positions",
        "test_longitude_wrap_does_not_create_a_false_turn",
        "test_short_or_nonforward_training_is_rejected",
        "test_task_grid_has_three_zero_native_tasks",
        "test_worker_saves_forecast_before_opening_separate_score",
        "test_worker_rejects_imu_values_in_training_input",
    ]
    request, report = checked(root, qualification, sources=sources(root),
                              environment=runtime_environment(),
                              required_tests=required, minimum_tests=len(required))
    parent = ClosedStudy(root, recipe()["parent"])
    try:
        if (parent.completion["state"] != "terminal"
                or parent.completion["manifest_sha256"] != PARENT_MANIFEST
                or parent.completion["summary_sha256"] != PARENT_SUMMARY
                or len(parent.tasks) != 72 or len(parent.rows) != 72):
            raise ValueError("exact sealed retrospective pilot required")
        layouts = parent.input("layouts.json")
        grid = tasks(layouts)
        material = {
            "recipe": encoded(recipe()),
            "qualification-request": request,
            "qualification-report": report,
            "parent-binding": encoded({
                "prefix": parent.prefix,
                "manifest_sha256": PARENT_MANIFEST,
                "summary_sha256": PARENT_SUMMARY,
                "original_reads": 0,
                "protected_reads": 0,
            }),
        }
        for row in layouts:
            segment = row["segment_id"]
            measurements = json.loads(gzip.decompress(parent.input(
                segment + "-measurements", raw=True)))
            scoring = parent.input(segment + "-scoring")
            cut = row["training_epochs"]
            if (measurements["segment_id"] != segment
                    or measurements["layout"] != row
                    or len(measurements["times"]) != row["receiver_epochs"]
                    or len(measurements["training_gps"]) != cut
                    or scoring["segment_id"] != segment
                    or len(scoring["prediction_gps"]) != row["prediction_epochs"]):
                raise ValueError("sealed pilot split or recording differs")
            material[segment + "-training"] = encoded({
                "segment_id": segment,
                "layout": row,
                "training_times": measurements["times"][:cut],
                "future_times": measurements["times"][cut:],
                "training_gps": measurements["training_gps"],
            })
            material[segment + "-scoring"] = encoded(scoring)
    finally:
        parent.close()
    base = safe_path(root, "data/" + IDENTITY + "-inputs")
    if base.exists() or safe_path(root, "data/" + IDENTITY).exists():
        raise ValueError("fresh finite receiver-only study required")
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(material.items()):
        path = base / f"input-{index:03d}"
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = {
        "id": IDENTITY,
        "scope": "three saved NASA receiver-only forecasts; no IMU or original/protected reads; no Earth-model decision",
        "adapter": "analysis/lll/receiver_only_forecast_study.py",
        "sources": sources(root),
        "inputs": inputs,
        "tasks": grid,
        "workers": 1,
        "threads": 1,
        "maximum_wall_s": recipe()["maximum_wall_s"],
    }
    atomic(base / "definition.json", encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)


def evaluate(task, context):
    import json
    import numpy as np
    from lll.receiver_only_forecast import RADIUS_M, _wrap, forecast

    frozen_recipe = json.loads(context.input_path("recipe").read_bytes())
    if frozen_recipe != recipe():
        raise ValueError("frozen receiver-only rule differs")
    material = json.loads(context.input_path().read_bytes())
    if set(material) != {"segment_id", "layout", "training_times", "future_times", "training_gps"}:
        raise ValueError("strict training-only receiver input required")
    segment = task["payload"]["segment_id"]
    layout = material["layout"]
    if (material["segment_id"] != segment or task["identity"] != segment
            or task["input_key"] != segment + "-training"
            or len(material["training_times"]) != layout["training_epochs"]
            or len(material["future_times"]) != layout["prediction_epochs"]
            or len(material["training_gps"]) != layout["training_epochs"]):
        raise ValueError("unchanged selected recording and split required")
    predicted = forecast(material["training_times"], material["training_gps"],
                         material["future_times"], window_s=recipe()["window_s"])
    context.save("forecast.json", {
        "segment_id": segment,
        "times": material["future_times"],
        "coordinates": predicted["coordinates"].tolist(),
        "north_east_up_velocity_mps": predicted["north_east_up_velocity_mps"].tolist(),
        "training_window_points": predicted["training_window_points"],
        "window_s": predicted["window_s"],
        "later_positions_used": False,
        "imu_samples_used": 0,
    })
    # The scoring input is unavailable until the complete forecast is saved.
    scoring = json.loads(context.input_path(segment + "-scoring").read_bytes())
    observed = np.asarray(scoring["prediction_gps"], dtype=float)
    prediction = predicted["coordinates"]
    if (scoring["segment_id"] != segment or observed.shape != prediction.shape
            or not np.all(np.isfinite(observed))):
        raise ValueError("complete finite separate scoring positions required")
    scale = RADIUS_M + observed[:, 2]
    errors = np.column_stack((
        (prediction[:, 0] - observed[:, 0]) * scale,
        _wrap(prediction[:, 1] - observed[:, 1]) * scale * np.cos(observed[:, 0]),
        prediction[:, 2] - observed[:, 2],
    ))
    if not np.all(np.isfinite(errors)):
        raise ValueError("finite signed prediction errors required")
    square = errors * errors
    rms = np.sqrt(np.mean(square, axis=0))
    horizontal = np.sqrt(np.sum(square[:, :2], axis=1))
    summary = {
        "north_rms_m": float(rms[0]),
        "east_rms_m": float(rms[1]),
        "up_rms_m": float(rms[2]),
        "horizontal_rms_m": float(np.sqrt(np.mean(horizontal * horizontal))),
        "three_dimensional_rms_m": float(np.sqrt(np.mean(np.sum(square, axis=1)))),
        "maximum_horizontal_m": float(np.max(horizontal)),
        "maximum_absolute_up_m": float(np.max(np.abs(errors[:, 2]))),
    }
    context.save("epochs.json", [
        {"epoch": i, "time_s": float(time),
         "north_error_m": float(error[0]), "east_error_m": float(error[1]),
         "up_error_m": float(error[2])}
        for i, (time, error) in enumerate(zip(material["future_times"], errors))
    ])
    context.save("scores.json", summary)
    return {"passed": True, "segment_id": segment, "group_id": layout["group_id"],
            "prediction": summary, "receiver_epochs": layout["receiver_epochs"],
            "training_epochs": layout["training_epochs"],
            "prediction_epochs": layout["prediction_epochs"],
            "training_window_points": predicted["training_window_points"],
            "imu_samples_used": 0, "later_positions_used_for_forecast": False,
            "confidence_calibrated": False, "scientific_decision": "abstain"}
