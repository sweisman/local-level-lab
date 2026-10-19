# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest
from test_ilvis0_horizontal_repeat_probes import fixture


def module():
    p=Path(__file__).with_name('ilvis0_horizontal_timing_path.py')
    assert p.exists(), 'timing diagnostic worker missing'
    spec=importlib.util.spec_from_file_location('horizontal_timing_test',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def test_frozen_path_and_symmetric_timing_points():
    m=module();result=m.tasks(*fixture())
    assert len(result)==3 and sum(len(t['points']) for t in result)==29
    for t in result:
        points={p['method']:p['point'] for p in t['points']}
        assert points['time_primary_plus'][0]==pytest.approx(m.TIME_STEP_NORMALIZED)
        assert points['time_primary_minus'][0]==pytest.approx(-m.TIME_STEP_NORMALIZED)
        if not t['is_control']:
            assert points['path_4']==[.1,.05]
            assert points['repeat_center']==[.2,.1]
            assert points['time_repeat_plus'][0]==pytest.approx(.2+m.TIME_STEP_NORMALIZED)
    assert all(-1<=v<=1 for t in result for p in t['points'] for v in p['point'])


def test_boundary_differences_are_rejected_instead_of_clipped():
    args=fixture()
    next(r for r in args[0] if r['model']=='sphere_still')['fit']['normalized_parameters'][0]=1.
    with pytest.raises(ValueError,match='interior'):
        module().tasks(*args)


def test_changed_pair_population_is_rejected():
    args=fixture();args[1].pop()
    with pytest.raises(ValueError):module().tasks(*args)


def test_finite_difference_report_has_independent_linear_answer():
    m=module();h=.001
    center=dict(residual=[1.,2.],jacobian=[[2.,0.],[-1.,0.]])
    minus=dict(residual=[1.-2*h,2.+h]);plus=dict(residual=[1.+2*h,2.-h])
    r=m.derivative_check(center,minus,plus,index=0,step=h)
    assert r['relative_residual_derivative_error']<1e-12
    assert r['analytic_cost_derivative']==0.
    assert r['finite_difference_cost_derivative']==pytest.approx(0.,abs=1e-10)
    with pytest.raises(ValueError):m.derivative_check(center,minus,plus,index=0,step=0.)
