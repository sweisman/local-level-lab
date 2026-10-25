# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded, append-only report streams with a verifiable completed prefix.

A valid prefix records completed work, never completion of an entire study.
Truncated or corrupt lines are rejected rather than silently repaired.
"""
import io
import json
import os
from pathlib import Path

from .artifacts import digest, encoded

VERSION = 'lll-report-stream-v1'


def _header(binding, maximum_records, maximum_record_bytes):
    if (not isinstance(binding, str) or not binding or len(binding) > 4096
            or type(maximum_records) is not int or not 1 <= maximum_records <= 1000000
            or type(maximum_record_bytes) is not int or not 128 <= maximum_record_bytes <= 16777216):
        raise ValueError('binding and finite record/byte limits required')
    return dict(version=VERSION, binding=binding, maximum_records=maximum_records,
                maximum_record_bytes=maximum_record_bytes)


class ReportStream:
    def __init__(self, path, *, binding, maximum_records, maximum_record_bytes):
        self.header = _header(binding, maximum_records, maximum_record_bytes)
        self.count = 0
        raw = encoded(self.header)
        self.previous = digest(raw)
        self.stream = Path(path).open('xb')
        try:
            self._write(raw)
            fd = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(fd)
            finally: os.close(fd)
        except BaseException:
            self.stream.close()
            raise

    def _write(self, raw):
        self.stream.write(raw)
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def append(self, index, value):
        if type(index) is not int or index != self.count or index >= self.header['maximum_records']:
            raise ValueError('contiguous index within frozen record limit required')
        row = dict(index=index, previous_sha256=self.previous, value=value)
        sha = digest(encoded(row))
        raw = encoded(dict(row, sha256=sha))
        if len(raw) > self.header['maximum_record_bytes']:
            raise ValueError('report exceeds frozen byte limit')
        self._write(raw)
        self.previous = sha
        self.count += 1

    def __enter__(self): return self

    def __exit__(self, *exc): self.stream.close()


def read_reports(path, *, binding, maximum_records, maximum_record_bytes):
    with Path(path).open('rb') as stream:
        return _read(stream,binding=binding,maximum_records=maximum_records,maximum_record_bytes=maximum_record_bytes)


def read_report_bytes(raw, *, binding, maximum_records, maximum_record_bytes):
    """Read a sealed archive object without expanding it into a temporary file."""
    if not isinstance(raw,bytes):raise ValueError('exact report bytes required')
    with io.BytesIO(raw) as stream:
        return _read(stream,binding=binding,maximum_records=maximum_records,maximum_record_bytes=maximum_record_bytes)


def _read(stream, *, binding, maximum_records, maximum_record_bytes):
    header = _header(binding, maximum_records, maximum_record_bytes)
    if stream is not None:
        raw = stream.readline(8193)
        if raw != encoded(header):
            raise ValueError('report header/binding/limits mismatch')
        previous = digest(raw)
        reports = []
        while raw := stream.readline(maximum_record_bytes + 1):
            if len(raw) > maximum_record_bytes:
                raise ValueError('report exceeds frozen byte limit')
            if not raw.endswith(b'\n'):
                raise ValueError('truncated report line')
            if len(reports) >= maximum_records:
                raise ValueError('report count exceeds frozen limit')
            try:
                row = json.loads(raw)
                if not isinstance(row, dict) or set(row) != {'index', 'previous_sha256', 'value', 'sha256'}:
                    raise ValueError('invalid report fields')
                sha = row.pop('sha256')
                if type(row['index']) is not int or row['index'] != len(reports):
                    raise ValueError('report index mismatch')
                if row['previous_sha256'] != previous or digest(encoded(row)) != sha:
                    raise ValueError('report hash chain mismatch')
            except (KeyError, TypeError) as error:
                raise ValueError('invalid report record') from error
            reports.append(row['value'])
            previous = sha
    return reports
