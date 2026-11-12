# SPDX-License-Identifier: AGPL-3.0-or-later
"""Outcome-blind selection of retrospective prediction-transfer groups."""

import csv
import io
import math
from pathlib import Path

from lll.ilvis0_prediction_pilot import FIELDS


def policy():
    return {
        "version": "ilvis0-prediction-group-transfer-selection-v1",
        "population": "unchanged 53 saved eligible stretches",
        "excluded": "three original prediction-pilot conservative groups",
        "categories": ["southern IMU8", "northern IMU21", "southern IMU21 before 2011", "southern IMU21 from 2015"],
        "order": "longest duration, then segment ID; one recording per conservative group",
        "model_outcomes_used": False,
        "gyro_values_used": False,
        "original_reads": 0,
        "observed_fits": 0,
        "independent_flights_established": False,
        "protected_esa_data_used": False,
    }


def select(cohort, provenance, pilot):
    if len(cohort) != 53 or len(pilot) != 3:
        raise ValueError("unchanged 53-stretch cohort and three-recording pilot required")
    lookup = {}
    for row in provenance:
        if row["archive"] != "ilvis0":
            continue
        key = row["record_id"]
        if key in lookup:
            raise ValueError("duplicate recording provenance")
        lookup[key] = row
    excluded = {row["group_id"] for row in pilot}
    if len(excluded) != 3 or not all(excluded):
        raise ValueError("distinct prior pilot provenance required")
    available = []
    seen = set()
    for row in cohort:
        item = {key: row[key] for key in FIELDS}
        identity = item["segment_id"]
        if not identity or identity in seen:
            raise ValueError("duplicate or missing saved stretch")
        seen.add(identity)
        record = lookup.get("ilvis0:" + identity)
        if (record is None or record["role"] != "retrospective_development"
                or not record["group_id"]
                or any(record[key] != item[key] for key in ("filename", "source_sha256"))):
            raise ValueError("verified retrospective provenance required")
        duration = float(item["duration_s"])
        latitude = float(item["mean_latitude_deg"])
        course = float(item["mean_course_deg"])
        minimum = float(item["minimum_ground_speed_kmh"])
        median = float(item["median_ground_speed_kmh"])
        if (not all(math.isfinite(v) for v in (duration, latitude, course, minimum, median))
                or duration < 240 or minimum < 700 or median < minimum
                or not -90 < latitude < 90 or not 0 <= course < 360
                or item["imu_type"] not in ("8", "21")
                or not all(item[key] for key in ("filename", "source_sha256", "start_utc", "end_utc"))):
            raise ValueError("saved receiver eligibility metadata required")
        item["group_id"] = record["group_id"]
        item["hemisphere"] = "north" if latitude >= 0 else "south"
        if item["group_id"] not in excluded:
            available.append(item)
    used = set(excluded)
    chosen = []
    categories = (
        lambda row: row["imu_type"] == "8" and row["hemisphere"] == "south",
        lambda row: row["imu_type"] == "21" and row["hemisphere"] == "north",
        lambda row: row["imu_type"] == "21" and row["hemisphere"] == "south" and row["start_utc"][:4] < "2011",
        lambda row: row["imu_type"] == "21" and row["hemisphere"] == "south" and row["start_utc"][:4] >= "2015",
    )
    for eligible in categories:
        candidates = (row for row in available if row["group_id"] not in used and eligible(row))
        selected = next(iter(sorted(candidates, key=lambda row: (-float(row["duration_s"]), row["segment_id"]))), None)
        if selected is None:
            raise ValueError("four distinct metadata categories and provenance groups required")
        chosen.append(selected)
        used.add(selected["group_id"])
    return chosen


def publish_selection(root, output="docs/prediction-group-transfer"):
    from lll.studies.artifacts import atomic, digest, encoded, safe_path

    root = Path(root).resolve()
    target = safe_path(root, output)
    names = (
        "docs/ilvis0-current-findings-20261015/stretch-analytics.csv",
        "docs/analysis-provenance/recording-groups.csv",
        "docs/ilvis0-prediction-pilot-preparation/selection.csv",
    )
    raw = {name: (root / name).read_bytes() for name in names}
    rows = [list(csv.DictReader(io.StringIO(raw[name].decode()))) for name in names]
    chosen = select(*rows)
    columns = (*FIELDS, "group_id", "hemisphere")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(chosen)
    selection = stream.getvalue().encode()
    receipt = {
        "policy": policy(),
        "rows": len(chosen),
        "input_sha256": {name: digest(value) for name, value in raw.items()},
        "selection_sha256": digest(selection),
        "selector_sha256": digest(Path(__file__).read_bytes()),
        "numerical_work": 0,
        "observed_fits": 0,
    }
    target.mkdir(parents=True, exist_ok=True)
    atomic(target / "selection.csv", selection)
    atomic(target / "selection-receipt.json", encoded(receipt))
    return receipt


def build_layouts(root):
    """Verify the saved selection and derive exact receiver cut times without fitting."""
    import gzip
    import json

    from lll.ilvis0_prediction_layout import prediction_layout
    from lll.studies.artifacts import ArchiveStore, digest

    root = Path(root).resolve()
    names = {
        "cohort": "docs/ilvis0-current-findings-20261015/stretch-analytics.csv",
        "provenance": "docs/analysis-provenance/recording-groups.csv",
        "pilot": "docs/ilvis0-prediction-pilot-preparation/selection.csv",
        "selection": "docs/prediction-group-transfer/selection.csv",
        "receipt": "docs/prediction-group-transfer/selection-receipt.json",
        "population": "data/ilvis0-highspeed-segments-v2-20261008/selection.json.gz",
        "context": "data/ilvis0-followup-20261007/summary.json",
    }
    store = ArchiveStore(root)
    try:
        raw = {key: store.read(path) for key, path in names.items()}
    finally:
        store.close()
    selection_receipt = json.loads(raw["receipt"])
    source_hash = digest(Path(__file__).read_bytes())
    if (digest(raw["selection"]) != selection_receipt["selection_sha256"]
            or selection_receipt["selector_sha256"] != source_hash
            or any(selection_receipt["input_sha256"][names[key]] != digest(raw[key])
                   for key in ("cohort", "provenance", "pilot"))):
        raise ValueError("saved selection provenance or selector source differs")
    parsed = {
        key: list(csv.DictReader(io.StringIO(raw[key].decode())))
        for key in ("cohort", "provenance", "pilot", "selection")
    }
    if parsed["selection"] != select(parsed["cohort"], parsed["provenance"], parsed["pilot"]):
        raise ValueError("saved selection differs from metadata-only rule")
    population = json.loads(gzip.decompress(raw["population"]))
    source = {row["segment"]["segment_id"]: row for row in population["selected"]}
    contexts = {row["task_id"]: row for row in json.loads(raw["context"])["results"]}
    layouts = [
        prediction_layout(row, source[row["segment_id"]], contexts[source[row["segment_id"]]["task"]])
        for row in parsed["selection"]
    ]
    if len(layouts) != 4 or len({row["group_id"] for row in layouts}) != 4:
        raise ValueError("four distinct saved retrospective groups required")
    return {
        "version": "ilvis0-prediction-group-transfer-layout-v1",
        "layouts": layouts,
        "input_sha256": {names[key]: digest(value) for key, value in raw.items()},
        "source_sha256": source_hash,
        "layout_source_sha256": digest(Path(prediction_layout.__code__.co_filename).read_bytes()),
        "selection": "saved metadata-only choice; first floor(2*N/3) epochs train",
        "original_reads": 0,
        "observed_starts": 0,
        "scientific_decision": "abstain",
    }


def publish_layouts(root, output="docs/prediction-group-transfer/split-receipt.json"):
    from lll.studies.artifacts import atomic, encoded, safe_path

    root = Path(root).resolve()
    target = safe_path(root, output)
    if target.exists():
        raise ValueError("fresh split receipt required")
    result = build_layouts(root)
    atomic(target, encoded(result))
    return result
