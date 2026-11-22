"""Training-only cuts and independent later-path solver comparisons."""

import numpy as np
import pytest

from lll import ilvis0_solver_forecast_controls as controls


def test_training_cut_cannot_pass_later_receiver_positions_to_solver():
    fixture=dict(gps_times=np.arange(24,dtype=float),
                 gps=np.arange(72,dtype=float).reshape(24,3),
                 truth={'gyro_bias_z':.1},model='sphere_rotating')
    train,query,later=controls.split_fixture(fixture)
    assert train['gps_times'].shape==(16,)
    assert train['gps'].shape==(16,3)
    assert query['gps_times'].shape==(24,)
    assert np.all(query['gps'][16:]==0.)
    assert np.array_equal(later,fixture['gps'][16:])
    assert fixture['gps'][16,0]!=query['gps'][16,0]


def test_pair_gate_requires_all_four_stops_and_close_later_paths():
    base=np.zeros((8,3))
    rows=[dict(identity=f'fit-{i}',converged=True,
               training_cost=.01,known_cost=.01,
               metric=[6371000.,6371000.,1.],
               later_path=base.tolist()) for i in range(4)]
    assert controls.compare_rows(rows)['passed']
    rows[3]['later_path']=(base+np.array([0.,0.,.11])).tolist()
    assert not controls.compare_rows(rows)['passed']
    rows[3]['later_path']=base.tolist()
    rows[1]['converged']=False
    assert not controls.compare_rows(rows)['passed']
    with pytest.raises(ValueError):
        controls.compare_rows(rows[:3])
