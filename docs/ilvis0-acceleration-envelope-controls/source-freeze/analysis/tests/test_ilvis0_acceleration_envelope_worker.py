# SPDX-License-Identifier: AGPL-3.0-or-later
import ilvis0_acceleration_envelope_worker as worker


def test_finite_joint_interface_lifecycle(tmp_path,monkeypatch):
    for name in ('NAME','DATA','PUBLIC','TASKS','LIMITS','SOURCE_NAMES','controls','publish'):
        monkeypatch.setattr(worker.base,name,getattr(worker.base,name))
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(worker,'TASKS',[worker.TASKS[0],worker.TASKS[3],worker.TASKS[-1]])
    worker.configure();worker.prepare();worker.base.run();worker.base.verify()
    summary=worker.base.load(worker.DATA/'summary.json')
    assert summary['passed'] and len(summary['results'])==3
    assert summary['charged']['native_calls']==0
    assert (worker.PUBLIC/'evidence-receipt.json').exists()
