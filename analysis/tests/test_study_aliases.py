# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path
from lll.studies.artifacts import ArchiveStore
from lll.studies.aliases import index_local_duplicates


def test_only_declared_matching_members_are_read_even_when_private_bytes_match(tmp_path,monkeypatch):
    root=tmp_path/'repo';source=tmp_path/'local';manifest=b'{"version":1}'
    for folder in (root/'docs/example',source/'data/example-20261021'):
        folder.mkdir(parents=True);(folder/'manifest.json').write_bytes(manifest)
        (folder/'inputs').mkdir();(folder/'inputs/0000.json').write_bytes(b'{}')
    data=source/'data/example-20261021';(data/'completion.json').write_text('{}')
    private=data/'inputs/personal.txt';private.write_bytes(b'{}')
    (source/'analysis').mkdir();(source/'analysis/study-status.json').write_text(json.dumps({'studies':[{'path':'data/example-20261021'}]}))
    store=ArchiveStore(root);store.pack(['docs/example/inputs/0000.json'])
    original=Path.read_bytes
    def read(path):
        assert path!=private,'unfamiliar files must remain invisible'
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',read)
    report=index_local_duplicates(root,source)
    assert report['local_duplicate_aliases']==1
    assert 'data/example-20261021/inputs/personal.txt' not in store.catalog()['paths']


def test_changed_local_member_is_preserved_and_not_aliased(tmp_path):
    root=tmp_path/'repo';source=tmp_path/'local'
    for folder in (root/'docs/example',source/'data/example-20261021'):
        folder.mkdir(parents=True);(folder/'manifest.json').write_text('{}')
        (folder/'inputs').mkdir();(folder/'inputs/0000.json').write_text('{}')
    data=source/'data/example-20261021';(data/'completion.json').write_text('{}')
    (data/'inputs/0000.json').write_text('{"local":true}')
    (source/'analysis').mkdir();(source/'analysis/study-status.json').write_text(json.dumps({'studies':[{'path':'data/example-20261021'}]}))
    store=ArchiveStore(root);store.pack(['docs/example/inputs/0000.json'])
    report=index_local_duplicates(root,source)
    assert report['local_duplicate_aliases']==0
    assert report['different_members_preserved']==1
    assert (data/'inputs/0000.json').read_text()=='{"local":true}'
