# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_oracle_material_charges_before_generating_and_keeps_physical_truth_separate():
    import numpy as np
    from lll.generated_noise_benchmark import material
    charges=[]
    r=material(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,reserve=lambda **w:charges.append(w))
    assert sum(v.get('generated_samples',0) for v in charges)==610
    assert sum(v.get('constructed_intervals',0) for v in charges)==600
    assert r['training_epochs']==6 and r['theta'].shape==(600,3)
    assert r['nominal_receiver'].shape==(9,3) and r['nominal_metric'].shape==(9,3)
    assert r['oracle_nominal_future_geometry_used'] is True
    assert r['initial_state_is_known'] and r['calibration_is_known']
    assert r['random_draws']==0 and np.all(r['dt']>0)


def test_oracle_constructor_rejects_unbounded_or_incomplete_inputs_before_any_charge():
    from lll.generated_noise_benchmark import material
    charges=[]
    for patch in ({'duration_s':1201.},{'queries':1200},{'query_start_s':-1.}):
        args=dict(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2);args.update(patch)
        with pytest.raises(ValueError):material(**args,reserve=lambda **w:charges.append(w))
    assert charges==[]


def test_oracle_constructor_stops_before_truth_when_construction_reservation_fails():
    from lll.generated_noise_benchmark import material
    def stop(**counts):raise RuntimeError('no allowance')
    with pytest.raises(RuntimeError,match='no allowance'):
        material(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,reserve=stop)


def test_oracle_operator_requires_declared_source_law_before_native_work():
    from lll.generated_noise_benchmark import build_operator
    with pytest.raises(ValueError):build_operator({},law='unknown',kernel=None,reserve=lambda **w:pytest.fail('native work'))
