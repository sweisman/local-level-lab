# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


@pytest.fixture(scope='module')
def arithmetic(tmp_path_factory):
    from lll.ilvis0_path_arithmetic import load_backend
    return load_backend(tmp_path_factory.mktemp('path-arithmetic'))[0]


def contains(actual,expected):
    for (lo,hi),(left,right) in zip(actual.exact,expected.exact):
        assert lo<=left<=right<=hi


def test_compiled_products_and_reciprocals_enclose_exact_rational_reference(arithmetic):
    from lll.ilvis0_path_jets import Jet3 as J
    a=J([[F(-1,3),F(1,7)],[F(1,3),F(2,3)],[-1,2],[3,4]])
    b=J([[F(4,3),F(7,3)],[-2,3],[4,5],[-6,7]])
    for operation,expected in ((0,a+b),(1,a*b),(3,a.square())):
        contains(arithmetic.calculate(operation,a,b),expected)
    contains(arithmetic.calculate(2,b),b.inverse())


def test_compiled_square_root_encloses_known_derivatives_and_positive_reference(arithmetic):
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_geometry import positive_sqrt
    s=J.affine(0,[1,1],[0,0]);value=(2+s).square()
    contains(arithmetic.calculate(4,value),positive_sqrt(value))
    irrational=J([[2,3],[1,2],[-3,4],[5,6]])
    contains(arithmetic.calculate(4,irrational),positive_sqrt(irrational))


def test_compiled_trigonometric_chain_rules_enclose_exact_interval_reference(arithmetic):
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_geometry import sincos
    for domain in ([[F(-2,3),F(1,2)],[F(1,3),F(1,2)],[F(-1,7),0],[1,2]],
            [[0,0],[1,1],[2,2],[3,3]],[[F(7,4),2],[0,0],[0,0],[0,0]]):
        value=J(domain);si,co=sincos(value)
        contains(arithmetic.calculate(5,value),si);contains(arithmetic.calculate(6,value),co)


def test_zero_denominators_unsupported_arguments_and_nonfinite_inputs_fail(arithmetic):
    from lll.ilvis0_path_jets import Jet3 as J
    with pytest.raises(ValueError):arithmetic.calculate(2,J.constant([-1,1]))
    with pytest.raises(ValueError):arithmetic.calculate(4,J.constant([-1,1]))
    with pytest.raises(ValueError):arithmetic.calculate(5,J.constant(9))
    with pytest.raises(ValueError):arithmetic.calculate(99,J.constant(1))
    with pytest.raises(ValueError):arithmetic.calculate(0,[[0,0]]*3)
    with pytest.raises(ValueError):arithmetic.calculate(2,J.constant(1),[[0,0]]*4)


def test_subnormal_products_do_not_silently_flush_to_zero(arithmetic):
    from lll.ilvis0_path_jets import Jet3 as J
    tiny=J.constant(F(1,2**1074))
    answer=arithmetic.calculate(1,tiny,J.constant(F(1,2)))
    assert answer.exact[0][0]<=F(1,2**1075)<=answer.exact[0][1]
    assert answer.exact[0][1]>0


def test_square_root_value_bounds_are_verified_by_exact_squaring_at_extreme_scales(arithmetic):
    from lll.ilvis0_path_jets import Jet3 as J
    for x in (F(1,2**1074),F(float(1e-300)),F(2),F(float(1e300))):
        lo,hi=arithmetic.calculate(4,J.constant(x)).exact[0]
        assert lo>0 and lo*lo<=x<=hi*hi


def test_backend_records_source_compiler_and_runtime_mode(tmp_path):
    from lll.ilvis0_path_arithmetic import load_backend
    _,metadata=load_backend(tmp_path)
    assert metadata['runtime_ieee_guard'] and len(metadata['sources'])==2
    assert metadata['floating_point_native_execution_covered'] is False
