# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import numpy as np
import pytest


def test_contraction_is_fixed_and_represented_feasibility_is_exact():
    from lll.ilvis0_density_native_probes import contracted_point
    proposal=['0']*27;proposal[0]=str(F(.1));proposal[1]='1'
    row=[10.,0.]+[0.]*25;future=[[0.,2.]+[0.]*25]*3
    value=contracted_point(proposal,[row],future)
    assert value['point'][1]==.99 and value['contraction']==.99
    assert F(value['maximum_affine_training_change_m'])<=1
    assert F(value['linear_future_change_m'][0])==2*F(.99)
    proposal[0]='1'
    with pytest.raises(ValueError):contracted_point(proposal,[row],future)


def test_future_error_does_not_enter_training_feasibility():
    from lll.ilvis0_density_native_probes import metrics
    baseline=np.zeros((3,3));actual=np.array([[.5,0.,0.],[0.,.5,0.],[100.,200.,300.]])
    result=metrics(actual,baseline,[1.,1.,1.],['0']*3)
    assert result['nonlinear_training_feasible'] and result['future_change_m']==[100.,200.,300.]
    actual[0,0]=2.
    assert not metrics(actual,baseline,[1.,1.,1.],['0']*3)['nonlinear_training_feasible']


def test_nonzero_point_batch_preserves_native_arguments_and_clock(tmp_path):
    from test_ilvis0_native_box_bounds import configuration
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_training_density import native_batch
    from lll.ilvis0_density_native_probes import query
    config=configuration();theta=np.tile([1e-5,-2e-5,3e-6],(32,1))
    dv=np.tile([0.,0.,-.04905],(32,1));dt=np.full(32,.005);times=[.015,.075,.13]
    kernel,_=load_tangent(tmp_path);charges=[]
    reserve=lambda count,visits:charges.append((count,visits))
    before=native_batch(kernel,config,theta,dv,dt,times,reserve)
    after=query(kernel,config,theta,dv,dt,times,np.zeros(27),reserve)
    np.testing.assert_array_equal(after['prediction'],before['prediction'])
    np.testing.assert_array_equal(after['jacobian'],before['jacobian'])
    point=np.zeros(27);point[25]=1.
    shifted=query(kernel,config,theta,dv,dt,times,point,reserve)
    assert shifted['classification']['counter_verified']
    assert not np.array_equal(shifted['prediction'],before['prediction'])
    assert charges==[(3,96)]*3
    saved=[]
    with pytest.raises(ValueError):
        query(kernel,config,theta,dv,dt,[.2],np.zeros(27),reserve,saved.append)
    assert saved[0]['status']==1 and 'prediction' not in saved[0]


def test_report_distinguishes_rejected_calibration_from_software_failure():
    from ilvis0_density_native_probe_worker import render
    tasks=[dict(identity=f'{int(p)}-{a}-{s}',payload=dict(profile=p,axis=a,sign=s))
        for p in (False,True) for a in range(3) for s in (-1,1)]
    summary=dict(completed=0,total=12,charged=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))
    text=render(dict(tasks=tasks),summary,{})
    assert '0/12' in text and 'nonlinear training' in text
    with pytest.raises(ValueError):render(dict(tasks=tasks),dict(summary,completed=1),
        {tasks[0]['identity']:dict(passed=True)})
