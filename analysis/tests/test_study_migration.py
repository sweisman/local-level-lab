# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
from lll.studies.artifacts import ArchiveStore
from lll.studies.migration import tracked_payloads,migrate


def fixture(root,monkeypatch):
    names=['docs/a/source-freeze/code.py','docs/a/artifacts/one.json','docs/a/README.md',
        'docs/a/results/public.csv','docs/b/source-freeze/code.py']
    for name in names:
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(b'print(42)\n' if name.endswith('.py') else b'{}\n')
    def output(args,**kwargs):
        return 'a'*40+'\n' if args[1]=='rev-parse' else ('\0'.join(names)+'\0').encode()
    monkeypatch.setattr('lll.studies.migration.subprocess.check_output',output)
    return names


def test_only_tracked_payloads_are_compacted_after_actual_restore(tmp_path,monkeypatch):
    names=fixture(tmp_path,monkeypatch)
    personal=tmp_path/'docs/a/unrelated.py';personal.write_text('leave alone')
    assert set(tracked_payloads(tmp_path))=={names[0],names[1],names[4]}
    destination=tmp_path/'restoration';report=migrate(tmp_path,restore_destination=destination)
    assert report['archived_files']==3 and report['unique_objects']==2
    assert personal.read_text()=='leave alone' and (tmp_path/names[2]).exists() and (tmp_path/names[3]).exists()
    assert not (destination/names[0]).exists()
    store=ArchiveStore(tmp_path);assert store.read(names[0])==b'print(42)\n'
    assert store.catalog()['origin_commit']=='a'*40
