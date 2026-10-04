import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from lll_server.admission import Admission
from lll_server.app import Store, create_app
from lll_server import registry
from test_server import synth_zip, client


def test_chunked_body_stops_before_multipart_ingestion(tmp_path):
    store = Store(tmp_path)
    read = 0
    sent = []
    async def inner(scope, receive, send):
        while (await receive())["more_body"]:
            pass
    async def receive():
        nonlocal read
        read += 1
        return {"type": "http.request", "body": b"x" * 10000, "more_body": True}
    async def send(message):
        sent.append(message)
    app = Admission(inner, store, max_bytes=1000)
    asyncio.run(app({"type": "http", "method": "POST", "path": "/api/v1/sessions", "client": ("ip", 1)}, receive, send))
    assert sent[0]["status"] == 413 and read == 7
    with store.db() as c:
        assert c.execute("SELECT count(*) FROM upload_leases").fetchone()[0] == 0


def test_duplicate_race_is_idempotent_across_apps(tmp_path, synth_zip, monkeypatch):
    import lll_server.app as appmod
    monkeypatch.setattr(appmod, "RATE_PER_HOUR", 1)
    apps = [create_app(tmp_path), create_app(tmp_path)]
    clients = [TestClient(a) for a in apps]
    def upload(c):
        return c.post("/api/v1/sessions", files={"file": ("s.zip", synth_zip)})
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(upload, clients))
    assert [r.status_code for r in results] == [201, 201]
    assert len({r.json()["id"] for r in results}) == 1
    assert upload(clients[1]).json()["duplicate"]
    assert len(list((tmp_path / "raw").glob("*.zip"))) == 1


def test_shared_lease_blocks_before_reading(tmp_path):
    app = create_app(tmp_path)
    c = TestClient(app)
    c.get("/health")  # initialize middleware
    with app.state.store.db() as db:
        db.executemany("INSERT INTO upload_leases VALUES (?,?)", [(str(i), time.time() + 100) for i in range(2)])
    other = TestClient(create_app(tmp_path))
    assert other.post("/api/v1/sessions", content=b"junk").status_code == 429


def test_certificate_cannot_be_backdated(tmp_path):
    from lll.policy import BENCH_CHECKS
    store = Store(tmp_path)
    unit = registry.register(store, "private operator")
    evidence = {"approved_at": "2000-01-01T00:00:00Z", "tier": "usable", "checks": dict.fromkeys(BENCH_CHECKS, True),
                "config": {"rate_hz": 100, "gyro_range_dps": 2000, "accel_range_g": 16, "auto_zero": False}, "source_sha256": ["a" * 64]}
    cert = registry.certify(store, unit, evidence)
    with store.db() as c:
        saved = json.loads(c.execute("SELECT evidence FROM certificates WHERE id=?", (cert,)).fetchone()[0])
    assert saved["approved_at"] != evidence["approved_at"]
    evidence["checks"].pop("range")
    with pytest.raises(ValueError):
        registry.certify(store, unit, evidence)
