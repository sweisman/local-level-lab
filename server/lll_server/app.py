# SPDX-License-Identifier: AGPL-3.0-or-later
"""Upload server for Local Level Lab session zips. Raw uploads are kept byte-for-byte and
published as an open (CC0) dataset."""
from __future__ import annotations

import hashlib
import io
import json
import os
import sqlite3
import time
import uuid
import zipfile
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from lll.format import validate_manifest

MAX_BYTES = int(os.environ.get("LLL_MAX_UPLOAD_MB", "200")) * 1024 * 1024
RATE_PER_HOUR = int(os.environ.get("LLL_UPLOADS_PER_HOUR", "20"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, sha256 TEXT UNIQUE NOT NULL, received_at REAL NOT NULL, size INTEGER NOT NULL,
  session_id TEXT, install_id TEXT, airline TEXT, flight_number TEXT, flight_date TEXT,
  mount TEXT, device_model TEXT, status TEXT NOT NULL DEFAULT 'received', manifest TEXT NOT NULL,
  result TEXT
);
"""
PUBLIC_COLS = ("id", "sha256", "received_at", "size", "session_id", "airline", "flight_number",
               "flight_date", "mount", "device_model", "status")


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        (self.root / "raw").mkdir(parents=True, exist_ok=True)
        (self.root / "reports").mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "lll.sqlite3"
        with self.db() as c:
            c.executescript(SCHEMA)

    def db(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def raw_path(self, id_: str) -> Path:
        return self.root / "raw" / f"{id_}.zip"

    def report_path(self, id_: str) -> Path:
        return self.root / "reports" / f"{id_}.report.html"

    def get(self, id_: str):
        with self.db() as c:
            return c.execute("SELECT * FROM sessions WHERE id=?", (id_,)).fetchone()

    def all(self):
        with self.db() as c:
            return c.execute("SELECT * FROM sessions ORDER BY received_at").fetchall()


def create_app(data_dir: str | Path | None = None) -> FastAPI:
    store = Store(Path(data_dir or os.environ.get("LLL_DATA", "data")))
    app = FastAPI(title="Local Level Lab", version="0.1.0")
    app.state.store = store
    recent: dict[str, deque] = defaultdict(deque)

    def limited(key: str) -> bool:
        now = time.time()
        q = recent[key]
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= RATE_PER_HOUR:
            return True
        q.append(now)
        return False

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.post("/api/v1/sessions", status_code=201)
    async def upload(file: UploadFile, request: Request):
        data = await file.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, f"upload exceeds {MAX_BYTES // 2**20} MB")
        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
            manifest = json.loads(zf.read("manifest.json"))
            names = zf.namelist()
        except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(422, "not a session zip (need a zip containing manifest.json)")
        errs = validate_manifest(manifest, names)
        if errs:
            raise HTTPException(422, "; ".join(errs))
        client = request.client.host if request.client else "?"
        if limited(str(manifest.get("install_id"))) or limited("ip:" + client):
            raise HTTPException(429, "too many uploads; try again later")
        sha = hashlib.sha256(data).hexdigest()
        with store.db() as c:
            row = c.execute("SELECT id FROM sessions WHERE sha256=?", (sha,)).fetchone()
            if row:
                return {"id": row["id"], "duplicate": True}
            id_ = str(uuid.uuid4())
            store.raw_path(id_).write_bytes(data)
            fl, mt, dv = manifest.get("flight", {}), manifest.get("mount", {}), manifest.get("device", {})
            c.execute("INSERT INTO sessions (id, sha256, received_at, size, session_id, install_id, airline, "
                      "flight_number, flight_date, mount, device_model, manifest) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (id_, sha, time.time(), len(data), manifest.get("session_id"), manifest.get("install_id"),
                       fl.get("airline"), fl.get("flight_number"), fl.get("date"), mt.get("type"),
                       dv.get("model"), json.dumps(manifest)))
        return {"id": id_, "duplicate": False}

    @app.get("/api/v1/sessions")
    def index():
        return [{k: r[k] for k in PUBLIC_COLS} for r in store.all()]

    @app.get("/api/v1/sessions/{id_}")
    def status(id_: str):
        r = store.get(id_)
        if r is None:
            raise HTTPException(404)
        out = {k: r[k] for k in PUBLIC_COLS}
        if r["result"]:
            res = json.loads(r["result"])
            out["result"] = {k: res.get(k) for k in ("flags", "cruise_minutes", "fit", "calibration")}
        return out

    @app.get("/api/v1/sessions/{id_}/raw")
    def raw(id_: str):
        if store.get(id_) is None:
            raise HTTPException(404)
        return FileResponse(store.raw_path(id_), media_type="application/zip", filename=f"{id_}.zip")

    @app.get("/api/v1/sessions/{id_}/report", response_class=HTMLResponse)
    def report(id_: str):
        p = store.report_path(id_)
        if store.get(id_) is None or not p.exists():
            raise HTTPException(404, "not processed yet")
        return HTMLResponse(p.read_text())

    @app.get("/report", response_class=HTMLResponse)
    def collated():
        p = store.root / "collated" / "collated.html"
        if not p.exists():
            raise HTTPException(404, "no collated report yet")
        return HTMLResponse(p.read_text())

    return app
