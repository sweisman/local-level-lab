# SPDX-License-Identifier: AGPL-3.0-or-later
"""Export a verified publication without depending on the global pack catalog."""

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

from .artifacts import ArchiveStore, atomic, safe_path


_MAX_BUNDLE_BYTES = 32 * 1024**2


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _names(receipt):
    artifacts = receipt.get('artifacts')
    if (not isinstance(artifacts, dict) or not artifacts or
            'manifest.json' not in artifacts):
        raise ValueError('complete publication receipt required')
    for name, expected in artifacts.items():
        if not isinstance(name, str) or not name:
            raise ValueError('safe artifact name and SHA-256 required')
        path = PurePosixPath(name)
        if (path.is_absolute() or
                name != path.as_posix() or '..' in path.parts or
                name == 'evidence-receipt.json' or
                not isinstance(expected, str) or len(expected) != 64):
            raise ValueError('safe artifact name and SHA-256 required')
    return sorted(artifacts)


def _info(name):
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def verify_bundle(path):
    """Verify every member against the publication's original receipt."""
    try:
        with zipfile.ZipFile(path) as bundle:
            names = bundle.namelist()
            if len(names) != len(set(names)) or 'evidence-receipt.json' not in names:
                raise ValueError('duplicate or missing portable evidence member')
            receipt_raw = bundle.read('evidence-receipt.json')
            receipt = json.loads(receipt_raw)
            artifacts = _names(receipt)
            if set(names) != set(artifacts) | {'evidence-receipt.json'}:
                raise ValueError('portable evidence member set differs')
            for name in artifacts:
                if _digest(bundle.read(name)) != receipt['artifacts'][name]:
                    raise ValueError('portable artifact checksum mismatch: ' + name)
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as exc:
        raise ValueError('invalid portable study bundle') from exc
    raw = Path(path).read_bytes()
    return dict(artifact_count=len(artifacts), bytes=len(raw),
                sha256=_digest(raw), publication_receipt_sha256=
                _digest(receipt_raw))


def build_bundle(root, publication, output):
    """Write one deterministic portable ZIP from verified expanded or packed bytes."""
    root = Path(root).resolve()
    public = safe_path(root, Path(publication).as_posix())
    destination = safe_path(root, Path(output).as_posix())
    if not public.is_dir() or not destination.is_relative_to(public):
        raise ValueError('bundle must stay inside an existing publication')
    store = ArchiveStore(root)
    try:
        catalog = store.catalog()
        receipt_name = (public / 'evidence-receipt.json').relative_to(root).as_posix()
        receipt_raw = store._read(receipt_name, catalog)
        receipt = json.loads(receipt_raw)
        names = _names(receipt)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=False) as bundle:
            for name in names:
                source = (public / name).relative_to(root).as_posix()
                data = store._read(source, catalog)
                if _digest(data) != receipt['artifacts'][name]:
                    raise ValueError('publication artifact checksum mismatch: ' + name)
                bundle.writestr(_info(name), data)
            bundle.writestr(_info('evidence-receipt.json'), receipt_raw)
        raw = buffer.getvalue()
        if len(raw) > _MAX_BUNDLE_BYTES:
            raise ValueError('portable evidence bundle exceeds 32 MiB')
        if destination.exists():
            if destination.read_bytes() != raw:
                raise ValueError('existing portable bundle differs')
        else:
            atomic(destination, raw)
        checked = verify_bundle(destination)
        if checked['artifact_count'] != len(names):
            raise ValueError('portable evidence count changed')
        return checked
    finally:
        store.close()


def _part_bytes(artifacts):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=False) as bundle:
        for name, data in artifacts:
            bundle.writestr(_info(name), data)
    return buffer.getvalue()


def verify_collection(directory):
    """Check a multi-part publication without consulting the global catalog."""
    directory = Path(directory)
    try:
        index_raw = (directory / 'index.json').read_bytes()
        index = json.loads(index_raw)
        if index.get('format') != 'portable-study-parts-v1':
            raise ValueError('unsupported portable collection')
        receipt_raw = (directory / 'evidence-receipt.json').read_bytes()
        if _digest(receipt_raw) != index['receipt_sha256']:
            raise ValueError('publication receipt checksum mismatch')
        receipt = json.loads(receipt_raw)
        expected = set(_names(receipt))
        artifact_chunks = index['artifact_chunks']
        if set(artifact_chunks) != expected or any(
                not isinstance(chunks, list) or not chunks
                for chunks in artifact_chunks.values()):
            raise ValueError('portable artifact index invalid')
        expected_chunks = {chunk for chunks in artifact_chunks.values()
                           for chunk in chunks}
        if (len(expected_chunks) != sum(map(len, artifact_chunks.values())) or
                not all(isinstance(name, str) and name.startswith('chunk-')
                        and name.endswith('.bin') and '/' not in name
                        for name in expected_chunks)):
            raise ValueError('portable chunk index invalid')
        parts = index['parts']
        if not isinstance(parts, list) or not parts:
            raise ValueError('portable parts missing')
        chunks_seen = {}
        total_bytes = 0
        expected_files = {'index.json', 'evidence-receipt.json'}
        for number, part in enumerate(parts):
            filename = f'part-{number:03d}.zip'
            if part['file'] != filename or not isinstance(part['members'], list):
                raise ValueError('portable part index invalid')
            expected_files.add(filename)
            raw = (directory / filename).read_bytes()
            if _digest(raw) != part['sha256']:
                raise ValueError('part checksum mismatch: ' + filename)
            total_bytes += len(raw)
            with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
                members = bundle.namelist()
                if (members != part['members'] or len(members) != len(set(members))
                        or not members):
                    raise ValueError('portable part member mismatch')
                for name in members:
                    if name in chunks_seen or name not in expected_chunks:
                        raise ValueError('duplicate or unexpected portable chunk')
                    chunks_seen[name] = bundle.read(name)
        if (set(chunks_seen) != expected_chunks or
                {item.name for item in directory.iterdir()} != expected_files):
            raise ValueError('portable collection artifact set differs')
        for name in expected:
            data = b''.join(chunks_seen[chunk] for chunk in artifact_chunks[name])
            if _digest(data) != receipt['artifacts'][name]:
                raise ValueError('portable artifact checksum mismatch: ' + name)
    except (OSError, KeyError, TypeError, zipfile.BadZipFile,
            json.JSONDecodeError) as exc:
        raise ValueError('invalid portable study collection') from exc
    return dict(artifact_count=len(expected), part_count=len(parts),
                bytes=total_bytes, index_sha256=_digest(index_raw),
                publication_receipt_sha256=_digest(receipt_raw))


def build_collection(root, publication, output):
    """Split a complete receipt into deterministic, independently checked ZIPs."""
    root = Path(root).resolve()
    public = safe_path(root, Path(publication).as_posix())
    destination = safe_path(root, Path(output).as_posix())
    if not public.is_dir() or not destination.is_relative_to(public):
        raise ValueError('collection must stay inside an existing publication')
    store = ArchiveStore(root)
    try:
        catalog = store.catalog()
        receipt_name = (public / 'evidence-receipt.json').relative_to(root).as_posix()
        receipt_raw = store._read(receipt_name, catalog)
        receipt = json.loads(receipt_raw)
        names = _names(receipt)
        artifacts = []
        for name in names:
            source = (public / name).relative_to(root).as_posix()
            data = store._read(source, catalog)
            if _digest(data) != receipt['artifacts'][name]:
                raise ValueError('publication artifact checksum mismatch: ' + name)
            artifacts.append((name, data))
        limit = max(1, _MAX_BUNDLE_BYTES // 3)
        while True:
            buckets = []
            current = []
            current_size = 0
            artifact_chunks = {}
            for index, (name, data) in enumerate(artifacts):
                names_for_artifact = []
                for offset in range(0, len(data), limit):
                    if current and current_size + min(limit, len(data)-offset) > limit:
                        buckets.append(current)
                        current = []
                        current_size = 0
                    chunk_name = f'chunk-{index:06d}-{offset//limit:06d}.bin'
                    chunk = data[offset:offset+limit]
                    current.append((chunk_name, chunk))
                    current_size += len(chunk)
                    names_for_artifact.append(chunk_name)
                if not names_for_artifact:
                    chunk_name = f'chunk-{index:06d}-000000.bin'
                    current.append((chunk_name, b''))
                    names_for_artifact.append(chunk_name)
                artifact_chunks[name] = names_for_artifact
            if current:
                buckets.append(current)
            packed = [_part_bytes(bucket) for bucket in buckets]
            if all(len(raw) <= _MAX_BUNDLE_BYTES for raw in packed):
                break
            if limit == 1:
                raise ValueError('portable part limit too small for ZIP metadata')
            limit = max(1, limit // 2)
        parts = []
        payloads = {}
        for number, (bucket, raw) in enumerate(zip(buckets, packed)):
            filename = f'part-{number:03d}.zip'
            payloads[filename] = raw
            parts.append(dict(file=filename, sha256=_digest(raw),
                              members=[name for name, _ in bucket]))
        index_raw = (json.dumps(dict(format='portable-study-parts-v1',
                      receipt_sha256=_digest(receipt_raw),
                      artifact_chunks=artifact_chunks, parts=parts),
                      sort_keys=True, separators=(',', ':')) + '\n').encode()
        payloads['evidence-receipt.json'] = receipt_raw
        payloads['index.json'] = index_raw
        destination.mkdir(parents=True, exist_ok=True)
        if any(item.name not in payloads for item in destination.iterdir()):
            raise ValueError('existing portable collection contains other files')
        for filename, raw in payloads.items():
            target = destination / filename
            if target.exists():
                if target.read_bytes() != raw:
                    raise ValueError('existing portable part differs: ' + filename)
            else:
                atomic(target, raw)
        return verify_collection(destination)
    finally:
        store.close()


def extract_collection(directory, output):
    """Restore checked artifacts to a new directory for offline inspection."""
    directory = Path(directory).resolve()
    output = Path(output).resolve()
    if output == directory or output.is_relative_to(directory):
        raise ValueError('empty output outside the portable collection required')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('empty output directory required')
    checked = verify_collection(directory)
    index = json.loads((directory / 'index.json').read_bytes())
    receipt_raw = (directory / 'evidence-receipt.json').read_bytes()
    receipt = json.loads(receipt_raw)
    chunks = {}
    for part in index['parts']:
        with zipfile.ZipFile(directory / part['file']) as bundle:
            for name in part['members']:
                chunks[name] = bundle.read(name)
    output.mkdir(parents=True, exist_ok=True)
    for name in _names(receipt):
        data = b''.join(chunks[chunk] for chunk in index['artifact_chunks'][name])
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic(target, data)
    atomic(output / 'evidence-receipt.json', receipt_raw)
    return checked


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    verify = actions.add_parser('verify')
    verify.add_argument('bundle', type=Path)
    build = actions.add_parser('build')
    build.add_argument('publication', type=Path)
    build.add_argument('output', type=Path)
    build.add_argument('--root', type=Path, default=Path('.'))
    verify_parts = actions.add_parser('verify-parts')
    verify_parts.add_argument('directory', type=Path)
    build_parts = actions.add_parser('build-parts')
    build_parts.add_argument('publication', type=Path)
    build_parts.add_argument('output', type=Path)
    build_parts.add_argument('--root', type=Path, default=Path('.'))
    extract_parts = actions.add_parser('extract-parts')
    extract_parts.add_argument('directory', type=Path)
    extract_parts.add_argument('output', type=Path)
    args = parser.parse_args(argv)
    if args.action == 'verify':
        result = verify_bundle(args.bundle)
    elif args.action == 'build':
        result = build_bundle(args.root, args.publication, args.output)
    elif args.action == 'verify-parts':
        result = verify_collection(args.directory)
    elif args.action == 'extract-parts':
        result = extract_collection(args.directory, args.output)
    else:
        result = build_collection(args.root, args.publication, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
