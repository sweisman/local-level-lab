# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite geometry-aware receiver control on the same sealed pilot inputs."""


IDENTITY = "receiver-only-geodesic-control-v1"
PARENT = "data/receiver-only-forecast-baseline-v1"
PARENT_MANIFEST = "60279f90c86e2bf07b0cf8bfa23b7ec57507e140444fac8a4604a15ca65e5984"
PARENT_SUMMARY = "ee2bed425b9b47283e19792464c10c9a7fa4768c0b1b923c549d8769cedc03eb"


def recipe():
    return {
        "version": IDENTITY,
        "parent": PARENT,
        "spherical_radius_base_m": 6378137.0,
        "course": "north/east velocity fitted from last 60 training seconds",
        "position_anchor": "last observed training receiver fix",
        "height": "linear at fitted earlier up velocity",
        "workers": 1,
        "threads": 1,
        "maximum_wall_s": 600.0,
        "native_calls": 0,
        "original_reads": 0,
        "protected_reads": 0,
        "scientific_decision": "abstain",
    }


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        "analysis/lll/receiver_only_geodesic_study.py",
        "analysis/lll/receiver_only_geodesic.py",
        "analysis/tests/test_receiver_only_geodesic_study.py",
        "analysis/tests/test_receiver_only_geodesic.py",
        "docs/receiver-only-geodesic-control/PLAN.md",
    ])


def prepare(root, *, qualification):
    from pathlib import Path
    from lll.ilvis0_control_shards import runtime_environment
    from lll.receiver_only_forecast_study import tasks
    from lll.studies.artifacts import atomic, encoded, safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition

    root = Path(root).resolve()
    required = [
        "test_eastbound_high_latitude_path_has_correct_arc_and_moves_equatorward",
        "test_equatorial_receiver_track_is_extrapolated_from_earlier_positions",
        "test_geodesic_worker_saves_forecast_before_scoring",
    ]
    request, report = checked(root, qualification, sources=sources(root),
                              environment=runtime_environment(),
                              required_tests=required, minimum_tests=3)
    parent = ClosedStudy(root, PARENT)
    try:
        if (parent.completion["state"] != "complete"
                or parent.completion["manifest_sha256"] != PARENT_MANIFEST
                or parent.completion["summary_sha256"] != PARENT_SUMMARY
                or parent.summary["completed"] != 3
                or parent.summary["passed"] is not True
                or parent.manifest["limits"]["native_calls"] != 0):
            raise ValueError("exact sealed zero-native receiver baseline required")
        material = {
            "recipe": encoded(recipe()),
            "qualification-request": request,
            "qualification-report": report,
            "parent-binding": encoded({
                "prefix": PARENT,
                "manifest_sha256": PARENT_MANIFEST,
                "summary_sha256": PARENT_SUMMARY,
                "original_reads": 0,
                "protected_reads": 0,
            }),
        }
        layouts = []
        for identity in parent.tasks:
            training = parent.input(identity + "-training")
            scoring = parent.input(identity + "-scoring")
            if (set(training) != {"segment_id", "layout", "training_times",
                                  "future_times", "training_gps"}
                    or training["segment_id"] != identity
                    or scoring["segment_id"] != identity
                    or len(scoring["prediction_gps"]) != len(training["future_times"])):
                raise ValueError("unchanged separated receiver-only inputs required")
            layouts.append(training["layout"])
            material[identity + "-training"] = encoded(training)
            material[identity + "-scoring"] = encoded(scoring)
        grid = tasks(layouts)
    finally:
        parent.close()
    base = safe_path(root, "data/" + IDENTITY + "-inputs")
    if base.exists() or safe_path(root, "data/" + IDENTITY).exists():
        raise ValueError("fresh geometry-aware control required")
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(material.items()):
        path = base/f"input-{index:03d}"
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = {
        "id": IDENTITY,
        "scope": "three saved receiver-only great-circle forecasts; no IMU or original/protected reads; no shape decision",
        "adapter": "analysis/lll/receiver_only_geodesic_study.py",
        "sources": sources(root),
        "inputs": inputs,
        "tasks": grid,
        "workers": 1,
        "threads": 1,
        "maximum_wall_s": recipe()["maximum_wall_s"],
    }
    atomic(base/"definition.json", encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)


def evaluate(task, context):
    import json
    import numpy as np
    from lll.receiver_only_forecast import RADIUS_M, _wrap
    from lll.receiver_only_forecast_report import replay
    from lll.receiver_only_geodesic import forecast_geodesic

    if json.loads(context.input_path("recipe").read_bytes()) != recipe():
        raise ValueError("frozen spherical receiver rule differs")
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
    predicted = forecast_geodesic(material["training_times"],
                                  material["training_gps"], material["future_times"])
    context.save("forecast.json", {
        "segment_id": segment,
        "times": material["future_times"],
        "coordinates": predicted["coordinates"].tolist(),
        "north_east_up_velocity_mps": predicted["north_east_up_velocity_mps"].tolist(),
        "horizontal_speed_mps": predicted["horizontal_speed_mps"],
        "course_deg": predicted["course_deg"],
        "spherical_radius_m": predicted["spherical_radius_m"],
        "training_window_points": predicted["training_window_points"],
        "later_positions_used": False,
        "imu_samples_used": 0,
    })
    scoring = json.loads(context.input_path(segment + "-scoring").read_bytes())
    observed = np.asarray(scoring["prediction_gps"], dtype=float)
    prediction = predicted["coordinates"]
    if (scoring["segment_id"] != segment or observed.shape != prediction.shape
            or not np.all(np.isfinite(observed))):
        raise ValueError("complete finite separate scoring positions required")
    scale = RADIUS_M + observed[:, 2]
    errors = np.column_stack((
        (prediction[:, 0]-observed[:, 0])*scale,
        _wrap(prediction[:, 1]-observed[:, 1])*scale*np.cos(observed[:, 0]),
        prediction[:, 2]-observed[:, 2],
    ))
    if not np.all(np.isfinite(errors)):
        raise ValueError("finite signed prediction errors required")
    epochs = [{"epoch": index, "time_s": float(time),
               "north_error_m": float(error[0]), "east_error_m": float(error[1]),
               "up_error_m": float(error[2])}
              for index, (time, error) in enumerate(zip(material["future_times"], errors))]
    scores = replay(epochs)
    context.save("epochs.json", epochs)
    context.save("scores.json", scores)
    return {"passed": True, "segment_id": segment, "group_id": layout["group_id"],
            "prediction": scores, "receiver_epochs": layout["receiver_epochs"],
            "training_epochs": layout["training_epochs"],
            "prediction_epochs": layout["prediction_epochs"],
            "training_window_points": predicted["training_window_points"],
            "imu_samples_used": 0, "later_positions_used_for_forecast": False,
            "confidence_calibrated": False, "scientific_decision": "abstain"}
