# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify two sealed GPS-only controls on identical withheld receiver epochs."""

import csv
import io
import math
from pathlib import Path

from lll.receiver_only_forecast_report import replay
from lll.studies.artifacts import atomic, digest, encoded, safe_path
from lll.studies.closed import ClosedStudy


LINEAR = "data/receiver-only-forecast-baseline-v1"
SPHERICAL = "data/receiver-only-geodesic-control-v1"
LINEAR_MANIFEST = "60279f90c86e2bf07b0cf8bfa23b7ec57507e140444fac8a4604a15ca65e5984"
SPHERICAL_MANIFEST = "01492175789b4927d306a684631a81a98010a174c20a009373336227e6108f74"
QUALIFICATION = "docs/receiver-only-geodesic-control/report-qualification-request.json"
FIELDS = ("segment_id", "group_id", "prediction_epochs", "prediction_span_s",
          "linear_north_rms_m", "linear_east_rms_m", "linear_up_rms_m",
          "linear_horizontal_rms_m", "spherical_north_rms_m",
          "spherical_east_rms_m", "spherical_up_rms_m",
          "spherical_horizontal_rms_m", "horizontal_ratio_spherical_to_linear")


def paired_row(linear, spherical):
    first, first_epochs, first_scores = linear
    second, second_epochs, second_scores = spherical
    if (not first_epochs or not second_epochs
            or [(row["epoch"], row["time_s"]) for row in first_epochs]
               != [(row["epoch"], row["time_s"]) for row in second_epochs]
            or first["segment_id"] != second["segment_id"]
            or first["group_id"] != second["group_id"]
            or first["training_epochs"] != second["training_epochs"]
            or first["prediction_epochs"] != second["prediction_epochs"]):
        raise ValueError("same withheld epochs, recording and group required")
    for result, epochs, scores in (linear, spherical):
        if (result.get("passed") is not True
                or result.get("imu_samples_used") != 0
                or result.get("later_positions_used_for_forecast") is not False
                or result.get("scientific_decision") != "abstain"):
            raise ValueError("two complete receiver-only abstaining results required")
        computed = replay(epochs)
        if (set(scores) != set(computed)
                or any(not math.isclose(scores[key], value,
                                        rel_tol=1e-12, abs_tol=1e-9)
                       for key, value in computed.items())):
            raise ValueError("saved signed errors do not reproduce scores")
    linear_horizontal = first_scores["horizontal_rms_m"]
    spherical_horizontal = second_scores["horizontal_rms_m"]
    return {
        "segment_id": first["segment_id"],
        "group_id": first["group_id"],
        "prediction_epochs": first["prediction_epochs"],
        "prediction_span_s": first_epochs[-1]["time_s"] - first_epochs[0]["time_s"],
        **{f"linear_{axis}_rms_m": first_scores[f"{axis}_rms_m"]
           for axis in ("north", "east", "up", "horizontal")},
        **{f"spherical_{axis}_rms_m": second_scores[f"{axis}_rms_m"]
           for axis in ("north", "east", "up", "horizontal")},
        "horizontal_ratio_spherical_to_linear": (
            spherical_horizontal/linear_horizontal if linear_horizontal > 0
            else (0.0 if spherical_horizontal == 0 else math.inf)),
    }


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        "analysis/lll/receiver_baseline_comparison_report.py",
        "analysis/tests/test_receiver_baseline_comparison_report.py",
    ])


def build(root):
    root = Path(root).resolve()
    first = ClosedStudy(root, LINEAR)
    second = ClosedStudy(root, SPHERICAL)
    try:
        for study, identity in ((first, LINEAR_MANIFEST), (second, SPHERICAL_MANIFEST)):
            if (study.completion["state"] != "complete"
                    or study.completion["manifest_sha256"] != identity
                    or study.summary["completed"] != 3
                    or study.summary["passed"] is not True
                    or study.manifest["limits"]["native_calls"] != 0
                    or len(study.tasks) != 3 or len(study.rows) != 3):
                raise ValueError("exact complete zero-native receiver study required")
        if set(first.tasks) != set(second.tasks):
            raise ValueError("same three selected recordings required")
        rows = []
        for identity in first.tasks:
            for suffix in ("-training", "-scoring"):
                if first.input(identity + suffix, raw=True) != second.input(identity + suffix, raw=True):
                    raise ValueError("same frozen receiver-only inputs required")
            artifacts = []
            for study in (first, second):
                result = study.envelope(identity)["result"]
                epochs = study.artifact(identity, "epochs.json")
                scores = study.artifact(identity, "scores.json")
                forecast = study.artifact(identity, "forecast.json")
                if (forecast["times"] != [row["time_s"] for row in epochs]
                        or len(forecast["coordinates"]) != len(epochs)
                        or forecast["imu_samples_used"] != 0
                        or forecast["later_positions_used"] is not False):
                    raise ValueError("sealed forecast and scored epochs differ")
                artifacts.append((result, epochs, scores))
            rows.append(paired_row(*artifacts))
        if len({row["group_id"] for row in rows}) != 3:
            raise ValueError("three conservative pilot groups required")
        return {
            "linear_manifest_sha256": LINEAR_MANIFEST,
            "spherical_manifest_sha256": SPHERICAL_MANIFEST,
            "linear_summary_sha256": first.completion["summary_sha256"],
            "spherical_summary_sha256": second.completion["summary_sha256"],
            "rows": sorted(rows, key=lambda row: row["segment_id"]),
            "original_reads": 0,
            "protected_reads": 0,
            "native_calls": 0,
            "scientific_decision": "abstain",
            "confidence_calibrated": False,
        }
    finally:
        first.close()
        second.close()


def publish(root, output="docs/receiver-only-geodesic-control"):
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.qualification import checked

    root = Path(root).resolve()
    request, report = checked(root, QUALIFICATION,
                              sources=qualification_sources(root),
                              environment=runtime_environment(),
                              required_tests=["test_pair_requires_identical_group_and_scoring_times"],
                              minimum_tests=1)
    result = build(root)
    target = safe_path(root, output)
    target.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(result["rows"])
    csv_bytes = stream.getvalue().encode()
    lines = [
        "# Two receiver-only forecasts on the same withheld positions",
        "",
        "Both controls fit speed and course using the last 60 seconds of earlier",
        "primary-receiver positions. The first extends a straight line in local",
        "coordinates; the second follows a constant-course path on a declared",
        "sphere. Neither uses IMU values or withheld positions before forecasting.",
        "All six saved tasks completed with zero native model calls.",
        "",
        "| Recording | Straight horizontal RMS | Spherical horizontal RMS | Spherical height RMS |",
        "|---|---:|---:|---:|",
    ]
    for row in result["rows"]:
        lines.append(f"| `{row['segment_id'][:8]}…` | "
                     f"{row['linear_horizontal_rms_m']:.2f} m | "
                     f"{row['spherical_horizontal_rms_m']:.2f} m | "
                     f"{row['spherical_up_rms_m']:.2f} m |")
    lines += [
        "",
        "The sphere is an assumption of this navigation control, not an",
        "independent curvature measurement. These simple forecasts cannot",
        "distinguish globe from disc or identify the gyroscope's separate",
        "contribution. The three recordings are retrospective development data,",
        "and their errors do not establish a confidence level.",
        "",
        "[All matched scores](results.csv) · [Frozen method](PLAN.md) ·",
        "[IMU prediction pilot](../ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)",
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
    atomic(target/"results.csv", csv_bytes)
    atomic(target/"README.md", markdown)
    atomic(target/"verified-report.json", encoded(receipt))
    return receipt
