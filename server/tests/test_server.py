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
