# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_acceleration_duration_worker as worker


def test_duration_screen_keeps_raw_predictions_bounds_and_probes(tmp_path,monkeypatch):
    for name in ('NAME','DATA','PUBLIC','TASKS','LIMITS','SOURCE_NAMES','controls','publish'):
        monkeypatch.setattr(worker.base,name,getattr(worker.base,name))
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(worker,'TASKS',[dict(worker.TASKS[4],prefixes=[100],times_s=[.3])])
    worker.configure();worker.prepare();worker.verify(True);worker.base.run();worker.verify()
    summary=worker.base.load(worker.DATA/'summary.json');assert summary['passed']
    assert summary['charged']['native_calls']==4 and summary['charged']['packet_visits']==400
    row=worker.base.load(worker.DATA/summary['results'][0]['artifact'])
    assert len(row['prefixes'][0]['native'])==4 and len(row['prefixes'][0]['probes'])==3
    assert row['prefixes'][0]['bound']['enclosure_parameter_count']==42
    assert (worker.PUBLIC/'evidence-receipt.json').exists()
    with pytest.raises(ValueError):worker.base.run()
