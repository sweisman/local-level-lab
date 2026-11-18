"""A closed study can travel without the repository-wide archive catalog."""

import hashlib
import json
from pathlib import Path
import zipfile

import pytest


def test_portable_bundle_is_deterministic_and_checks_each_artifact(tmp_path):
    from lll.studies.portable import build_bundle, verify_bundle

    public = tmp_path / 'docs' / 'study-evidence'
    (public / 'source-freeze').mkdir(parents=True)
    content = {'README.md': b'Plain-language result\n',
               'manifest.json': b'{"id":"example"}\n',
               'source-freeze/worker.py': b'print(1)\n'}
    for name, data in content.items():
        target = public / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    receipt = {'artifacts': {name: hashlib.sha256(data).hexdigest()
                             for name, data in content.items()}}
    (public / 'evidence-receipt.json').write_text(json.dumps(receipt))
    output = public / 'bundle.zip'

    first = build_bundle(tmp_path, public.relative_to(tmp_path),
                         output.relative_to(tmp_path))
    raw = output.read_bytes()
    second = build_bundle(tmp_path, public.relative_to(tmp_path),
                          output.relative_to(tmp_path))
    assert first == second
    assert output.read_bytes() == raw
    assert verify_bundle(output)['artifact_count'] == 3
    from lll.studies.portable import main
    assert main(['verify', str(output)]) == 0

    altered = public / 'altered.zip'
    with zipfile.ZipFile(output) as source, zipfile.ZipFile(altered, 'w') as target:
        for item in source.infolist():
            data = source.read(item.filename)
            target.writestr(item, b'changed' if item.filename == 'manifest.json' else data)
    with pytest.raises(ValueError, match='artifact checksum'):
        verify_bundle(altered)


def test_portable_collection_splits_and_verifies_all_artifacts(tmp_path, monkeypatch):
    from lll.studies import portable

    public = tmp_path / 'docs' / 'large-study'
    public.mkdir(parents=True)
    content = {'manifest.json': b'{"id":"large"}\n'}
    for index in range(6):
        content[f'case-{index:02d}.bin'] = bytes(
            hashlib.sha256(f'{index}:{point}'.encode()).digest()[0]
            for point in range(256))
    content['long-case.bin'] = bytes(
        hashlib.sha256(f'long:{point}'.encode()).digest()[0]
        for point in range(2400))
    for name, data in content.items():
        (public / name).write_bytes(data)
    receipt = {'artifacts': {name: hashlib.sha256(data).hexdigest()
                             for name, data in content.items()}}
    (public / 'evidence-receipt.json').write_text(json.dumps(receipt))
    monkeypatch.setattr(portable, '_MAX_BUNDLE_BYTES', 900)
    directory = public / 'portable-evidence'

    first = portable.build_collection(tmp_path, public.relative_to(tmp_path),
                                      directory.relative_to(tmp_path))
    assert first['part_count'] > 1
    assert first['artifact_count'] == len(content)
    assert portable.verify_collection(directory) == first
    assert portable.build_collection(tmp_path, public.relative_to(tmp_path),
                                     directory.relative_to(tmp_path)) == first
    parts = sorted(directory.glob('part-*.zip'))
    assert len(parts) == first['part_count']
    assert all(part.stat().st_size <= 900 for part in parts)
    from lll.studies.portable import main
    assert main(['verify-parts', str(directory)]) == 0
    extracted = tmp_path / 'restored'
    assert main(['extract-parts', str(directory), str(extracted)]) == 0
    assert {path.relative_to(extracted).as_posix(): path.read_bytes()
            for path in extracted.rglob('*') if path.is_file()} == {
                **content, 'evidence-receipt.json': (public / 'evidence-receipt.json').read_bytes()}
    with pytest.raises(ValueError, match='empty output'):
        portable.extract_collection(directory, extracted)

    with zipfile.ZipFile(parts[0]) as original:
        members = {name: original.read(name) for name in original.namelist()}
    original_part = parts[0].read_bytes()
    with zipfile.ZipFile(parts[0], 'w') as altered:
        for name, data in members.items():
            altered.writestr(name, data + b'x')
    with pytest.raises(ValueError, match='part checksum'):
        portable.verify_collection(directory)

    parts[0].write_bytes(original_part)
    with zipfile.ZipFile(parts[0], 'w') as altered:
        for name, data in members.items():
            altered.writestr(name, data + b'x' if name == next(iter(members)) else data)
    index = json.loads((directory / 'index.json').read_text())
    index['parts'][0]['sha256'] = hashlib.sha256(parts[0].read_bytes()).hexdigest()
    (directory / 'index.json').write_text(json.dumps(index))
    with pytest.raises(ValueError, match='artifact checksum'):
        portable.verify_collection(directory)
