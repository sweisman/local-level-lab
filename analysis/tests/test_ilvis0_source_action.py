# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import numpy as np


def test_direction_preserving_source_action_exists():
    assert importlib.util.find_spec('lll.ilvis0_source_action') is not None


def test_polynomial_sources_retain_all_columns_and_cover_nonlinear_errors():
    from lll.ilvis0_source_action import source_action
    from lll.ilvis0_directional_values import Value
    from lll.ilvis0_directional_matrices import Matrix
    rng=np.random.default_rng(287);width=np.linspace(.001,.003,27)
    a0=np.array([.03,-.1,-9.81]);b0=np.array([.01,-.002,.00003])
    l0=rng.normal(0,.0001,(3,3));ja=rng.normal(0,.02,(3,27));jb=rng.normal(0,.0001,(3,27))
    jl=rng.normal(0,.00001,(3,3,27));qa=np.array([.01,-.03,.02]);qb=qa*.01;ql=rng.normal(0,.00001,(3,3))
    # Nonlinear terms multiply t², t=mean(p/width); |t|<=1 throughout this box.
    da=abs(ja)@width+abs(qa);db=abs(jb)@width+abs(qb);dl=np.einsum('ijk,k->ij',abs(jl),width)+abs(ql)
    a=Value(a0,da,abs(qa));b=Value(b0,db,abs(qb));left=Matrix(l0,dl,abs(ql),'general')
    result=source_action(left,a,b,jl,ja,jb,lower=-width,upper=width,reference=np.zeros(27))
    assert result.jacobian.shape==(3,27)
    assert np.all(np.any(result.jacobian!=0,axis=0))
    for point in [width,-width,np.zeros(27),*rng.uniform(-width,width,(24,27))]:
        t=np.mean(point/width);aa=a0+ja@point+qa*t*t;bb=b0+jb@point+qb*t*t
        ll=l0+np.einsum('ijk,k->ij',jl,point)+ql*t*t
        value=ll@(aa+bb)+bb
        assert np.all(abs(value-result.value.center)<=result.value.change+1e-13)
        assert np.all(abs(value-result.value.center-result.jacobian@point)<=result.value.remainder+1e-13)


def test_yaw_only_left_action_does_not_spread_horizontal_uncertainty_down():
    from lll.ilvis0_source_action import source_action
    from lll.ilvis0_directional_values import Value
    from lll.ilvis0_directional_matrices import Matrix
    from scipy.spatial.transform import Rotation
    left=Matrix.constant(Rotation.from_rotvec([0,0,.01]).as_matrix()-np.eye(3))
    a=Value([0,0,-9.81],[1.,1.,.02],[.5,.5,.01])
    b=Value([.002,-.001,.00001],[.02,.02,.0004],[.01,.01,.0001])
    zero=np.zeros((3,27));result=source_action(left,a,b,np.zeros((3,3,27)),zero,zero,
        lower=-np.ones(27),upper=np.ones(27),reference=np.zeros(27))
    assert result.value.remainder[2]<=.00010000000001
    assert result.value.change[2]<=.00040000000001
    np.testing.assert_array_equal(result.jacobian,zero)


def test_coefficient_rounding_is_included_in_affine_remainder():
    from fractions import Fraction as F
    from lll.ilvis0_source_action import source_action
    from lll.ilvis0_directional_values import Value
    from lll.ilvis0_directional_matrices import Matrix
    left=Matrix.constant(np.eye(3)*.1);ja=np.full((3,27),.1);jb=ja.copy();jl=np.zeros((3,3,27))
    a=Value([.1,.2,.3],[1.,1.,1.],[0.,0.,0.]);b=Value([.2,.3,.4],[1.,1.,1.],[0.,0.,0.])
    result=source_action(left,a,b,jl,ja,jb,lower=-np.ones(27),upper=np.ones(27),reference=np.zeros(27))
    exact=F(.1)*(F(.1)+F(.1))+F(.1)
    expected=sum((abs(exact-F(v)) for v in result.jacobian[0]),F(0))
    assert expected>0 and F(result.coefficient_rounding[0])>=expected
    assert result.value.remainder[0]>=result.coefficient_rounding[0]
    assert not result.jacobian.flags.writeable


def test_missing_or_invalid_columns_and_domains_rejected():
    import pytest
    from lll.ilvis0_source_action import source_action
    from lll.ilvis0_directional_values import Value
    from lll.ilvis0_directional_matrices import Matrix
    base=dict(left=Matrix.constant(np.zeros((3,3))),a=Value(np.zeros(3),np.zeros(3),np.zeros(3)),
        b=Value(np.zeros(3),np.zeros(3),np.zeros(3)),left_jacobian=np.zeros((3,3,27)),
        a_jacobian=np.zeros((3,27)),b_jacobian=np.zeros((3,27)),
        lower=-np.ones(27),upper=np.ones(27),reference=np.zeros(27))
    for altered in (dict(a_jacobian=np.zeros((3,26))),dict(upper=np.full(27,-2.)),
                    dict(reference=np.full(27,float('nan')))):
        with pytest.raises(ValueError):source_action(**dict(base,**altered))
