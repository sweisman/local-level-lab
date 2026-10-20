# SPDX-License-Identifier: AGPL-3.0-or-later
import ilvis0_acceleration_native_worker as worker


def test_acceleration_native_worker_retains_all_bound_blocks(tmp_path,monkeypatch):
    for module in (worker.predecessor,worker.base):
        for name in ('NAME','DATA','PUBLIC','TASKS','LIMITS','SOURCE_NAMES','controls','publish'):
            if hasattr(module,name):monkeypatch.setattr(module,name,getattr(module,name))
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(worker,'TASKS',[next(t for t in worker.TASKS if t['kind']=='boundary')])
    worker.configure();worker.prepare();worker.verify(True);worker.base.run();worker.verify()
    summary=worker.base.load(worker.DATA/'summary.json');assert summary['passed']
    result=worker.base.load(worker.DATA/summary['results'][0]['artifact'])
    assert len(result['augmented_design'][0])==42
    assert len(result['probes'][0]['normalized_common_errors'])==15
    assert len(result['bound']['acceleration_coefficients'][0])==9
    assert (worker.PUBLIC/'evidence-receipt.json').exists()
