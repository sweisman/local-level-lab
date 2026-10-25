# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import math
import pytest


def material():
    names=['gyro_bias_z','accel_gain_y','gravity_delta','time_offset']
    limits=dict(gyro_bias_z=math.radians(1)/3600,accel_gain_y=.02,gravity_delta=.1,time_offset=.01)
    point=[-1.,1.,-.5,0.]
    return dict(active_parameters=names,normalized_parameters=point,
        parameters={k:u*limits[k] for k,u in zip(names,point)},active_bounds=names[:2],
        gradient=[.01,-.02,0.,0.],converged=False),limits


def test_boundary_diagnostic_keeps_units_gradient_signs_and_original_fit():
    from lll.calibration_diagnostics import fit_parameters
    f,limits=material();before=copy.deepcopy(f)
    rows=fit_parameters(f,limits,profile=False,reference={'gyro_bias_z':math.radians(.25)/3600})
    assert f==before and len(rows)==4
    assert rows[0]['boundary']=='lower' and rows[0]['outward_descent_gradient']==.01
    assert rows[1]['boundary']=='upper' and rows[1]['outward_descent_gradient']==.02
    assert rows[0]['reference_value']==pytest.approx(.25)
    assert rows[0]['value']==pytest.approx(-1.) and rows[0]['reference_inside_bounds']
    assert rows[0]['error_in_bound_units']==pytest.approx(-1.25)
    assert rows[2]['reference_value'] is None and rows[2]['outward_descent_gradient'] is None


def test_boundary_diagnostic_exposes_inward_descent_without_relabeling():
    from lll.calibration_diagnostics import fit_parameters
    f,limits=material();f['gradient'][0]=-.01
    row=fit_parameters(f,limits,profile=False,reference={})[0]
    assert row['outward_descent_gradient']==-.01
    assert f['converged'] is False


def test_boundary_diagnostic_rejects_inconsistent_or_nonfinite_saved_values():
    from lll.calibration_diagnostics import fit_parameters
    f,limits=material()
    for patch in ({'gradient':[0.]},{'gradient':[0.,0.,float('nan'),0.]},
                  {'active_bounds':[]},{'parameters':dict(f['parameters'],gyro_bias_z=0.)}):
        with pytest.raises(ValueError):fit_parameters(dict(f,**patch),limits,profile=False,reference={})


def test_reference_comparison_excludes_initializer_dependent_coordinates():
    from lll.calibration_diagnostics import fit_parameters
    f,limits=material()
    for reference in ({'gravity_delta':.01},{'attitude_x':.01},{'gyro_bias_z':float('nan')}):
        with pytest.raises(ValueError):fit_parameters(f,limits,profile=False,reference=reference)
    row=fit_parameters(f,limits,profile=False,reference={'gyro_bias_z':limits['gyro_bias_z']*2})[0]
    assert not row['reference_inside_bounds']


def test_frozen_reference_evaluates_only_the_saved_calibration_function():
    from lll.calibration_diagnostics import frozen_reference
    source=b"raise RuntimeError('no top-level execution')\ndef _parameters(sign):\n return dict(gyro_bias_z=sign*math.radians(.25)/3600,gravity_delta=sign*.01,attitude_x=2.)\n"
    assert frozen_reference(source,-1)=={'gyro_bias_z':-math.radians(.25)/3600}
    for bad in (b'def other(sign): return {}',b'def _parameters(sign): return unknown()',
                b'def _parameters(sign): return dict(gyro_bias_z=float("nan"))'):
        with pytest.raises(ValueError):frozen_reference(bad,1)


def test_calibration_summary_counts_parameter_boundaries_without_independence_claim():
    from lll.calibration_diagnostics import summarize
    f,limits=material()
    rows=fit_parameters_for_summary(f,limits)
    result=summarize([dict(identity='a',parameters=rows),dict(identity='b',parameters=rows)])
    z=next(r for r in result if r['parameter']=='gyro_bias_z')
    assert z['fits']==2 and z['lower']==2 and z['upper']==0 and z['interior']==0
    assert z['median_value']==pytest.approx(-1.)


def fit_parameters_for_summary(f,limits):
    from lll.calibration_diagnostics import fit_parameters
    return fit_parameters(f,limits,profile=False,reference={})


def test_saved_jacobian_cosines_identify_aligned_orthogonal_and_zero_columns():
    from lll.calibration_diagnostics import column_cosines
    linear=dict(active_parameters=['a','b','c','d'],jacobian=[[1.,-2.,0.,0.],[0.,0.,3.,0.]])
    pairs=[('a','b'),('a','c'),('a','d')]
    values=column_cosines(linear,pairs=pairs)
    assert [v['cosine'] for v in values]==[-1.,0.,None]
    with pytest.raises(ValueError):column_cosines(dict(linear,jacobian=[[float('nan')]*4]),pairs=pairs)
    with pytest.raises(ValueError):column_cosines(linear,pairs=[('a','missing')])
