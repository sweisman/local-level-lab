# SPDX-License-Identifier: AGPL-3.0-or-later
"""Upload server for Local Level Lab session zips. Raw uploads are kept byte-for-byte and
published as an open (CC0) dataset."""
from __future__ import annotations

import hashlib
import gzip
import json
import os
import sqlite3
import time
import uuid
import zipfile
import zlib
from contextlib import contextmanager
from starlette.concurrency import run_in_threadpool
from .admission import Admission
from .stream_validation import StreamValidator
from . import registry
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from lll.format import TooLarge, bounded_gunzip, validate_manifest

MAX_BYTES = int(os.environ.get("LLL_MAX_UPLOAD_MB", "200")) * 1024 * 1024
# Declared uncompressed size of all zip members, and of manifest.json alone. Guards against
# decompression bombs: the analysis step gunzips every stream into memory.
MAX_UNCOMPRESSED = int(os.environ.get("LLL_MAX_UNCOMPRESSED_MB", "2000")) * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
RATE_PER_HOUR = int(os.environ.get("LLL_UPLOADS_PER_HOUR", "20"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, sha256 TEXT UNIQUE NOT NULL, received_at REAL NOT NULL, size INTEGER NOT NULL,
  session_id TEXT, install_id TEXT, airline TEXT, flight_number TEXT, flight_date TEXT,
  mount TEXT, seat TEXT, imu_variant TEXT, imu_unit TEXT, status TEXT NOT NULL DEFAULT 'received', manifest TEXT NOT NULL,
  result TEXT
);
"""
PUBLIC_COLS = ("id", "sha256", "received_at", "size", "session_id", "airline", "flight_number",
               "flight_date", "mount", "seat", "imu_variant", "imu_unit", "status")


def _text(v, limit: int = 200) -> str | None:
    """Index column from a manifest field: strings only, truncated; anything else is dropped."""
    return v[:limit] if isinstance(v, str) else None


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        (self.root / "raw").mkdir(parents=True, exist_ok=True)
        (self.root / "reports").mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "lll.sqlite3"
        with self.db() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def db(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        try:
            with c:
                yield c
        finally:
            c.close()

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
    from lll import __version__
    app = FastAPI(title="Local Level Lab", version=__version__)
    app.state.store = store
    registry.init(store)
    app.add_middleware(Admission, store=store, max_bytes=MAX_BYTES)

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.post("/api/v1/sessions", status_code=201)
    async def upload(request: Request):
        async with request.form(max_files=1, max_fields=0, max_part_size=65536) as form:
            file = form.get("file")
            if file is None or not hasattr(file, "file"):
                raise HTTPException(422, "one session file required")
            return await run_in_threadpool(accept_upload, file.file, request.state.upload_ip)

    def accept_upload(upload_file, ip):
        upload_file.seek(0, 2)
        size = upload_file.tell()
        upload_file.seek(0)
        if size > MAX_BYTES:
            raise HTTPException(413, "upload too large")
        try:
            zf = zipfile.ZipFile(upload_file)
            infos = zf.infolist()
            if len(infos) > 32:
                raise HTTPException(422, "too many archive members")
            if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:
                raise HTTPException(413, f"uncompressed contents exceed {MAX_UNCOMPRESSED // 2**20} MB")
            if zf.getinfo("manifest.json").file_size > MAX_MANIFEST_BYTES:
                raise HTTPException(413, "manifest.json too large")
            manifest = json.loads(zf.read("manifest.json"))
            names = [i.filename for i in infos]
            # the streams are gzips inside the zip: a tiny member can still expand enormously
            budget = MAX_UNCOMPRESSED
            for i in infos:
                if i.filename.endswith(".gz"):
                    validator = StreamValidator(i.filename)
                    with zf.open(i) as compressed, gzip.GzipFile(fileobj=compressed) as stream:
                        while chunk := stream.read(min(1024 * 1024, budget + 1)):
                            budget -= len(chunk)
                            if budget < 0:
                                raise TooLarge("expanded stream limit")
                            validator.feed(chunk)
                    validator.finish()
        except TooLarge:
            raise HTTPException(413, f"decompressed streams exceed {MAX_UNCOMPRESSED // 2**20} MB")
        except (zipfile.BadZipFile, KeyError, ValueError, UnicodeDecodeError, OSError, EOFError, zlib.error):
            raise HTTPException(422, "not a session zip (need a zip containing manifest.json)")
        errs = validate_manifest(manifest, names)
        zf.close()
        if errs:
            raise HTTPException(422, "; ".join(errs))
        upload_file.seek(0)
        digest = hashlib.sha256()
        while chunk := upload_file.read(1024 * 1024):
            digest.update(chunk)
        sha = digest.hexdigest()
        ip_key = "ip:" + ip
        install_key = "install:" + manifest["install_id"]
        stored_path = None
        try:
            with store.db() as c:
                c.execute("BEGIN IMMEDIATE")
                row = c.execute("SELECT id FROM sessions WHERE sha256=?", (sha,)).fetchone()
                if row:  # idempotent re-upload: never counted against the quota
                    return {"id": row["id"], "duplicate": True}
                if any(c.execute("SELECT count(*) FROM upload_accepts WHERE key=? AND at>?", (key, time.time() - 3600)).fetchone()[0] >= RATE_PER_HOUR for key in (ip_key, install_key)):
                    raise HTTPException(429, "too many uploads; try again later")
                id_ = str(uuid.uuid4())
                stored_path = store.raw_path(id_)
                upload_file.seek(0)
                import shutil
                with store.raw_path(id_).open("wb") as dest:
                    shutil.copyfileobj(upload_file, dest, 1024 * 1024)
                fl, mt, imu = manifest.get("flight") or {}, manifest.get("mount") or {}, manifest["imu"]
                c.execute("INSERT INTO sessions (id, sha256, received_at, size, session_id, install_id, airline, "
                          "flight_number, flight_date, mount, seat, imu_variant, imu_unit, manifest) "
                          "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (id_, sha, time.time(), size, manifest["session_id"], manifest["install_id"],
                           _text(fl.get("airline")), _text(fl.get("flight_number")), _text(fl.get("date")),
                           _text(mt.get("type")), _text(fl.get("seat")), _text(imu.get("variant")),
                           _text(imu.get("unit_id")), json.dumps(manifest)))
                c.executemany("INSERT INTO upload_accepts VALUES (?,?)", [(key, time.time()) for key in (ip_key, install_key)])
        except BaseException:
            if stored_path is not None:
                stored_path.unlink(missing_ok=True)
            raise
        return {"id": id_, "duplicate": False}

    @app.get("/api/v1/sessions")
    def index():
        trusted = registry.approvals(store)
        return [{**{k: r[k] for k in PUBLIC_COLS}, "provenance_status": "approved" if r["sha256"] in trusted else "unverified"} for r in store.all()]

    @app.get("/api/v1/sessions/{id_}")
    def status(id_: str):
        r = store.get(id_)
        if r is None:
            raise HTTPException(404)
        out = {k: r[k] for k in PUBLIC_COLS}
        approval = registry.approvals(store).get(r["sha256"])
        out["provenance_status"] = "approved" if approval else "unverified"
        out["verified_unit_id"] = approval["unit_id"] if approval else None
        if r["result"]:
            res = json.loads(r["result"])
            out["result"] = {k: res.get(k) for k in ("flags", "cruise_minutes", "fit", "calibration", "unit_quality", "slip")}
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
