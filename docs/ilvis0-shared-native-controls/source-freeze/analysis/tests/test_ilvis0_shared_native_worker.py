# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_shared_native_worker as worker


def test_shared_native_qualification_lifecycle(tmp_path,monkeypatch):
    for module in (worker.predecessor,worker.base):
        for name in ('NAME','DATA','PUBLIC','TASKS','LIMITS','SOURCE_NAMES','controls','publish'):
            if hasattr(module,name):monkeypatch.setattr(module,name,getattr(module,name))
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    task=next(t for t in worker.TASKS if t['kind']=='boundary' and t['model']==2 and not t['profile'])
    monkeypatch.setattr(worker,'TASKS',[task]);worker.configure();worker.prepare();worker.verify(True);worker.base.run()
    summary=worker.base.load(worker.DATA/'summary.json');assert summary['passed']
    result=worker.base.load(worker.DATA/summary['results'][0]['artifact'])
    assert result['physical_parameter_count']==27 and result['enclosure_parameter_count']==33
    assert len(result['probes'])==3 and all(p['contained'] and p['shared_inside_bound'] for p in result['probes'])
    assert worker.base.load(worker.PUBLIC/'summary.json')['passed']
    with pytest.raises(ValueError):worker.base.run()
