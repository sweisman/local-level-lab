# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest
from lll import ilvis0_rotation_products as products


def fixture(cap=.25):
    matrix=[[float(i==j) for j in range(3)] for i in range(3)]
    transform=dict(binding='matrix',reference_binding='reference',center=matrix,
        jacobian=[[[0.]*27 for _ in range(3)] for _ in range(3)],caps=[cap]*9)
    limits=[0.]*27;limits[18:21]=[.05]*3
    return dict(transform=transform,initial_r=matrix,limits=limits,physical_center=[0.]*27,
        lower=[-1.]*51,upper=[1.]*51,reference_binding='reference',source_id='source')


def point_for_matrix(spec,matrix,gain_points=(F(0),)*3):
    point=[F(0)]*51
    point[18:21]=gain_points
    for i in range(3):
        for j in range(3):
            point[42+3*i+j]=(F(matrix[i][j])-F(spec['transform']['center'][i][j]))/F(spec['transform']['caps'][3*i+j])
    return point


def test_product_planes_retain_exact_signed_corners_and_interior():
    for left in ((F(-2),F(3)),(F(1),F(1)),(F(-3),F(-1))):
        right=(F(-1),F(4))
        rows=products.product_planes((F(0),(F(1),F(0),F(0))),left,
            (F(0),(F(0),F(1),F(0))),right,2)
        for x in (left[0],sum(left)/2,left[1]):
            for y in (right[0],sum(right)/2,right[1]):
                assert all(sum(a*v for a,v in zip(row,(x,y,x*y)))<=b for row,b in rows)


def test_exact_rotation_and_anisotropic_gains_satisfy_every_exported_plane():
    spec=fixture();cuts=products.build(**spec)
    t=F(1,20);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    rotation=[[c,-s,0],[s,c,0],[0,0,1]];gp=(F(-1,2),F(1,3),F(3,4))
    matrix=[[F(rotation[i][j])/(1+F(spec['limits'][18+j])*gp[j]) for j in range(3)] for i in range(3)]
    lifted=products.lift(cuts,point_for_matrix(spec,matrix,gp))
    assert len(lifted)==78 and cuts['original_parameter_count']==51
    assert cuts['new_physical_parameters']==0 and max(products.slacks(cuts,lifted))<=0
    assert all(F(a)<=x<=F(b) for a,x,b in zip(cuts['lower'],lifted,cuts['upper']))


def test_nonorthogonal_columns_with_unit_norm_are_rejected_jointly():
    spec=fixture();cuts=products.build(**spec)
    t=F(1,10);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    impossible=[[1,s,0],[0,c,0],[0,0,1]]
    assert all(sum(F(impossible[i][j])**2 for i in range(3))==1 for j in range(3))
    assert max(products.slacks(cuts,products.lift(cuts,point_for_matrix(spec,impossible))))>0


def test_gram_condition_correctly_does_not_rule_out_reflection():
    spec=fixture(cap=2.);spec['limits']=[0.]*27;cuts=products.build(**spec)
    reflected=[[-1,0,0],[0,1,0],[0,0,1]]
    assert max(products.slacks(cuts,products.lift(cuts,point_for_matrix(spec,reflected))))<=0
    assert cuts['physical_realizability_established'] is False


def test_initial_mounting_defect_is_bounded_without_repair():
    spec=fixture();spec['initial_r'][0][0]=1.+2**-30
    # fixture's initial_r and saved center share this deliberately imperfect value
    cuts=products.build(**spec)
    point=point_for_matrix(spec,spec['initial_r'])
    assert F(cuts['reference_gram_defect_bound'])>0
    assert max(products.slacks(cuts,products.lift(cuts,point)))<=0


def test_fixed_domain_and_zero_caps_remain_supported():
    spec=fixture(cap=0.);spec['lower']=spec['upper']=[0.]*51
    cuts=products.build(**spec)
    assert max(products.slacks(cuts,products.lift(cuts,[0.]*51)))<=0
    assert len(cuts['lower'])==78


@pytest.mark.parametrize('change',['binding','missing','gain','nan'])
def test_invalid_source_or_domain_is_rejected(change):
    spec=fixture()
    if change=='binding':spec['reference_binding']='other'
    elif change=='missing':spec['lower'].pop()
    elif change=='gain':spec['limits'][18]=1.
    else:spec['transform']['caps'][0]=float('nan')
    with pytest.raises(ValueError):products.build(**spec)
