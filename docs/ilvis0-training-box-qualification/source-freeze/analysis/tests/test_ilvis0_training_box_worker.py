# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path


def test_actual_qualification_worker_freezes_reservations_and_results(tmp_path,monkeypatch):
    path=Path(__file__).with_name('ilvis0_training_box_worker.py')
    spec=importlib.util.spec_from_file_location('box_worker',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m,'DATA',tmp_path/'runtime');monkeypatch.setattr(m,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(m,'TASKS',[m.TASKS[-1]])
    m.configure();m.base.prepare();m.base.run();m.base.verify()
    summary=m.base.load(m.DATA/'summary.json');assert summary['passed']
    result=m.base.load(m.DATA/summary['results'][0]['artifact'])
    assert result['exact_feasible_points_retained']==64 and result['parameter_count']==27
    assert (m.DATA/'affine-reservations'/m.TASKS[-1]['identity']).with_suffix('.json').exists()
