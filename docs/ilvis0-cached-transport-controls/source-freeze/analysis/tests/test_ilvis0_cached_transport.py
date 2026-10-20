# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import numpy as np


def test_cached_transport_exists():
    assert importlib.util.find_spec('lll.ilvis0_cached_transport') is not None


def test_directional_view_reuses_immutable_validated_arrays():
    from lll import ilvis0_cached_transport as c
    value=c.Value([1,2,3],1,.1,component_change=[.1,.2,.3])
    first=c._axis(value)
    assert c._axis(value) is first
    assert first.center is value.center
    assert not first.center.flags.writeable and not first.change.flags.writeable
    result=c.add(value,value)
    assert c._axis(result) is c._axis(result)
    from lll.ilvis0_component_transport import Value as ExactValue
    original=ExactValue([1,2,3],1,.1,component_change=[.1,.2,.3])
    np.testing.assert_array_equal(c._value(original).component_change,original.component_change)


def test_cached_operators_preserve_exact_reference_outputs():
    from lll import ilvis0_cached_transport as fast,ilvis0_component_transport as exact
    from lll.ilvis0_local_step_bounds import Matrix
    rng=np.random.default_rng(421)
    for _ in range(20):
        center=rng.normal(size=(2,3));change=rng.uniform(.001,.1,(2,3));rem=change/8
        def inputs(module):
            return [module.Value(center[i],np.linalg.norm(change[i]),np.linalg.norm(rem[i]),
                component_change=change[i],component_remainder=rem[i]) for i in range(2)]
        a,b=inputs(exact);aa,bb=inputs(fast)
        matrix=Matrix(np.eye(3),.001,.00001,'rotation')
        old=[exact.add(a,b),exact.scale(a,-.7),exact.cross(a,b),exact.matrix_vector(matrix,a),
             exact.scalar_product(exact.Value(.3,.02,.001),a)]
        new=[fast.add(aa,bb),fast.scale(aa,-.7),fast.cross(aa,bb),fast.matrix_vector(matrix,aa),
             fast.scalar_product(fast.Value(.3,.02,.001),aa)]
        for x,y in zip(old,new,strict=True):
            np.testing.assert_array_equal(x.center,y.center)
            np.testing.assert_array_equal(x.component_change,y.component_change)
            np.testing.assert_array_equal(x.component_remainder,y.component_remainder)
            assert x.change==y.change and x.remainder==y.remainder
