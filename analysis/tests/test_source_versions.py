# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import pytest

from lll.studies.artifacts import ArchiveStore,digest,encoded


@pytest.mark.parametrize('suffix',['.py','.c'])
def test_source_version_requires_exact_name_and_hash_in_verified_snapshot(tmp_path,suffix):
    source='analysis/lll/example'+suffix;old=b'original\n';new=b'changed\n'
    current=tmp_path/source;current.parent.mkdir(parents=True);current.write_bytes(new)
    alias='docs/study/source-freeze/'+source
    saved=tmp_path/alias;saved.parent.mkdir(parents=True);saved.write_bytes(old)
    store=ArchiveStore(tmp_path);store.pack([alias]);store.compact(names=[alias])
    read=importlib.import_module('lll.studies.source_versions').read_source
    assert read(tmp_path,source,digest(old))==old
    assert read(tmp_path,source,digest(new))==new
    with pytest.raises(ValueError):read(tmp_path,source,'0'*64)
    with pytest.raises(ValueError):read(tmp_path,'analysis/lll/other.py',digest(old))
    with pytest.raises(ValueError):read(tmp_path,'docs/result.json',digest(old))


def test_explicit_compatibility_source_is_hash_checked(tmp_path):
    source='docs/build_current_status.py';old=b'preserved helper\n'
    alias='docs/metadata-compatibility/source-freeze/'+source
    saved=tmp_path/alias;saved.parent.mkdir(parents=True);saved.write_bytes(old)
    registry=tmp_path/'repro/source-versions.json';registry.parent.mkdir()
    registry.write_bytes(encoded({source:{digest(old):alias}}))
    read=importlib.import_module('lll.studies.source_versions').read_source
    assert read(tmp_path,source,digest(old))==old
    saved.write_bytes(b'corrupt')
    with pytest.raises(ValueError):read(tmp_path,source,digest(old))
