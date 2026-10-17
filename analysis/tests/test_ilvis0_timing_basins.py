# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import numpy as np
import pytest


def report():
    p=Path(__file__).resolve().parents[2]/'docs/ilvis0-timing-basins-20261017/build_report.py'
    spec=importlib.util.spec_from_file_location('timing_basin_report',p)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def endpoint(point,jac):
    return dict(normalized_parameters=list(point),active_parameters=['bias','time_offset'],
                residual=(np.array(jac)@point+np.array([1.,2.,3.])).tolist(),jacobian=jac,
                times_s=[1.],gps=[[.5,.1,1000.]])


def test_exact_linear_endpoints_agree_with_both_tangents():
    j=[[1.,0.],[0.,2.],[1.,1.]]
    a,b=endpoint([0.,0.],j),endpoint([.2,.3],j)
    r=report().compare(a,b,time_scale_s=.15)
    assert r['time_separation_s']==pytest.approx(.045)
    assert max(r['tangent_mismatch_norm'])<1e-12


@pytest.mark.parametrize('fault',['parameter_order','epochs','coordinates'])
def test_incompatible_saved_endpoints_are_rejected(fault):
    j=[[1.,0.],[0.,2.],[1.,1.]]
    a,b=endpoint([0.,0.],j),endpoint([.2,.3],j)
    if fault=='parameter_order':b['active_parameters'].reverse()
    elif fault=='epochs':b['times_s']=[2.]
    else:b['gps']=[[.6,.1,1000.]]
    with pytest.raises(ValueError):report().compare(a,b,time_scale_s=.15)


@pytest.mark.parametrize('jac,retained',[
    ([[1.,1.],[0.,0.],[0.,0.]],0.),
    ([[1.,0.],[0.,1.],[0.,0.]],1.),
])
def test_projection_detects_collinear_and_orthogonal_timing(jac,retained):
    a,b=endpoint([0.,0.],jac),endpoint([.1,.1],jac)
    r=report().compare(a,b,time_scale_s=.15)
    assert r['local_timing_retention']==pytest.approx([retained,retained],abs=1e-12)


def test_older_linearizations_use_their_separate_saved_epoch_artifact():
    saved=endpoint([0.,0.],[[1.,0.],[0.,1.],[0.,0.]])
    del saved['times_s'];del saved['gps']
    result=report().observation_context(saved,dict(times_s=[1.]),[[.5,.1,1000.]])
    assert result['times_s']==[1.] and result['gps']==[[.5,.1,1000.]]
    assert 'times_s' not in saved
    with pytest.raises(ValueError):report().observation_context(saved,dict(times_s=[1.,2.]),[[.5,.1,1000.]])
