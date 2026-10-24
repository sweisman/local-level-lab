# SPDX-License-Identifier: AGPL-3.0-or-later
"""Byte artifact lifecycle uses the real shared context and sealed hashes."""
import hashlib

import pytest

from test_ilvis0_control_shards import fixture
from lll import ilvis0_control_shards as runner


def test_binary_artifact_is_saved_and_hash_bound_without_json_conversion(tmp_path):
    output,_,_=fixture(tmp_path,workers=1)
    context=runner.TaskContext(output,0,'task-0')
    assert hasattr(context,'save_bytes'), 'shared byte artifact API is missing'
    raw=b'\x00\xff\x80\n';name=context.save_bytes('arrays/input.bin',raw)
    assert (output/name).read_bytes()==raw
    assert context.artifacts[name]==hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('bad',[{},'text',bytearray(b'bytes')])
def test_binary_artifact_rejects_implicit_serialization(tmp_path,bad):
    output,_,_=fixture(tmp_path,workers=1);context=runner.TaskContext(output,0,'task-0')
    assert hasattr(context,'save_bytes'), 'shared byte artifact API is missing'
    with pytest.raises(ValueError):context.save_bytes('input.bin',bad)
    assert not (context.directory/'input.bin').exists()


def test_binary_artifact_rejects_paths_and_sealed_context_before_writing(tmp_path):
    output,_,_=fixture(tmp_path,workers=1);context=runner.TaskContext(output,0,'task-0')
    assert hasattr(context,'save_bytes'), 'shared byte artifact API is missing'
    with pytest.raises(ValueError):context.save_bytes('../other.bin',b'bad')
    context.finished=True
    with pytest.raises(ValueError):context.save_bytes('late.bin',b'late')
    assert not (context.directory/'late.bin').exists()
