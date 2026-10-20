# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest
from lll import ilvis0_control_publication as publication
from lll import ilvis0_control_shards as runner
from test_ilvis0_control_shards import fixture


def test_publication_preserves_hashes_journals_and_detects_tampering(tmp_path):
    data,_,tasks=fixture(tmp_path)
    for i,task in enumerate(tasks):
        context=runner.TaskContext(data,i,task['identity'])
        context.save('witness.json',dict(value='1/3'))
        context.finish(dict(passed=True,scientific_decision='abstain'))
    runner._finish_study(data,runner.verify(data))
    public=tmp_path/'public'
    publication.publish(data,public,'# Generated controls\n')
    publication.check(data,public)
    receipt=json.loads((public/'evidence-receipt.json').read_text())
    assert 'artifacts/task-0/witness.json' in receipt['artifacts']
    assert any('/charges/' in name for name in receipt['artifacts'])
    assert not any(name.endswith('.lock') for name in receipt['artifacts'])
    assert (public/'inputs/0000.json').read_bytes()==(data/'inputs/0000.json').read_bytes()
    (public/'README.md').write_text('changed')
    with pytest.raises(ValueError):publication.check(data,public)
