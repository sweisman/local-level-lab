# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_acceleration_cover_worker as worker


def test_shared_cover_lifecycle_keeps_all_joint_inputs(tmp_path,monkeypatch):
    for module in (worker.predecessor,worker.base):
        for name in ('NAME','DATA','PUBLIC','TASKS','LIMITS','SOURCE_NAMES','controls','publish'):
            if hasattr(module,name):monkeypatch.setattr(module,name,getattr(module,name))
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    task=dict(worker.TASKS[4],packets=100,training_times=[.2,.25],future_time=.3)
    monkeypatch.setattr(worker,'TASKS',[task]);worker.configure();worker.prepare();worker.verify(True);worker.base.run();worker.verify()
    summary=worker.base.load(worker.DATA/'summary.json');assert summary['passed']
    result=worker.base.load(worker.DATA/summary['results'][0]['artifact'])
    assert len(result['extra_artifacts'])==5 and result['future_truth_evaluated_after_bounds']
    assert result['parameter_count']==42
    training=worker.base.load(worker.DATA/('evidence/'+task['identity']+'-training.json.gz'))
    assert len(training['region']['design'][0])==42
    assert len(training['region']['lower'])==42
    assert worker.base.load(worker.PUBLIC/'case-comparison.json')['all_cases_complete'] is False
    evidence=worker.DATA/next(iter(result['extra_artifacts']))
    evidence.write_bytes(evidence.read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='side artifact'):worker.verify()
    with pytest.raises(ValueError):worker.base.run()
