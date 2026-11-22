# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decode an original UNIX-compressed compact RINEX observation day."""
from contextlib import contextmanager
import hashlib
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryFile


CHUNK = 1024**2
COMPRESSED_LIMIT = 48*CHUNK
COMPACT_LIMIT = 512*CHUNK
EXPANDED_LIMIT = 1024*CHUNK


def copy_bounded(source, target, maximum_bytes):
    """Hash the copied bytes. Drain a decoder to completion on overflow."""
    digest = hashlib.sha256()
    size = 0
    while chunk := source.read(CHUNK):
        size += len(chunk)
        if size <= maximum_bytes:
            target.write(chunk)
            digest.update(chunk)
    if not 0 < size <= maximum_bytes:
        raise ValueError('archive output outside its finite byte allowance')
    return size, digest.hexdigest()


def _decode(program, arguments, source, output, maximum_bytes):
    source.seek(0)
    with subprocess.Popen([str(program), *arguments], stdin=source, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL) as worker:
        size, sha = copy_bounded(worker.stdout, output, maximum_bytes)
        if worker.wait():
            raise ValueError(f'{program.name} failed to decode the complete archive')
    output.seek(0)
    return dict(bytes=size, sha256=sha)


def _binary_hash(program):
    with program.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


@contextmanager
def decode_archive(original, converter):
    """Bind two verified decoder exits to the exact original and expanded bytes."""
    gzip_cmd = shutil.which('gzip')
    if gzip_cmd is None:
        raise ValueError('gzip with UNIX compress support is required')
    gzip_cmd, converter = Path(gzip_cmd).resolve(), converter.resolve(strict=True)
    decoders = dict(gzip_sha256=_binary_hash(gzip_cmd), crx2rnx_sha256=_binary_hash(converter))
    with original.open('rb') as stream:
        data = stream.read(COMPRESSED_LIMIT+1)
    if len(data) > COMPRESSED_LIMIT or not data.startswith(b'\x1f\x9d'):
        raise ValueError('bounded original UNIX-compressed observations required')
    source = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    with TemporaryFile() as raw, TemporaryFile() as compact, TemporaryFile() as expanded:
        raw.write(data)
        del data
        compact_receipt = _decode(gzip_cmd, ['-dc'], raw, compact, COMPACT_LIMIT)
        expanded_receipt = _decode(converter, [], compact, expanded, EXPANDED_LIMIT)
        yield expanded, dict(original=source, compact=compact_receipt, expanded=expanded_receipt, decoders=decoders)
