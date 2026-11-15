# SPDX-License-Identifier: AGPL-3.0-or-later
"""Export a verified publication without depending on the global pack catalog."""

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

from .artifacts import ArchiveStore, atomic, safe_path


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
        if len(raw) > 32*1024**2:
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
    args = parser.parse_args(argv)
    result = (verify_bundle(args.bundle) if args.action == 'verify' else
              build_bundle(args.root, args.publication, args.output))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
