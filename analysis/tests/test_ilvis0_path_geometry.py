# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math
import pytest


def test_scalar_trigonometric_chain_rule_at_zero_has_known_derivatives():
    from lll.ilvis0_path_jets import Jet3
    from lll.ilvis0_path_geometry import sincos
    s=Jet3.affine(0,[1,1],[0,0]);si,co=sincos(s+s.square())
    assert si.exact==tuple((F(v),)*2 for v in [0,1,2,-1])
    assert co.exact==tuple((F(v),)*2 for v in [1,0,-1,-6])


def test_square_root_derivatives_recover_an_independent_positive_square():
    from lll.ilvis0_path_jets import Jet3
    from lll.ilvis0_path_geometry import positive_sqrt
    s=Jet3.affine(0,[1,1],[0,0]);root=positive_sqrt((2+s).square())
    assert root.exact==tuple((F(v),)*2 for v in [2,1,0,0])
    irrational=positive_sqrt(Jet3.constant(2)).exact[0]
    assert irrational[0]**2<=2<=irrational[1]**2
    assert irrational[1]-irrational[0]<=F(1,2**128)
    with pytest.raises(ValueError):positive_sqrt(Jet3.constant([0,1]))


def test_geographic_metric_latitude_curvature_matches_series_at_equator():
    from lll.ilvis0_path_jets import Jet3
    from lll.ilvis0_path_geometry import metric,E2,A
    phi=Jet3.affine(0,[1,1],[0,0]);zero=Jet3.constant(0)
    for model in (0,1):
        north,east=metric(model,phi,zero,Jet3.constant(6000000))
        assert north.exact==tuple((v,v) for v in [A*(1-E2),0,3*A*(1-E2)*E2,0])
        assert east.exact==tuple((v,v) for v in [A,0,A*(E2-1),0])


def test_disc_rates_and_context_preserve_independent_yaw_and_height_signs():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_geometry import metric,rates,context
    c=[J.constant(F(1,2)),J.constant(0),J.constant(1000)]
    v=[J.constant(200),J.constant(-100),J.constant(3)];radius=J.constant(6000000)
    n,e=metric(2,c[0],c[2],radius);q=rates(2,c,v,radius)
    assert q[0].exact[0]==(F(1,30000),)*2
    assert q[1].exact[0]==(-100/e.exact[0][0],)*2
    assert q[2].exact[0]==(F(-3),)*2
    earth,transport=context(2,c[0],q)
    assert all(x.exact[0]==(0,0) for x in earth)
    assert transport[2].exact[0]==(-q[1].exact[0][0],)*2


def test_interval_trigonometry_contains_independent_endpoint_series():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_geometry import sincos
    # Scalar alternating series is independent of the production polynomial.
    si,co=sincos(J.affine(0,[1,1],[F(1,4),F(1,2)]))
    for x in (F(1,4),F(1,3),F(1,2)):
        for jet,cosine in ((si,False),(co,True)):
            degree=lambda j:2*j if cosine else 2*j+1
            value=sum(((-1)**j*x**degree(j)/math.factorial(degree(j)) for j in range(18)),F(0))
            following=x**degree(18)/math.factorial(degree(18))
            assert jet.exact[0][0]<=value<=value+following<=jet.exact[0][1]


def test_geographic_unsupported_domains_fail_before_producing_a_bound():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_geometry import metric,sincos
    with pytest.raises(ValueError):metric(3,J.constant(0),J.constant(0),J.constant(1))
    with pytest.raises(ValueError):metric(0,J.constant(1.58),J.constant(0),J.constant(1))
    with pytest.raises(ValueError):metric(2,J.constant(0),J.constant(0),J.constant(-1))
    with pytest.raises(ValueError):sincos(J.constant(9))
