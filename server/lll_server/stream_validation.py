# SPDX-License-Identifier: AGPL-3.0-or-later
"""Incremental stream framing checks, without materializing decompressed files."""
import math
import struct

from lll.format import STREAMS


class StreamValidator:
    def __init__(self, name):
        self.binary = name == "imu.bin.gz"
        self.header = ("t_ns,kind,detail" if name == "events.csv.gz" else
                       ",".join(STREAMS["gnss"]) if name == "gnss.csv.gz" else None)
        self.buffer = b""
        self.rows = 0
        self.last = -1

    def feed(self, chunk):
        if not self.binary and self.header is None:
            return
        self.buffer += chunk
        if self.binary:
            offset = 0
            while len(self.buffer) - offset >= 10:
                t, n = struct.unpack_from("<qH", self.buffer, offset)
                if n == 0 or t < self.last:
                    raise ValueError("invalid IMU record timestamp/length")
                if len(self.buffer) - offset < 10 + n:
                    break
                self.last = t
                self.rows += 1
                offset += 10 + n
            self.buffer = self.buffer[offset:]
            return
        lines = self.buffer.split(b"\n")
        self.buffer = lines.pop()
        for raw in lines:
            if len(raw) > 65536:
                raise ValueError("CSV line too long")
            line = raw.decode("ascii").rstrip("\r")
            if line == self.header:
                self.rows += 1
                continue
            fields = line.split(",")
            if self.rows == 0 or len(fields) != len(self.header.split(",")):
                raise ValueError("invalid CSV header/columns")
            t = int(fields[0])
            if not self.last <= t < 2**63:
                raise ValueError("invalid CSV timestamp order")
            self.last = t
            if self.header.startswith("t_ns,utc_ms"):
                values = [float(v) if v else None for v in fields[1:]]
                if any(v is not None and not math.isfinite(v) for v in values):
                    raise ValueError("nonfinite GNSS value")
                if not fields[1].isdigit() or not 0 <= int(fields[1]) < 2**63:
                    raise ValueError("invalid GNSS UTC timestamp")
                if values[1] is None or values[2] is None or not -90 <= values[1] <= 90 or not -180 <= values[2] <= 180:
                    raise ValueError("invalid GNSS coordinates")
            self.rows += 1
        if len(self.buffer) > 65536:
            raise ValueError("CSV line too long")

    def finish(self):
        if self.buffer or (self.binary or self.header) and self.rows == 0:
            raise ValueError("empty or truncated stream")
