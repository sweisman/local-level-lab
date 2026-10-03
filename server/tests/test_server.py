# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from lll.synth import synthesize
from lll_server.app import create_app
from lll_server.cli import export, process


@pytest.fixture(scope="module")
def synth_zip(tmp_path_factory):
    p = tmp_path_factory.mktemp("z") / "s.zip"
    synthesize(p, "sphere_rotating", seed=2, fs=20.0)
    return p.read_bytes()


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / "data")
    return TestClient(app), app.state.store


def test_upload_process_and_publish(client, synth_zip, tmp_path):
    c, store = client
    r = c.post("/api/v1/sessions", files={"file": ("s.zip", synth_zip, "application/zip")})
    assert r.status_code == 201, r.text
    id_ = r.json()["id"]
    # same bytes again → deduplicated
    assert c.post("/api/v1/sessions", files={"file": ("s.zip", synth_zip)}).json() == {"id": id_, "duplicate": True}
    idx = c.get("/api/v1/sessions").json()
    assert len(idx) == 1 and idx[0]["sha256"] == hashlib.sha256(synth_zip).hexdigest()
    assert "install_id" not in idx[0]
    # raw download is byte-identical
    assert c.get(f"/api/v1/sessions/{id_}/raw").content == synth_zip
    assert c.get(f"/api/v1/sessions/{id_}/report").status_code == 404
    out = process(store)
    assert "processed" in out[0]
    st = c.get(f"/api/v1/sessions/{id_}").json()
    assert st["status"] == "processed" and st["result"]["fit"]["best_model"] == "sphere_rotating"
    assert c.get(f"/api/v1/sessions/{id_}/report").text.startswith("<!doctype html>")
    ex = export(store, tmp_path / "export")
    assert (ex / "SHA256SUMS").read_text().startswith(hashlib.sha256(synth_zip).hexdigest())
    assert "install_id" not in (ex / "index.json").read_text()


def test_rejects_bad_uploads(client):
    c, _ = client
    assert c.post("/api/v1/sessions", files={"file": ("x.zip", b"not a zip")}).status_code == 422
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.json", json.dumps({"schema_version": 99}))
    r = c.post("/api/v1/sessions", files={"file": ("x.zip", buf.getvalue())})
    assert r.status_code == 422 and "schema_version" in r.text


def test_size_cap(client, monkeypatch):
    import lll_server.app as appmod
    monkeypatch.setattr(appmod, "MAX_BYTES", 1000)
    c, _ = client
    assert c.post("/api/v1/sessions", files={"file": ("x.zip", b"0" * 2000)}).status_code == 413


def _zip_with(manifest_obj, extra=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest_obj))
        for name, data in (extra or {}).items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_rejects_malformed_manifest_types(client, synth_zip):
    c, _ = client
    m = json.loads(zipfile.ZipFile(io.BytesIO(synth_zip)).read("manifest.json"))
    streams = {"imu.bin.gz": b""}
    for bad in ({**m, "flight": "not an object"}, {**m, "session_id": {"x": 1}}, {**m, "phases": "nope"},
                {**m, "phases": [{"name": 3}]}, {**m, "imu": {"variant": "usb"}}, {**m, "imu": None}, [m]):
        r = c.post("/api/v1/sessions", files={"file": ("x.zip", _zip_with(bad, streams))})
        assert r.status_code == 422, r.text


def test_uncompressed_size_cap(client, synth_zip, monkeypatch):
    import lll_server.app as appmod
    monkeypatch.setattr(appmod, "MAX_UNCOMPRESSED", 1000)
    c, _ = client
    assert c.post("/api/v1/sessions", files={"file": ("s.zip", synth_zip)}).status_code == 413


def test_rate_limit_counts_only_accepted(client, synth_zip, monkeypatch):
    import lll_server.app as appmod
    monkeypatch.setattr(appmod, "RATE_PER_HOUR", 1)
    c, _ = client
    # rejected uploads don't consume quota
    assert c.post("/api/v1/sessions", files={"file": ("x.zip", b"junk")}).status_code == 422
    assert c.post("/api/v1/sessions", files={"file": ("s.zip", synth_zip)}).status_code == 201
    # a second new session from the same client is limited
    m = json.loads(zipfile.ZipFile(io.BytesIO(synth_zip)).read("manifest.json"))
    m["session_id"] = "different"
    with zipfile.ZipFile(io.BytesIO(synth_zip)) as src:
        other = _zip_with(m, {n: src.read(n) for n in src.namelist() if n != "manifest.json"})
    assert c.post("/api/v1/sessions", files={"file": ("o.zip", other)}).status_code == 429
