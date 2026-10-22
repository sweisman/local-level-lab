# SPDX-License-Identifier: AGPL-3.0-or-later
from lll.studies.artifacts import ArchiveStore
from lll.studies.publication import archive_publication


def test_closed_publication_compacts_both_copies_and_keeps_readable_report(tmp_path):
    from test_ilvis0_control_shards import fixture
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_control_publication import publish
    output,_,tasks=fixture(tmp_path,workers=1,accounting_format='sqlite-v1')
    manifest=runner.verify(output);runner._begin(output,manifest)
    for task in tasks:
        context=runner.TaskContext(output,0,task['identity'])
        context.save('result.json',{'answer':3})
        context.finish(dict(passed=True,scientific_decision='abstain'))
    runner._finish_study(output,manifest)
    public=tmp_path/'docs/example';publish(output,public,'# Four completed bookkeeping controls\n')
    report=archive_publication(tmp_path,output,public)
    assert report['compacted_files']>0 and (public/'README.md').is_file()
    assert not (public/'source-freeze/adapter.py').exists()
    store=ArchiveStore(tmp_path)
    assert store.read('docs/example/source-freeze/adapter.py')==b'# fixture only\n'
    assert store.read('study/source-freeze/adapter.py')==b'# fixture only\n'
