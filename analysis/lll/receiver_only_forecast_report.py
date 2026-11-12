# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay and publish the sealed receiver-only forecast baseline."""

import csv
import io
import math
from pathlib import Path

from lll.studies.artifacts import atomic, digest, encoded, safe_path
from lll.studies.closed import ClosedStudy


STUDY = "data/receiver-only-forecast-baseline-v1"
MANIFEST_SHA256 = "60279f90c86e2bf07b0cf8bfa23b7ec57507e140444fac8a4604a15ca65e5984"
QUALIFICATION = "docs/receiver-only-forecast-baseline/report-qualification-request.json"
FIELDS = ("segment_id", "group_id", "training_epochs", "prediction_epochs",
          "training_window_points", "prediction_span_s", "north_rms_m", "east_rms_m",
          "up_rms_m", "horizontal_rms_m", "three_dimensional_rms_m",
          "maximum_horizontal_m", "maximum_absolute_up_m")


def replay(epochs):
    if not isinstance(epochs, list) or not epochs:
        raise ValueError("nonempty saved epoch errors required")
    values = []
    previous = -math.inf
    for index, row in enumerate(epochs):
        if set(row) != {"epoch", "time_s", "north_error_m", "east_error_m", "up_error_m"}:
            raise ValueError("complete saved epoch errors required")
        time = row["time_s"]
        errors = [row[key] for key in ("north_error_m", "east_error_m", "up_error_m")]
        if (row["epoch"] != index or not isinstance(time, (int, float))
                or not math.isfinite(time) or time <= previous
                or any(not isinstance(value, (int, float)) or not math.isfinite(value)
                       for value in errors)):
            raise ValueError("finite consecutive increasing saved epochs required")
        previous = time
        values.append(errors)
    n = len(values)
    axis = [math.sqrt(math.fsum(row[k]**2 for row in values)/n) for k in range(3)]
    horizontal_squared = [row[0]**2 + row[1]**2 for row in values]
    return {
        "north_rms_m": axis[0],
        "east_rms_m": axis[1],
        "up_rms_m": axis[2],
        "horizontal_rms_m": math.sqrt(math.fsum(horizontal_squared)/n),
        "three_dimensional_rms_m": math.sqrt((math.fsum(horizontal_squared)
                                             + math.fsum(row[2]**2 for row in values))/n),
        "maximum_horizontal_m": math.sqrt(max(horizontal_squared)),
        "maximum_absolute_up_m": max(abs(row[2]) for row in values),
    }


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        "analysis/lll/receiver_only_forecast_report.py",
        "analysis/tests/test_receiver_only_forecast_report.py",
    ])


def build(root):
    root = Path(root).resolve()
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion["state"] != "complete"
                or study.completion["manifest_sha256"] != MANIFEST_SHA256
                or study.summary["completed"] != 3
                or study.summary["total"] != 3
                or study.summary["passed"] is not True
                or study.manifest["limits"]["native_calls"] != 0
                or len(study.tasks) != 3 or len(study.rows) != 3):
            raise ValueError("exact complete zero-native baseline study required")
        rows = []
        for identity in study.tasks:
            envelope = study.envelope(identity)
            result = envelope["result"]
            if (result.get("passed") is not True
                    or result.get("imu_samples_used") != 0
                    or result.get("later_positions_used_for_forecast") is not False
                    or result.get("scientific_decision") != "abstain"):
                raise ValueError("complete receiver-only abstaining result required")
            forecast = study.artifact(identity, "forecast.json")
            scores = study.artifact(identity, "scores.json")
            epochs = study.artifact(identity, "epochs.json")
            training = study.input(identity + "-training")
            if (set(training) != {"segment_id", "layout", "training_times",
                                  "future_times", "training_gps"}
                    or forecast["segment_id"] != identity
                    or forecast["imu_samples_used"] != 0
                    or forecast["later_positions_used"] is not False
                    or len(forecast["coordinates"]) != len(epochs)
                    or forecast["times"] != training["future_times"]
                    or result["training_epochs"] != len(training["training_times"])
                    or result["prediction_epochs"] != len(epochs)):
                raise ValueError("sealed input, prediction and scoring boundary differ")
            checked = replay(epochs)
            if (set(scores) != set(checked)
                    or any(not math.isclose(scores[key], value, rel_tol=1e-12, abs_tol=1e-9)
                           for key, value in checked.items())):
                raise ValueError("saved epoch errors do not reproduce score")
            rows.append({
                "segment_id": identity,
                "group_id": result["group_id"],
                "training_epochs": result["training_epochs"],
                "prediction_epochs": result["prediction_epochs"],
                "training_window_points": result["training_window_points"],
                "prediction_span_s": epochs[-1]["time_s"] - epochs[0]["time_s"],
                **checked,
            })
        if len({row["group_id"] for row in rows}) != 3:
            raise ValueError("three conservative pilot groups required")
        return {
            "study": STUDY,
            "manifest_sha256": MANIFEST_SHA256,
            "summary_sha256": study.completion["summary_sha256"],
            "rows": sorted(rows, key=lambda row: row["segment_id"]),
            "original_reads": 0,
            "protected_reads": 0,
            "new_fits": 0,
            "native_calls": 0,
            "confidence_calibrated": False,
            "scientific_decision": "abstain",
        }
    finally:
        study.close()


def publish(root, output="docs/receiver-only-forecast-baseline"):
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.qualification import checked

    root = Path(root).resolve()
    request, report = checked(root, QUALIFICATION,
                              sources=qualification_sources(root),
                              environment=runtime_environment(),
                              required_tests=["test_replay_recovers_all_saved_error_summaries",
                                              "test_replay_rejects_missing_or_nonfinite_saved_epochs"],
                              minimum_tests=2)
    result = build(root)
    output = safe_path(root, output)
    output.mkdir(parents=True, exist_ok=True)
    table = io.StringIO(newline="")
    writer = csv.DictWriter(table, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(result["rows"])
    csv_bytes = table.getvalue().encode()
    lines = [
        "# Receiver-only forecast baseline",
        "",
        "A constant-velocity line fitted to the **last 60 seconds of earlier GPS receiver positions**",
        "was extrapolated across the same withheld periods as the three-recording IMU pilot.",
        "The forecast used no IMU values and saw no withheld positions before it was saved.",
        "All three saved tasks completed with zero native model calls.",
        "",
        "| Recording | Withheld time | North RMS | East RMS | Height RMS | Horizontal RMS |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        lines.append(f"| `{row['segment_id'][:8]}…` | {row['prediction_span_s']/60:.1f} min | "
                     f"{row['north_rms_m']:.2f} m | {row['east_rms_m']:.2f} m | "
                     f"{row['up_rms_m']:.2f} m | {row['horizontal_rms_m']:.2f} m |")
    lines += [
        "",
        "This is a descriptive prediction baseline, **not an Earth-shape test**.",
        "It uses receiver coordinates and assumes constant local velocity for a minute.",
        "A difference from an IMU forecast does not identify which IMU channel caused it.",
        "The three recordings were already used for development; these results do not",
        "calibrate confidence or prove independent replication.",
        "",
        "[All scores](results.csv) · [Frozen method](PLAN.md) ·",
        "[Original IMU pilot](../ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)",
        "",
    ]
    markdown = "\n".join(lines).encode()
    receipt = {**{key: value for key, value in result.items() if key != "rows"},
               "rows": len(result["rows"]),
               "qualification_request_sha256": digest(request),
               "qualification_report_sha256": digest(report),
               "report_source_sha256": digest(Path(__file__).read_bytes()),
               "results_csv_sha256": digest(csv_bytes),
               "readme_sha256": digest(markdown)}
    atomic(output / "results.csv", csv_bytes)
    atomic(output / "README.md", markdown)
    atomic(output / "verified-report.json", encoded(receipt))
    return receipt
