# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from lll.studies.intake import preserve_completed


def test_declared_report_source_is_kept_even_without_published_receipt(tmp_path,monkeypatch):
    monkeypatch.setattr('lll.studies.intake.subprocess.check_output',lambda *a,**k:b'')
    source=tmp_path/'source';target=tmp_path/'target'
    for name,value in {
        'analysis/study-status.json':{'studies':[{'path':'data/test'}]},
        'data/test/manifest.json':{'sources':{'docs/check/build_report.py':'unused-for-live-source'}},
    }.items():
        p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value))
    report=source/'docs/check/build_report.py';report.parent.mkdir(parents=True);report.write_text('# report\n')
    (report.parent/'unrelated.txt').write_text('private')
    preserve_completed(source,target)
    assert (target/'docs/check/build_report.py').read_bytes()==report.read_bytes()
    assert not (target/'docs/check/unrelated.txt').exists()


def test_linked_public_pages_preserved_without_neighbor_scan(tmp_path):
    from lll.studies.intake import preserve_linked_pages
    source=tmp_path/'source';target=tmp_path/'target'
    page=source/'docs/known/README.md';page.parent.mkdir(parents=True);page.write_text('# Known page\n')
    (page.parent/'personal.md').write_text('private')
    assert preserve_linked_pages(source,target,['docs/known/README.md'])==1
    assert (target/'docs/known/README.md').read_bytes()==page.read_bytes()
    assert not (target/'docs/known/personal.md').exists()
