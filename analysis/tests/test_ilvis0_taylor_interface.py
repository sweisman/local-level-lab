# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from lll import ilvis0_taylor_native as candidate,ilvis0_transform_envelope as joint
from lll.ilvis0_directional_acceleration import DirectionalAcceleration
from lll.ilvis0_taylor_interface import bridge,training_rows
from test_ilvis0_native_box_bounds import configuration


def fixture(tmp_path):
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    source=load_stream(tmp_path)[0];derivatives=load_kernel(tmp_path)[0]
    from test_ilvis0_conditioned_transform_native import case
    config,theta,dv,dt,center,lo,hi,reference,conditioning=case(0,False)
    proof=DirectionalAcceleration(reference,lo,hi)
    report=candidate.enclose(config,theta,dv,dt,time=.05,lower=lo,upper=hi,reference=reference,
        conditioning=proof,source_kernel=source,derivative_kernel=derivatives)
    return reference,proof,report


def test_bridge_transfers_center_difference_outward_and_preserves_all_common_blocks(tmp_path):
    ref,proof,report=fixture(tmp_path);native_center=report.center.copy();native_center[0]+=1e-14
    value=bridge(report,ref,proof,native_center,[6371000.,6371000.,1.])
    assert isinstance(value,joint.TransformEnclosure)
    np.testing.assert_array_equal(value.center,native_center)
    assert F(value.unshared_remainder[0])>=F(report.unshared_remainder[0])+abs(F(report.center[0])-F(native_center[0]))
    assert value.previous_coefficients is report.previous_coefficients
    assert value.acceleration_coefficients is report.acceleration_coefficients
    assert value.transform_coefficients is report.transform_coefficients
    assert value.metadata['native_candidate_version']==candidate.VERSION


@pytest.mark.parametrize('change',['proof','center','source'])
def test_mismatched_interface_is_rejected(change,tmp_path):
    ref,proof,report=fixture(tmp_path);center=report.center.copy()
    if change=='proof':proof=DirectionalAcceleration(ref,ref.parent.lower,ref.parent.center)
    if change=='center':center[2]+=.001
    if change=='source':report.metadata['source_id']='changed'
    with pytest.raises(ValueError):bridge(report,ref,proof,center,[6371000.,6371000.,1.])


def test_training_rows_scale_all_51_columns_once_and_export_exact_bounds():
    region=dict(parameter_count=78,center=[0.]*78,coordinate_scale=[2.,3.,1.],arithmetic_allowance=.00001,
        design=[[2.]*27+[4.]*6+[6.]*9+[8.]*9,[3.]*27+[6.]*6+[9.]*9+[12.]*9,[1.]*27+[2.]*6+[3.]*9+[4.]*9])
    training=dict(region=region,times_s=[1.],observations=[[1.,2.,3.]],nominal=[[1.,2.,3.]],jacobian=[[[1.]*27]*3])
    report=dict(time_s=1.,center=[1.,2.,3.],unshared_remainder=[.5,.25,1.],
        previous_coefficients=[[2.]*6]*3,acceleration_coefficients=[[3.]*9]*3,transform_coefficients=[[4.]*9]*3)
    rows=training_rows(training,[report])
    assert rows['design'][:3]==[r+[0.]*27 for r in region['design']]
    assert len(rows['design'])==6
    assert rows['upper'][0]>=1.00101
    assert rows['upper'][1]>=.75101
    assert rows['upper'][2]>=1.00101
    report['previous_coefficients'][0][0]=0
    with pytest.raises(ValueError,match='coefficient'):training_rows(training,[report])
