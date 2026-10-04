# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read and write session zips (docs/FORMAT.md)."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import witmotion

SCHEMA_VERSION = 2
IMU_FILE = "imu.bin.gz"

# CSV streams written by the app. The IMU itself is imu.bin.gz, decoded by witmotion.py into
# the streams gyro, accel, mag, imu_temp and imu_volt.
STREAMS = {
    "gnss": ["t_ns", "utc_ms", "lat", "lon", "alt_m", "speed_mps", "bearing_deg", "h_acc_m",
             "v_acc_m", "speed_acc_mps", "bearing_acc_deg", "sats_used"],
}


@dataclass
class Session:
    manifest: dict
    streams: dict[str, dict[str, np.ndarray]]
    events: list[tuple[int, str, str]] = field(default_factory=list)
    sha256: str = ""
    imu_stats: dict = field(default_factory=dict)

    def phase(self, name: str) -> dict | None:
        """The last phase with this name (a redone calibration position replaces the earlier try)."""
        return next((p for p in reversed(self.manifest.get("phases", [])) if p["name"] == name), None)

    def phases(self, prefix: str) -> list[dict]:
        return [p for p in self.manifest.get("phases", []) if p["name"].startswith(prefix)]

    def slice(self, stream: str, start_ns: int, end_ns: int) -> dict[str, np.ndarray] | None:
        s = self.streams.get(stream)
        if s is None:
            return None
        m = (s["t_ns"] >= start_ns) & (s["t_ns"] < end_ns)
        return {k: v[m] for k, v in s.items()}

    def gyro_stream(self) -> str:
        return "gyro"


def _parse_csv(text: str) -> dict[str, np.ndarray]:
    lines = text.splitlines()
    header = lines[0].split(",")
    # Multi-member gzip files repeat the header once per recording phase.
    body = [ln for ln in lines[1:] if ln and not ln.startswith("t_ns")]
    if not body:
        return {n: np.array([], dtype=np.int64 if n in ("t_ns", "utc_ms") else np.float64) for n in header}
    joined = "\n".join(body)
    if ",," not in joined and not any(ln.endswith(",") for ln in body):
        # Fast path (C parser). Time columns are parsed as int64 so ns precision survives.
        ints = [i for i, n in enumerate(header) if n in ("t_ns", "utc_ms")]
        out = {}
        for i in ints:
            out[header[i]] = np.atleast_1d(np.loadtxt(io.StringIO(joined), delimiter=",", usecols=i, dtype=np.int64))
        flt = [i for i in range(len(header)) if i not in ints]
        if flt:
            arr = np.loadtxt(io.StringIO(joined), delimiter=",", usecols=flt, dtype=np.float64, ndmin=2)
            for j, i in enumerate(flt):
                out[header[i]] = arr[:, j]
        return out
    rows = [ln.split(",") for ln in body]
    out: dict[str, np.ndarray] = {}
    for i, name in enumerate(header):
        col = [r[i] if i < len(r) else "" for r in rows]
        if name in ("t_ns", "utc_ms"):
            out[name] = np.array([int(c) if c else 0 for c in col], dtype=np.int64)
        else:
            out[name] = np.array([float(c) if c else np.nan for c in col], dtype=np.float64)
    return out


# Total decompressed size read_session accepts across all streams. The ZIP's own size check doesn't
# cover this: each stream is a gzip inside the ZIP, and a tiny one can expand enormously.
MAX_DECOMPRESSED = int(os.environ.get("LLL_MAX_UNCOMPRESSED_MB", "2000")) * 1024 * 1024


class TooLarge(ValueError):
    """A session expands beyond the decompression limit."""


def bounded_gunzip(data: bytes, limit: int, keep: bool = True) -> bytes | int:
    """gzip.decompress, multi-member, that stops with TooLarge once the output passes limit bytes.
    With keep=False only the decompressed size is returned, using constant memory."""
    out, total = [], 0
    while data:
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        buf = data
        while buf:
            chunk = d.decompress(buf, 1 << 20)
            total += len(chunk)
            if total > limit:
                raise TooLarge(f"decompressed data exceeds {limit // 2**20} MB")
            if keep:
                out.append(chunk)
            buf = d.unconsumed_tail
        if not d.eof:
            raise EOFError("compressed file ended before the end-of-stream marker was reached")
        data = d.unused_data.lstrip(b"\x00")
    return b"".join(out) if keep else total


def read_session(path: str | Path, max_bytes: int | None = None) -> Session:
    raw = Path(path).read_bytes()
    zf = zipfile.ZipFile(io.BytesIO(raw))
    budget = [MAX_DECOMPRESSED if max_bytes is None else max_bytes]

    def gunzip(name):
        b = bounded_gunzip(zf.read(name), budget[0])
        budget[0] -= len(b)
        return b
    manifest = json.loads(zf.read("manifest.json"))
    streams = {}
    for name in STREAMS:
        fn = f"{name}.csv.gz"
        if fn in zf.namelist():
            streams[name] = _parse_csv(gunzip(fn).decode())
    events = []
    if "events.csv.gz" in zf.namelist():
        for ln in gunzip("events.csv.gz").decode().splitlines()[1:]:
            if ln and not ln.startswith("t_ns"):
                t, kind, *rest = ln.split(",", 2)
                events.append((int(t), kind, rest[0] if rest else ""))
    imu_stats = {}
    if IMU_FILE in zf.namelist():
        imu = json.loads(json.dumps(manifest.get("imu") or {}))
        cfg = imu.setdefault("config", {}) if isinstance(imu.get("config", {}), dict) else {}
        intended = float(cfg.get("gyro_range_dps", 2000.0))
        # Trust the range the device reported back over the one the app intended: decoding at the
        # wrong full scale would rescale every rate.
        reported, consistent = witmotion.range_from_events(events)
        if reported is not None:
            cfg["gyro_range_dps"] = reported
        acc_intended = float(cfg.get("accel_range_g", 16.0))
        acc_reported, acc_consistent = witmotion.range_from_events(events, witmotion.REG_ACC_RANGE, witmotion.ACC_RANGE_G)
        if acc_reported is not None:
            cfg["accel_range_g"] = acc_reported
        arrival, chunks = witmotion.read_records(gunzip(IMU_FILE))
        decoded, imu_stats = witmotion.decode(arrival, chunks, imu)
        imu_stats.update({"gyro_range_intended_dps": intended, "gyro_range_reported_dps": reported,
                          "gyro_range_used_dps": float(cfg.get("gyro_range_dps", intended)),
                          "gyro_range_readbacks_consistent": consistent,
                          "accel_range_intended_g": acc_intended, "accel_range_reported_g": acc_reported,
                          "accel_range_used_g": float(cfg.get("accel_range_g", acc_intended)),
                          "accel_range_readbacks_consistent": acc_consistent})
        streams.update(decoded)
    return Session(manifest, streams, events, hashlib.sha256(raw).hexdigest(), imu_stats)


def validate_manifest(m: dict, names: list[str]) -> list[str]:
    """Return a list of problems (empty = valid). Used by the upload server."""
    if not isinstance(m, dict):
        return ["manifest is not a JSON object"]
    errs = []
    if m.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"unsupported schema_version {m.get('schema_version')!r}")
    for key, typ in (("session_id", str), ("install_id", str), ("phases", list), ("device", dict)):
        if key not in m:
            errs.append(f"manifest missing {key}")
        elif not isinstance(m[key], typ):
            errs.append(f"manifest {key} must be a {typ.__name__}")
    for key in ("flight", "mount", "privacy", "quality"):
        if key in m and m[key] is not None and not isinstance(m[key], dict):
            errs.append(f"manifest {key} must be an object")
    if isinstance(m.get("phases"), list):
        for p in m["phases"]:
            if not (isinstance(p, dict) and isinstance(p.get("name"), str)
                    and all(isinstance(p.get(k), (int, float)) for k in ("start_ns", "end_ns"))):
                errs.append("each phase needs a string name and numeric start_ns/end_ns")
                break
    for key in ("session_id", "install_id"):
        if isinstance(m.get(key), str) and not 0 < len(m[key]) <= 64:
            errs.append(f"{key} must be 1-64 characters")
    if IMU_FILE not in names:
        errs.append(f"missing {IMU_FILE}")
    imu = m.get("imu")
    if not isinstance(imu, dict):
        errs.append("manifest imu must be an object")
    elif imu.get("variant") not in witmotion.VARIANTS:
        errs.append(f"manifest imu.variant must be one of {', '.join(witmotion.VARIANTS)}")
    elif imu.get("config") is not None and not isinstance(imu["config"], dict):
        errs.append("manifest imu.config must be an object")
    return errs


def _col_strings(a: np.ndarray) -> list[str]:
    a = np.asarray(a)
    if a.dtype.kind in "iu":
        return [str(v) for v in a.tolist()]
    if a.dtype == np.float32:
        # numpy's str() of a float32 scalar is the shortest round-trip text, like Kotlin's Float.toString
        return ["" if v != v else str(v) for v in a]
    return ["" if v != v else repr(v) for v in a.astype(np.float64).tolist()]


def write_session(path: str | Path, manifest: dict, streams: dict[str, dict[str, np.ndarray]],
                  events: list[tuple[int, str, str]] = (), imu=None) -> None:
    """Write a session zip. Float32 arrays are written shortest-round-trip, as the app does.
    imu = (arrival_ns, chunks) is written as imu.bin.gz, framed exactly as the app frames it."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=1))
        for name, cols in streams.items():
            header = STREAMS[name]
            strs = [_col_strings(cols[c]) for c in header]
            text = ",".join(header) + "\n" + "".join(",".join(r) + "\n" for r in zip(*strs))
            zf.writestr(f"{name}.csv.gz", gzip.compress(text.encode(), 6))
        ev = "t_ns,kind,detail\n" + "".join(f"{t},{k},{d}\n" for t, k, d in events)
        zf.writestr("events.csv.gz", gzip.compress(ev.encode(), 6))
        if imu is not None:
            zf.writestr(IMU_FILE, gzip.compress(witmotion.write_records(*imu), 6))
