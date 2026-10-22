# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import numpy as np
import pytest


def module():
    p=Path(__file__).resolve().parents[2]/'docs/ilvis0-probe-shared-map-audit/build_report.py'
    spec=importlib.util.spec_from_file_location('_shared_probe_audit',p)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def test_shared_map_comparison_keeps_first_and_last_auxiliary_columns():
    matrix=np.zeros((6,3,51));matrix[:,0,0]=2.;matrix[:,0,27]=8.;matrix[:,0,50]=4.
    point=np.zeros(27);point[0]=.5;source=np.zeros(24);source[0]=.25;source[-1]=.5
    actual=np.zeros((6,3));actual[:,0]=5.
    result=module().compare(matrix,point,source,actual)
    assert result['maximum_linear_error_m']==4. and result['maximum_shared_error_m']==0.
    assert result['physical_parameter_count']==27 and result['source_parameter_count']==24
    assert result['future_block_contributions_m'][0][0]==2.
    assert result['future_block_contributions_m'][2][0]==2.
    assert not result['conditioned_radii_transferred']


def test_partial_or_nonfinite_shared_map_is_rejected():
    with pytest.raises(ValueError):module().compare(np.zeros((6,3,50)),np.zeros(27),np.zeros(24),np.zeros((6,3)))
    source=np.zeros(24);source[0]=float('nan')
    with pytest.raises(ValueError):module().compare(np.zeros((6,3,51)),np.zeros(27),source,np.zeros((6,3)))


def test_saved_list_inputs_reconstruct_the_identical_source_reference():
    from test_ilvis0_native_box_bounds import configuration
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_sharded_native import plain
    config=configuration();theta=np.zeros((4,3));dv=np.tile([0.,0.,-.04905],(4,1));dt=np.full(4,.005)
    kwargs=dict(lower=-np.ones(27),upper=np.ones(27),center=np.zeros(27))
    before=make_reference(config,theta,dv,dt,**kwargs)
    after=make_reference(plain(config),theta.tolist(),dv.tolist(),dt.tolist(),**kwargs)
    assert plain(before.report())==plain(after.report())
