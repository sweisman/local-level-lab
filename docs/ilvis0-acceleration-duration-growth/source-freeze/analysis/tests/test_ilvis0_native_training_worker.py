# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path


def test_real_generated_native_contraction_lifecycle(tmp_path,monkeypatch):
    path=Path(__file__).with_name('ilvis0_native_training_worker.py')
    spec=importlib.util.spec_from_file_location('native_training_worker',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m,'DATA',tmp_path/'runtime');monkeypatch.setattr(m,'PUBLIC',tmp_path/'public')
    task=dict(m.TASKS[0],packets=100,training_times=[.2,.25],future_time=.3)
    monkeypatch.setattr(m,'TASKS',[task]);m.configure();m.prepare();m.base.run();m.verify()
    summary=m.base.load(m.DATA/'summary.json');assert summary['passed']
    result=m.base.load(m.DATA/summary['results'][0]['artifact'])
    assert len(result['noise_cases'])==2
    assert all(r['known_truth_retained'] for r in result['noise_cases'])
    assert result['parameter_count']==27
