# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path


def module():
    path=Path(__file__).resolve().parents[2]/'docs/paper-development-dataset-v2/build_dataset.py'
    spec=importlib.util.spec_from_file_location('paper_v2_builder',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def test_public_check_works_without_runtime_or_original_corpus(tmp_path,monkeypatch):
    w=module();public=tmp_path/'docs/paper-development-dataset-v2';old=tmp_path/w.BASE
    for path,version in ((public,'v2'),(old,'v1')):
        w.snapshot.create(tmp_path,path,version=version,inputs={},sources={},outputs={'table.csv':b'index'},summary={})
    runtime=tmp_path/'data/absent'
    monkeypatch.setattr(w,'ROOT',tmp_path);monkeypatch.setattr(w,'HERE',public);monkeypatch.setattr(w,'DATA',runtime)
    monkeypatch.setattr(w.sys,'argv',['build_dataset.py','--check-public'])
    w.main()
    assert not runtime.exists()
