# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math

import numpy as np
import pytest
from lll import ilvis0_affine_support as support


def test_joint_constraint_preserves_information_lost_by_coordinate_box():
    # x=y leaves both coordinates in [-1,1], but x-y is exactly zero.
    result=support.upper([-1.,-1.],[1.,1.],[[1.,-1.],[-1.,1.]],[0.,0.],[1.,-1.],[1.,0.])
    assert result['upper']==0. and result['exact_upper']==F(0)
    assert result['parameter_count']==2 and result['scientific_decision']=='abstain'
    loose=support.upper([-1.,-1.],[1.,1.],[[1.,-1.],[-1.,1.]],[0.,0.],[1.,-1.],[.5,0.])
    assert loose['upper']==1.


def test_known_triangle_optimum_and_bad_dual_proposals_are_safe():
    for multiplier,expected in [(0.,3.),(1.,2.),(2.,2.),(20.,20.)]:
        result=support.upper([0.,0.],[1.,1.],[[1.,1.]],[1.],[1.,2.],[multiplier])
        assert result['upper']==expected
        for i in range(9):
            for j in range(9-i):assert F(i,8)+2*F(j,8)<=F(result['upper'])


def test_outward_linear_endpoint_at_binary_rounding_boundary():
    result=support.upper([0.],[1.],[[3.]],[1.],[1.],[1/3.])
    assert result['exact_upper']>=F(1,3)
    assert F(result['upper'])>=result['exact_upper']
    assert F(math.nextafter(result['upper'],-math.inf))<result['exact_upper']


def test_all_twenty_seven_columns_remain_and_unidentified_contribution_survives():
    a=np.zeros((2,27));a[0,:2]=[1.,-1.];a[1,:2]=[-1.,1.]
    c=np.zeros(27);c[:3]=[1.,-1.,2.]
    result=support.upper(-np.ones(27),np.ones(27),a,[0.,0.],c,[1.,0.])
    assert result['upper']==2. and result['parameter_count']==27


def test_optional_lp_proposal_must_still_have_an_exact_certificate():
    result=support.propose([-1.,-1.],[1.,1.],[[1.,-1.],[-1.,1.]],[0.,0.],[1.,-1.])
    assert result['upper']==0. and result['exact_upper']==0
    assert not result['observational_coverage_qualified']


def test_bad_solver_status_cannot_empty_or_narrow_region(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(support,'linprog',lambda *a,**k:SimpleNamespace(success=False,status=2))
    result=support.propose([0.,0.],[1.,1.],[[1.,1.]],[1.],[1.,2.])
    assert result['upper']==3. and result['proposal_used'] is False
    monkeypatch.setattr(support,'linprog',lambda *a,**k:SimpleNamespace(success=True,ineqlin=SimpleNamespace(marginals=[float('nan')])))
    assert support.propose([0.,0.],[1.,1.],[[1.,1.]],[1.],[1.,2.])['upper']==3.


def test_invalid_negative_multipliers_and_overflow_are_unsupported():
    with pytest.raises(ValueError):support.upper([0.],[1.],[[1.]],[1.],[1.],[-1.])
    with pytest.raises(ValueError):support.upper([0.],[1.],[[float('nan')]],[1.],[1.],[0.])
    with pytest.raises(ValueError,match='endpoint'):support.upper([0.],[1e308],[[1.]],[1.],[1e308],[0.])


def test_coordinate_projection_retains_latent_columns_and_certifies_both_sides():
    lo=-np.ones(51);hi=np.ones(51);lo[27]=-.2;hi[27]=.2
    a=np.zeros((2,51));a[0,[0,27]]=1.;a[1]= -a[0]
    reservations=[]
    report=support.project_coordinates(lo,hi,a,[.1,.1],axes=[0,1],
        reserve=lambda p,s:reservations.append((p,s)))
    assert report['parameter_count']==51 and report['axes']==[0,1]
    assert len(reservations)==4 and all(v==(1,3) for v in reservations)
    first,free=report['coordinates']
    assert first['lower']==pytest.approx(-.3) and first['upper']==pytest.approx(.3)
    assert free['lower']==-1 and free['upper']==1
    assert len(first['certificates'])==2
    for cert in first['certificates']:
        objective=np.zeros(51);objective[0]=cert['sign']
        from lll.ilvis0_saved_prediction_audit import support as independent
        assert independent(lo,hi,a,[.1,.1],objective,cert['multipliers'])==F(cert['exact_upper'])
    assert report['observational_coverage_qualified'] is False


def test_coordinate_projection_keeps_box_when_proposal_fails(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(support,'linprog',lambda *a,**k:SimpleNamespace(success=False,status=2))
    result=support.project_coordinates([-1.],[1.],[[1.]],[.1],axes=[0],reserve=lambda *args:None)
    row=result['coordinates'][0]
    assert row['lower']==-1 and row['upper']==1
    assert all(not c['proposal_used'] for c in row['certificates'])


@pytest.mark.parametrize('axes',[[],[0,0],[1],[-1],[True]])
def test_coordinate_projection_rejects_invalid_axes_before_reserving(axes):
    reservations=[]
    with pytest.raises(ValueError,match='axes'):
        support.project_coordinates([-1.],[1.],[[1.]],[.1],axes=axes,
            reserve=lambda *args:reservations.append(args))
    assert not reservations
