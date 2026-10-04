# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound bodies before multipart parsing; shared admission across worker processes."""
import asyncio
import hashlib
import time
import uuid

from starlette.responses import JSONResponse
from starlette.formparsers import MultiPartException


class Admission:
    def __init__(self, app, store, max_bytes, concurrency=2, attempts=60):
        self.app, self.store, self.limit = app, store, max_bytes
        self.concurrency, self.attempts = concurrency, attempts
        with store.db() as c:
            c.executescript("CREATE TABLE IF NOT EXISTS upload_leases (id TEXT PRIMARY KEY, expires REAL); CREATE TABLE IF NOT EXISTS upload_attempts (ip TEXT, at REAL); CREATE TABLE IF NOT EXISTS upload_accepts (key TEXT, at REAL);")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] != "/api/v1/sessions":
            return await self.app(scope, receive, send)
        ip = hashlib.sha256(str(scope.get("client", ("?",))[0]).encode()).hexdigest()
        token, now = str(uuid.uuid4()), time.time()
        with self.store.db() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("DELETE FROM upload_leases WHERE expires<?", (now,))
            c.execute("DELETE FROM upload_attempts WHERE at<?", (now - 3600,))
            c.execute("DELETE FROM upload_accepts WHERE at<?", (now - 3600,))
            busy = c.execute("SELECT count(*) FROM upload_leases").fetchone()[0] >= self.concurrency
            limited = c.execute("SELECT count(*) FROM upload_attempts WHERE ip=?", (ip,)).fetchone()[0] >= self.attempts
            if not busy and not limited:
                c.execute("INSERT INTO upload_leases VALUES (?,?)", (token, now + 360))
                c.execute("INSERT INTO upload_attempts VALUES (?,?)", (ip, now))
        if busy or limited:
            return await JSONResponse({"detail": "upload admission limit; retry later"}, status_code=429)(scope, receive, send)
        scope.setdefault("state", {})["upload_ip"] = ip
        total = 0
        async def bounded_receive():
            nonlocal total
            message = await receive()
            total += len(message.get("body", b""))
            if total > self.limit + 65536:  # bounded multipart framing allowance
                scope["state"]["body_limit_exceeded"] = True
                raise BodyLimit("upload too large")
            return message
        async def bounded_send(message):
            if message["type"] == "http.response.start" and scope["state"].get("body_limit_exceeded"):
                message = {**message, "status": 413}
            await send(message)
        try:
            headers = dict(scope.get("headers", []))
            try:
                declared = int(headers.get(b"content-length", b"0"))
            except ValueError:
                return await JSONResponse({"detail": "invalid content length"}, status_code=400)(scope, receive, send)
            if declared > self.limit + 65536:
                raise BodyLimit("upload too large")
            async with asyncio.timeout(300):
                await self.app(scope, bounded_receive, bounded_send)
        except BodyLimit:
            await JSONResponse({"detail": "upload too large"}, status_code=413)(scope, receive, send)
        finally:
            with self.store.db() as c:
                c.execute("DELETE FROM upload_leases WHERE id=?", (token,))


class BodyLimit(MultiPartException):
    pass
