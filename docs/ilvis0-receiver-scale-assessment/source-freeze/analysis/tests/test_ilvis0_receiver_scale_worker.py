# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest
import ilvis0_receiver_scale_worker as worker


def test_future_coordinate_mutations_do_not_enter_prefix():
    selected=dict(filename='example.013',segment=dict(segment_id='id',receiver_fixes=[dict(time_s=i,
        latitude_rad=.1,longitude_rad=.2,height_m=1000.) for i in range(439)]))
    original=worker.prefix(selected,292);modified=copy.deepcopy(selected)
    for row in modified['segment']['receiver_fixes'][292:]:row['height_m']=-1e9;row['latitude_rad']=0.
    assert worker.prefix(modified,292)==original
    assert len(original['fixes'])==292


def test_saved_prefix_freeze_and_small_assessment_lifecycle(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(worker,'TRAINING_EPOCHS',16);monkeypatch.setattr(worker,'TASKS',[worker.TASKS[0]])
    worker.configure();worker.prepare();worker.verify(True);worker.base.run()
    summary=worker.base.load(worker.DATA/'summary.json')
    assert summary['passed'] and summary['charged']['native_calls']==0
    result=worker.base.load(worker.DATA/summary['results'][0]['artifact'])
    assert result['observations']==48 and not result['future_receiver_positions_used']
    assert worker.base.load(worker.PUBLIC/'summary.json')['passed']
    with pytest.raises(ValueError):worker.prepare()
    with pytest.raises(ValueError):worker.base.run()
