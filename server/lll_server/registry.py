# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local curator registry. No upload field can write to this registry."""
import json
import uuid
from datetime import datetime, timezone

from lll.policy import BENCH_CHECKS, provenance_reasons

SCHEMA = """
CREATE TABLE IF NOT EXISTS instruments (id TEXT PRIMARY KEY, operator TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS certificates (id TEXT PRIMARY KEY, unit TEXT NOT NULL, evidence TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals (sha TEXT PRIMARY KEY, unit TEXT NOT NULL, certificate TEXT NOT NULL, active INTEGER NOT NULL);
"""


def init(store):
    with store.db() as c:
        c.executescript(SCHEMA)


def register(store, operator):
    init(store)
    unit = str(uuid.uuid4())
    with store.db() as c:
        c.execute("INSERT INTO instruments VALUES (?,?)", (unit, operator))
    return unit


def certify(store, unit, evidence):
    init(store)
    if not all(evidence.get("checks", {}).get(k) is True for k in BENCH_CHECKS):
        raise ValueError("all bench checks must be explicitly approved")
    if evidence.get("tier") not in ("usable", "qualified"):
        raise ValueError("bench tier must be usable or qualified")
    if not {"rate_hz", "gyro_range_dps", "accel_range_g", "auto_zero"} <= evidence.get("config", {}).keys():
        raise ValueError("complete instrument configuration required")
    for key, allowed in {"rate_hz": (10, 20, 50, 100, 200), "gyro_range_dps": (250, 500, 1000, 2000), "accel_range_g": (2, 4, 8, 16)}.items():
        if evidence["config"][key] not in allowed:
            raise ValueError(f"unsupported bench configuration: {key}")
    if evidence["config"]["auto_zero"] is not False:
        raise ValueError("science certificate requires auto-zero disabled")
    sources = evidence.get("source_sha256", [])
    if not sources or any(not isinstance(s, str) or len(s) != 64 or any(x not in "0123456789abcdef" for x in s) for s in sources):
        raise ValueError("bench evidence SHA-256 hashes required")
    cert = str(uuid.uuid4())
    # Only scientific attestation fields are exported; private curator notes never are.
    evidence = {"tier": evidence["tier"], "checks": {k: True for k in BENCH_CHECKS},
                "config": {k: evidence["config"][k] for k in ("rate_hz", "gyro_range_dps", "accel_range_g", "auto_zero")},
                "source_sha256": sources, "unit_id": unit, "approved_at": datetime.now(timezone.utc).isoformat()}
    with store.db() as c:
        if not c.execute("SELECT 1 FROM instruments WHERE id=?", (unit,)).fetchone():
            raise ValueError("unknown registered instrument")
        c.execute("INSERT INTO certificates VALUES (?,?,?)", (cert, unit, json.dumps(evidence)))
    return cert


def approvals(store):
    init(store)
    with store.db() as c:
        rows = c.execute("SELECT a.sha,a.unit,c.evidence FROM approvals a JOIN certificates c ON c.id=a.certificate AND c.unit=a.unit WHERE a.active=1").fetchall()
    return {r["sha"]: {"status": "approved", "sha256": r["sha"], "unit_id": r["unit"], "bench": json.loads(r["evidence"])} for r in rows}


def approve(store, session_id, certificate):
    init(store)
    session = store.get(session_id)
    with store.db() as c:
        cert = c.execute("SELECT * FROM certificates WHERE id=?", (certificate,)).fetchone()
        if session is None or cert is None or session["status"] != "processed":
            raise ValueError("processed session and existing certificate required")
        approval = {"status": "approved", "sha256": session["sha256"], "unit_id": cert["unit"], "bench": json.loads(cert["evidence"])}
        reasons = provenance_reasons(json.loads(session["result"]), approval)
        if reasons:
            raise ValueError("; ".join(reasons))
        c.execute("INSERT OR REPLACE INTO approvals VALUES (?,?,?,1)", (session["sha256"], cert["unit"], certificate))


def revoke(store, session_id):
    init(store)
    with store.db() as c:
        c.execute("UPDATE approvals SET active=0 WHERE sha=(SELECT sha256 FROM sessions WHERE id=?)", (session_id,))
