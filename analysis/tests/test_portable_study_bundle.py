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
