# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import pytest


def helper(name):
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-verified-stop-trial-20261011'/name
    spec=importlib.util.spec_from_file_location('verified_'+path.stem,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_report_uses_saved_evidence_and_checks_output_hashes(tmp_path):
    from test_ilvis0_unit_scale_report import publications
    from lll.ilvis0 import sha256
    from lll.ilvis0_saved_audit import verify_artifacts
    _,new,old=publications(tmp_path)
    for name in ('manifest.json','summary.json'):
        p=new/name; data=json.loads(p.read_text())
        data['version']='ilvis0-verified-stop-prediction-trial-v1'
        p.write_text(json.dumps(data))
    completion=json.loads((new/'completion.json').read_text())
    completion.update(summary_sha256=sha256(new/'summary.json'),manifest_sha256=sha256(new/'manifest.json'))
    (new/'completion.json').write_text(json.dumps(completion))
    receipt=json.loads((new/'evidence-receipt.json').read_text())
    for name in receipt['artifacts']: receipt['artifacts'][name]=sha256(new/name)
    (new/'evidence-receipt.json').write_text(json.dumps(receipt))
    assert len(helper('build_report.py').build(new,old))==6
    receipt=json.loads((new/'report-receipt.json').read_text())
    verify_artifacts(new,receipt)
    assert receipt['optimizer_starts']==receipt['native_predictions']==0
    text=(new/'RESULTS.md').read_text()
    assert '# Verified stopping' in text and 'verified-stop-trial-20261011/build_report.py' in text


def test_watcher_only_prepares_and_renders(monkeypatch):
    m=helper('watch_report.py'); calls=[]
    monkeypatch.setattr(m.subprocess,'run',lambda argv,**kwargs:calls.append(argv))
    m.render()
    assert len(calls)==2 and calls[0][-1]=='--prepare-only'
    assert 'ilvis0_verified_stop_trial.py' in calls[0][1]
    assert '--detach' not in calls[0]+calls[1]


def test_watcher_records_completion_without_numerical_work(tmp_path):
    m=helper('watch_report.py'); calls=[]
    m.monitor(tmp_path,ready_check=lambda:True,render=lambda:calls.append('render'))
    assert calls==['render']
    state=json.loads((tmp_path/'report-watch.json').read_text())
    assert state['state']=='complete' and not state['performs_fits']


def test_watcher_stops_on_missing_completion_without_retry(tmp_path):
    m=helper('watch_report.py')
    def forbidden(): raise AssertionError('cannot render unfinished work')
    with pytest.raises(RuntimeError,match='without completed'):
        m.monitor(tmp_path,ready_check=lambda:m.ready(tmp_path),render=forbidden)
    state=json.loads((tmp_path/'report-watch.json').read_text())
    assert state['state']=='failed' and not state['performs_fits']
