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
