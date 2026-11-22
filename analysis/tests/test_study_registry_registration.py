"""Prepared studies must be visible to the shared numerical thread guard."""

import json
import pytest

from lll import ilvis0_control_shards as runner
from lll.studies.runtime import Definition


def test_definition_preparation_registers_study_under_status_lock(tmp_path,monkeypatch):
    registry=tmp_path/'analysis/study-status.json'
    registry.parent.mkdir(parents=True)
    registry.write_text('{"studies":[]}')
    (tmp_path/'analysis/study-status.lock').touch()
    def prepared(output,**kwargs):
        output.mkdir(parents=True)
        (output/'manifest.json').write_text('{}')
        return {'prepared':True}
    monkeypatch.setattr(runner,'prepare',prepared)
    definition=Definition('registry-check',dict(
        adapter='adapter.py',sources=['adapter.py'],inputs={},tasks=[],
        workers=1,threads=1,maximum_wall_s=5))
    assert definition.prepare(tmp_path)=={'prepared':True}
    rows=json.loads(registry.read_bytes())['studies']
    assert rows==[{'name':'registry-check','path':'data/registry-check'}]


def test_missing_status_registry_blocks_preparation_before_freeze(tmp_path,monkeypatch):
    def forbidden(*args,**kwargs):
        raise AssertionError('preparation started without a status registry')
    monkeypatch.setattr(runner,'prepare',forbidden)
    definition=Definition('registry-check',dict(
        adapter='adapter.py',sources=['adapter.py'],inputs={},tasks=[],
        workers=1,threads=1,maximum_wall_s=5))
    with pytest.raises(ValueError,match='status registry'):
        definition.prepare(tmp_path)
