# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import pytest


def module():
    from lll import evidence_snapshot
    return evidence_snapshot


def test_versioned_snapshot_is_immutable_and_uses_frozen_inputs(tmp_path):
    w=module();root=tmp_path/'root';root.mkdir();dest=tmp_path/'snapshot'
    (root/'source.csv').write_text('source');digest=hashlib.sha256((root/'source.csv').read_bytes()).hexdigest()
    w.create(root,dest,version='v2',inputs={'source.csv':digest},sources={},outputs={'out.csv':b'output'},summary={'role':'development'})
    assert w.check(dest)['version']=='v2'
    (root/'source.csv').write_text('later')
    w.check(dest)
    with pytest.raises(ValueError):w.check(dest,live_root=root)
    with pytest.raises(ValueError):w.create(root,dest,version='v2',inputs={},sources={},outputs={},summary={})


def test_corrupted_snapshot_does_not_publish_or_repair_itself(tmp_path):
    w=module();root=tmp_path/'root';root.mkdir();dest=tmp_path/'snapshot'
    w.create(root,dest,version='v2',inputs={},sources={},outputs={'out.csv':b'output'},summary={})
    (dest/'out.csv').write_text('changed')
    with pytest.raises(ValueError):w.publish(dest,tmp_path/'public')
    assert (dest/'out.csv').read_text()=='changed'


def test_packed_frozen_snapshot_checks_and_publishes_without_expanded_copies(tmp_path):
    from lll.studies.artifacts import ArchiveStore

    w=module()
    for name,raw in (('input.csv',b'input\n'),('source.py',b'code\n')):
        (tmp_path/name).write_bytes(raw)
    hashes={name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
            for name in ('input.csv','source.py')}
    dest=tmp_path/'docs/example'
    w.create(tmp_path,dest,version='v1',inputs={'input.csv':hashes['input.csv']},
             sources={'source.py':hashes['source.py']},
             outputs={'out.csv':b'output\n'},summary={})
    store=ArchiveStore(tmp_path)
    names=['docs/example/frozen-inputs/input.csv',
           'docs/example/source-freeze/source.py']
    store.pack(names)
    assert store.compact(names=names)==2
    assert not (dest/'frozen-inputs/input.csv').exists()
    assert w.check(dest)['version']=='v1'
    public=tmp_path/'docs/public'
    w.publish(dest,public)
    assert (public/'frozen-inputs/input.csv').read_bytes()==b'input\n'
    assert w.check(public)['version']=='v1'
    (dest/'frozen-inputs/input.csv').write_bytes(b'changed\n')
    with pytest.raises(ValueError,match='artifact hash changed'):
        w.check(dest)
    store.close()
