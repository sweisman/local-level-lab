# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import pytest

from lll.studies.artifacts import ArchiveStore


def fixture(root,prefix,payload):
    folder=root/prefix;name='docs/study/inputs/0000'
    path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
    store=ArchiveStore(folder);store.pack([name]);store.compact(names=[name]);store.close()
    return name


def test_registered_bundle_is_readable_without_expansion_or_payload_copy(tmp_path):
    prefix='repro/bundle';name=fixture(tmp_path,prefix,b'exact original')
    register=importlib.import_module('lll.studies.bundles').register
    report=register(tmp_path,prefix)
    store=ArchiveStore(tmp_path)
    assert report['added_aliases']==1
    assert not (tmp_path/name).exists()
    assert store.read(name)==b'exact original'
    assert store.verify()['paths']==1
    assert all(n.startswith('bundle/repro/packs/') for n in store.catalog()['packs'])
    assert not (tmp_path/'repro/packs').exists()
    assert register(tmp_path,prefix)['added_aliases']==0


def test_bundle_cannot_replace_conflicting_registered_bytes(tmp_path):
    prefix='repro/bundle';name=fixture(tmp_path,prefix,b'other')
    p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'original')
    store=ArchiveStore(tmp_path);store.pack([name]);before=store.catalog_path.read_bytes()
    register=importlib.import_module('lll.studies.bundles').register
    with pytest.raises(ValueError,match='conflict'):register(tmp_path,prefix)
    assert store.catalog_path.read_bytes()==before
    assert store.read(name)==b'original'


def test_only_bundle_locations_inside_registered_archive_tree_are_allowed(tmp_path):
    prefix='data/elsewhere';fixture(tmp_path,prefix,b'original')
    register=importlib.import_module('lll.studies.bundles').register
    with pytest.raises(ValueError):register(tmp_path,prefix)


def test_missing_bundle_is_not_accepted_as_an_empty_registration(tmp_path):
    register=importlib.import_module('lll.studies.bundles').register
    with pytest.raises(ValueError,match='catalog'):register(tmp_path,'repro/missing')
