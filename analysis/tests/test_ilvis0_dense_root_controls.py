# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def test_root_adapter_loads_under_the_frozen_worker_name():
    path=Path(__file__).resolve().parents[1]/'lll/ilvis0_dense_root_controls.py'
    spec=importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert callable(module.evaluate)


def test_root_setup_refuses_old_training_material():
    from lll.ilvis0_dense_root_controls import setup
    case=dict(configuration={},theta=[],dv=[],dt=[],training={})
    with pytest.raises(ValueError,match='raw generated'):
        setup(case,reserve=lambda **v:None)


def test_root_setup_uses_the_full_prior_without_training_rows():
    import numpy as np
    from lll.ilvis0_native_prefix_controls import make_case
    from lll.ilvis0_dense_root_controls import setup
    original=make_case(0,False,'physical',reserve=lambda **v:None)
    case={k:original[k] for k in ('configuration','theta','dv','dt')};counts={}
    # The sealed corpus retains a known-center tag and provenance. Neither
    # authorizes choosing an expansion point from that tag or importing a proof.
    case.update(center=[.5]*27,provenance={'source':'retained original metadata'})
    def reserve(**values):
        for k,n in values.items():counts[k]=counts.get(k,0)+n
    value=setup(case,reserve=reserve);proof=value['conditioning'].report()
    assert counts==dict(reference_setups=1,physical_proofs=1)
    assert np.array_equal(value['lower'],[-1.]*27) and np.array_equal(value['upper'],[1.]*27)
    assert np.array_equal(value['center'],[0.]*27)
    assert proof['uses_training_data'] is False and proof['applies_only_to_physical_domain'] is True
    assert proof['lower']==[-1.]*27 and proof['upper']==[1.]*27
    assert np.array_equal(value['theta'],original['theta']) and np.array_equal(value['dv'],original['dv'])
