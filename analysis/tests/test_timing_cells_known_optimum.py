# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent convex optima; no saved calibration matrices or IMU histories."""
import math

import numpy as np
import pytest

from lll.timing_cells import bounded_step


@pytest.mark.parametrize('columns',[4,26])
@pytest.mark.parametrize('strong_exponent',[8,16])
@pytest.mark.parametrize('weak_exponent',[-28,-36,-44])
@pytest.mark.parametrize('narrow',[False,True])
def test_cell_step_preserves_independently_certified_box_minimum(columns,strong_exponent,weak_exponent,narrow):
    h=np.ones((1,1))
    while len(h)<columns:h=np.block([[h,h],[h,-h]])
    scales=np.full(len(h),2.**weak_exponent)
    scales[:columns-2]=2.**strong_exponent;scales[columns-2]=2.**-12
    j=scales[:,None]*h[:,:columns]
    r=np.zeros(len(h));r[columns-2]=.25;r[columns-1]=1.
    # Binary inputs make these gradient sums exact: no optimizer supplies the reference.
    gradient=np.array([math.fsum(float(a)*float(b) for a,b in zip(j[:,k],r)) for k in range(columns)])
    point=-np.sign(gradient);lo=-np.ones(columns);hi=np.ones(columns)
    if narrow:
        if point[-1]<0:hi[-1]=math.nextafter(-1.,0.)
        else:lo[-1]=math.nextafter(1.,0.)
    assert np.all((point==-1)&(gradient>=0)|(point==1)&(gradient<=0)|(point==0)&(gradient==0))
    charges=[]
    p=bounded_step(r,j,point,lo,hi,active=[f'x{i}' for i in range(columns-1)]+['time_offset'],
                   reserve=lambda:charges.append(1))
    assert charges==[1]
    delta=np.array(p['point'])-point
    residual=[float(b)+math.fsum(float(a)*float(d) for a,d in zip(row,delta)) for row,b in zip(j,r)]
    cost=math.fsum(v*v for v in residual);anchor=math.fsum(float(v)*float(v) for v in r)
    assert cost<=anchor+64*np.finfo(float).eps*max(1.,cost,anchor),p


def test_cell_step_moves_from_nonoptimal_anchor_with_all_26_columns():
    j=np.diag(2.**np.linspace(-5,5,26));point=np.zeros(26)
    target=np.linspace(-.75,.75,26);r=j@(point-target)
    p=bounded_step(r,j,point,-np.ones(26),np.ones(26),
        active=[f'x{i}' for i in range(25)]+['time_offset'],reserve=lambda:None)
    assert p['linear_success'] and len(p['point'])==26
    assert np.max(abs(np.array(p['point'])-target))<1e-9
    assert p['predicted_cost']<1e-16


def test_cell_step_rejects_worsening_even_when_solver_claims_success(monkeypatch):
    from types import SimpleNamespace
    import importlib
    core=importlib.import_module('scipy.optimize._lsq.bvls')
    monkeypatch.setattr(core,'bvls',lambda *a:SimpleNamespace(x=np.array([.25,0.]),status=1,nit=1))
    p=bounded_step([1.,0.],[[0.,0.],[1.,0.]],[0.,0.],[-1.,-1.],[1.,1.],
                   active=['x','time_offset'],reserve=lambda:None)
    assert p['solver_claimed_success'] and not p['nonworsening']
    assert p['linear_success'] is False
