# SPDX-License-Identifier: AGPL-3.0-or-later
import itertools

import numpy as np
import pytest


def test_cell_step_keeps_fixed_timing_column_and_optimizes_remaining_nuisance():
    from lll.timing_cells import bounded_step
    charges=[]
    result=bounded_step([-1.,-4.],[[1.,1.],[0.,2.]],[0.,0.],[0.,-1.],[0.,1.],
        active=['time_offset','bias'],reserve=lambda:charges.append(1))
    assert result['linear_success'] and charges==[1]
    assert result['point']==pytest.approx([0.,1.])
    assert result['predicted_cost']==pytest.approx(4.)
    assert result['active_parameters']==['time_offset','bias']
    assert result['fixed_parameters']==['time_offset']


def test_cell_step_all_fixed_still_charges_and_preserves_full_prediction():
    from lll.timing_cells import bounded_step
    charges=[];u=[.25,-.75]
    result=bounded_step([1.,2.],[[2.,1.],[1.,-1.]],u,u,u,
        active=['time_offset','bias'],reserve=lambda:charges.append(1))
    assert charges==[1] and result['linear_success']
    assert result['point']==u and result['step']==[0.,0.]
    assert result['predicted_cost']==5. and result['iterations']==0
    assert result['fixed_parameters']==['time_offset','bias']


def face_reference(a,b,lo,hi):
    """Independent low-dimensional exhaustive active-face solution."""
    values=[]
    for face in itertools.product((-1,0,1),repeat=len(lo)):
        x=np.zeros(len(lo));fixed=[i for i,v in enumerate(face) if v]
        free=[i for i,v in enumerate(face) if not v]
        for i in fixed:x[i]=lo[i] if face[i]<0 else hi[i]
        if free:x[free]=np.linalg.lstsq(a[:,free],-b-a[:,fixed]@x[fixed],rcond=None)[0]
        if np.all(x>=lo-1e-12) and np.all(x<=hi+1e-12):
            values.append(float(np.linalg.norm(a@x+b)**2))
    return min(values)


@pytest.mark.parametrize('a,b',[
    ([[1.,0.],[0.,1.],[.2,-.3]],[-.2,.1,.04]),
    ([[1.,2.],[.2,1.],[3.,-1.]],[-4.,2.,1.]),
    ([[1.,1.],[2.,2.]],[-.4,-.8])])
def test_cell_step_matches_independent_face_enumeration(a,b):
    from lll.timing_cells import bounded_step
    a=np.asarray(a);b=np.asarray(b);point=np.array([.25,.3]);lo=np.array([-1.,-1.]);hi=-lo
    charged=[];original=(a.copy(),point.copy())
    result=bounded_step(a@point+b,a,point,lo,hi,active=['time_offset','bias'],
                        reserve=lambda:charged.append(1))
    assert len(charged)==1 and result['linear_success']
    assert result['predicted_cost']==pytest.approx(face_reference(a,b,lo,hi),abs=1e-10)
    assert np.array_equal(a,original[0]) and np.array_equal(point,original[1])
    assert result['nonlinear_fit_starts']==result['native_calls']==0


def test_cell_step_recovers_kink_minimum_from_both_sides_without_crossing():
    from lll.timing_cells import bounded_step
    for side in (-1,1):
        anchor=np.array([side*.25,0.]);a=np.array([[float(side),0.],[0.,1.]])
        lo=np.array([-1. if side<0 else 0.,-1.]);hi=np.array([0. if side<0 else 1.,1.])
        result=bounded_step(a@anchor+np.array([1.,-.2]),a,anchor,lo,hi,
                            active=['time_offset','bias'],reserve=lambda:None)
        assert result['point']==pytest.approx([0.,.2],abs=1e-10)
        assert result['predicted_cost']==pytest.approx(1.)


def test_cell_step_retains_all_27_columns_in_rank_deficient_problem():
    from lll.timing_cells import bounded_step
    a=np.zeros((2,27));a[:,0]=[1.,2.];a[:,1]=a[:,0]
    point=np.zeros(27);names=['time_offset']+['p'+str(i) for i in range(26)]
    result=bounded_step(np.array([-.4,-.8]),a,point,-np.ones(27),np.ones(27),
                        active=names,reserve=lambda:None)
    assert result['linear_success'] and result['predicted_cost']<1e-20
    assert len(result['point'])==len(result['active_parameters'])==27
    assert result['active_parameters']==names


def test_cell_step_can_choose_a_smooth_interior_minimum_instead_of_the_boundary():
    from lll.timing_cells import bounded_step
    results=[]
    for side in (-1,1):
        p=[side*.25];lo=[-1. if side<0 else 0.];hi=[0. if side<0 else 1.]
        results.append(bounded_step([p[0]-.4],[[1.]],p,lo,hi,
            active=['time_offset'],reserve=lambda:None))
    assert results[0]['point']==pytest.approx([0.])
    assert results[1]['point']==pytest.approx([.4])
    assert results[1]['predicted_cost']<results[0]['predicted_cost']


def test_cell_step_recovers_known_physical_bound_minimum():
    from lll.timing_cells import bounded_step
    result=bounded_step([-1.9],[[1.]],[.1],[-1.],[1.],active=['time_offset'],reserve=lambda:None)
    assert result['point']==pytest.approx([1.]) and result['predicted_cost']==pytest.approx(1.)


def test_cell_step_charges_before_solve_and_honors_exhaustion(monkeypatch):
    from lll.timing_cells import bounded_step
    import scipy.optimize
    def exhausted():raise RuntimeError('eighteen solves already charged')
    def forbidden(*a,**kw):raise AssertionError('solve before charge')
    monkeypatch.setattr(scipy.optimize,'lsq_linear',forbidden)
    with pytest.raises(RuntimeError,match='eighteen'):
        bounded_step([1.],[[1.]],[0.],[-1.],[1.],active=['time_offset'],reserve=exhausted)


@pytest.mark.parametrize('change',['box','point','nan','columns'])
def test_cell_step_rejects_invalid_inputs_before_charging(change):
    from lll.timing_cells import bounded_step
    r=[1.];j=[[1.]];point=[0.];lo=[-1.];hi=[1.];active=['time_offset'];charged=[]
    if change=='box':lo=[1.]
    elif change=='point':point=[2.]
    elif change=='nan':j=[[float('nan')]]
    else:active=['time_offset','omitted_bias']
    with pytest.raises(ValueError):
        bounded_step(r,j,point,lo,hi,active=active,reserve=lambda:charged.append(1))
    assert not charged
