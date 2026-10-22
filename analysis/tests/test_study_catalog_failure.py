# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from lll.studies.artifacts import ArchiveStore


def test_missing_catalog_cannot_turn_existing_archive_into_empty_success(tmp_path):
    name='docs/example/results/a.json';path=tmp_path/name
    path.parent.mkdir(parents=True);path.write_text('{}')
    store=ArchiveStore(tmp_path);store.pack([name]);store.compact()
    store.catalog_path.unlink()
    with pytest.raises(ValueError,match='missing.*catalog'):store.verify()
    with pytest.raises(ValueError,match='missing.*catalog'):store.read(name)
