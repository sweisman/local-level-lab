# SPDX-License-Identifier: AGPL-3.0-or-later
import fcntl
import json
import pytest


def test_finished_shard_must_release_its_lease_before_tests_can_start(tmp_path):
    from lll.studies.testing_after import released_shard
    p=tmp_path/'shards/002';p.mkdir(parents=True)
    lock=p/'worker.lock';lock.touch()
    assert not released_shard(tmp_path,2,'freeze')
    (p/'done.json').write_text(json.dumps(dict(manifest_sha256='freeze',shard=2)))
    with lock.open('rb') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not released_shard(tmp_path,2,'freeze')
    assert released_shard(tmp_path,2,'freeze')
    with pytest.raises(ValueError,match='binding'):released_shard(tmp_path,2,'different-freeze')


def test_scheduling_requires_four_single_thread_shards(tmp_path):
    from lll.studies.testing_after import validate_wait
    manifest=dict(allocation=dict(workers=4,threads=1,total=4))
    validate_wait(manifest,[2,3],7200.)
    for shards,seconds in (([],1),([4],1),([2],float('inf')),([True],1),([2],0)):
        with pytest.raises(ValueError):validate_wait(manifest,shards,seconds)
    with pytest.raises(ValueError):validate_wait(dict(allocation=dict(workers=2,threads=2,total=4)),[1],1)
