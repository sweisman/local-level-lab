"""Export every receiver epoch from a completed, hash-verified evidence summary."""
import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(directory, output):
    completion = json.loads((directory / "completion.json").read_text())
    for name, key in (("summary.json.gz", "summary_sha256"),
                      ("manifest.json", "manifest_sha256")):
        if digest(directory / name) != completion[key]:
            raise ValueError(f"Completed evidence hash mismatch: {name}")
    summary = json.loads(gzip.decompress((directory / "summary.json.gz").read_bytes()))
    rows = []
    for result in summary["results"]:
        for record in result["receiver"]["gsof_records"]:
            row = {
                "task_id": result["task_id"], "source_file": result["filename"],
                "source_sha256": result["source_sha256"],
                "source_kind": record["source_kind"],
                "covariance_semantics": record["covariance_semantics"],
                "independently_calibrated": False,
            }
            for key in ("gps_week", "gps_week_seconds", "utc_epoch", "latitude_rad",
                        "longitude_rad", "ellipsoid_height_m", "satellites",
                        "position_flags1", "position_flags2", "initialization_counter",
                        "first_stream_offset", "last_stream_offset", "payload_sha256",
                        "pages", "transmission"):
                row[key] = record.get(key)
            row.update(record.get("reported_uncertainty", {}))
            rows.append(row)
    if not rows or len(rows) != completion["receiver_reported_sigma_epochs"]:
        raise ValueError("Receiver inventory count does not match completed evidence")
    columns = list(rows[0])
    if any(set(row) != set(columns) for row in rows):
        raise ValueError("Heterogeneous receiver inventory requires explicit handling")
    with output.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
    with gzip.open(output, "rt", newline="") as stream:
        if sum(1 for _ in csv.DictReader(stream)) != len(rows):
            raise ValueError("Written receiver inventory count mismatch")
    receipt = {
        "artifact": output.name, "artifact_sha256": digest(output), "rows": len(rows),
        "source_summary_sha256": completion["summary_sha256"],
        "source_manifest_sha256": completion["manifest_sha256"],
        "generator_sha256": digest(Path(__file__)),
        "scope": "all complete GSOF receiver epochs, not accepted Earth-science windows",
        "receiver_reported_uncertainties_independently_calibrated": False,
        "empirical_earth_fit_attempts": 0,
    }
    output.with_name("receiver-inventory.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"Exported {len(rows)} receiver epochs; SHA-256 {receipt['artifact_sha256']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export(args.directory, args.output)
