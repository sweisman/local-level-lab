# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read and write session zips (docs/FORMAT.md)."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SCHEMA_VERSION = 1

STREAMS = {
    "gyro_uncal": ["t_ns", "x", "y", "z", "bx", "by", "bz"],
    "gyro": ["t_ns", "x", "y", "z"],
    "accel_uncal": ["t_ns", "x", "y", "z", "bx", "by", "bz"],
    "accel": ["t_ns", "x", "y", "z"],
    "mag_uncal": ["t_ns", "x", "y", "z", "bx", "by", "bz"],
    "pressure": ["t_ns", "hpa"],
    "game_rv": ["t_ns", "x", "y", "z", "w"],
    "gnss": ["t_ns", "utc_ms", "lat", "lon", "alt_m", "speed_mps", "bearing_deg", "h_acc_m",
             "v_acc_m", "speed_acc_mps", "bearing_acc_deg", "sats_used"],
    "battery": ["t_ns", "temp_c", "level_pct", "plugged"],
}
REQUIRED_STREAMS = ("accel_uncal",)  # plus one of gyro_uncal / gyro


@dataclass
class Session:
    manifest: dict
    streams: dict[str, dict[str, np.ndarray]]
    events: list[tuple[int, str, str]] = field(default_factory=list)
    sha256: str = ""

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
        return "gyro_uncal" if "gyro_uncal" in self.streams else "gyro"


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


def read_session(path: str | Path) -> Session:
    raw = Path(path).read_bytes()
    zf = zipfile.ZipFile(io.BytesIO(raw))
    manifest = json.loads(zf.read("manifest.json"))
    streams = {}
    for name in STREAMS:
        fn = f"{name}.csv.gz"
        if fn in zf.namelist():
            streams[name] = _parse_csv(gzip.decompress(zf.read(fn)).decode())
    events = []
    if "events.csv.gz" in zf.namelist():
        for ln in gzip.decompress(zf.read("events.csv.gz")).decode().splitlines()[1:]:
            if ln and not ln.startswith("t_ns"):
                t, kind, *rest = ln.split(",", 2)
                events.append((int(t), kind, rest[0] if rest else ""))
    return Session(manifest, streams, events, hashlib.sha256(raw).hexdigest())


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
    for key in ("flight", "mount", "privacy", "quality", "sensors"):
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
    for s in REQUIRED_STREAMS:
        if f"{s}.csv.gz" not in names:
            errs.append(f"missing stream {s}")
    if "gyro_uncal.csv.gz" not in names and "gyro.csv.gz" not in names:
        errs.append("missing gyro stream")
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
                  events: list[tuple[int, str, str]] = ()) -> None:
    """Write a session zip. Float32 arrays are written shortest-round-trip, as the app does."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=1))
        for name, cols in streams.items():
            header = STREAMS[name]
            strs = [_col_strings(cols[c]) for c in header]
            text = ",".join(header) + "\n" + "".join(",".join(r) + "\n" for r in zip(*strs))
            zf.writestr(f"{name}.csv.gz", gzip.compress(text.encode(), 6))
        ev = "t_ns,kind,detail\n" + "".join(f"{t},{k},{d}\n" for t, k, d in events)
        zf.writestr("events.csv.gz", gzip.compress(ev.encode(), 6))
