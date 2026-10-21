# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from fractions import Fraction as F
import numpy as np
import pytest


def test_compiled_transport_exists():
    assert importlib.util.find_spec('lll.ilvis0_compiled_transport') is not None


@pytest.fixture(scope='module',autouse=True)
def configure(tmp_path_factory):
    if importlib.util.find_spec('lll.ilvis0_compiled_transport') is not None:
        from lll.ilvis0_compiled_transport import configure_backend
        configure_backend(tmp_path_factory.mktemp('compiled-transport'))


def test_compiled_outputs_enclose_exact_reference_and_preserve_centers():
    from lll import ilvis0_compiled_transport as fast,ilvis0_cached_transport as old
    from lll.ilvis0_local_step_bounds import Matrix
    rng=np.random.default_rng(712)
    for _ in range(20):
        centers=rng.normal(size=(2,3));d=rng.uniform(.001,.1,(2,3));r=d/9
        def make(module):
            return [module.Value(centers[i],old._norm(d[i]),old._norm(r[i]),component_change=d[i],component_remainder=r[i]) for i in range(2)]
        a,b=make(old);aa,bb=make(fast);matrix=Matrix(np.eye(3),.001,.0001,'rotation')
        before=[old.add(a,b),old.scale(a,-.7),old.cross(a,b),old.matrix_vector(matrix,a),old.scalar_product(old.Value(.3,.02,.001),a)]
        after=[fast.add(aa,bb),fast.scale(aa,-.7),fast.cross(aa,bb),fast.matrix_vector(matrix,aa),fast.scalar_product(fast.Value(.3,.02,.001),aa)]
        for x,y in zip(before,after,strict=True):
            np.testing.assert_array_equal(x.center,y.center)
            assert y.change>=x.change and y.remainder>=x.remainder
            assert np.all(y.component_change>=x.component_change)
            assert np.all(y.component_remainder>=x.component_remainder)
            assert not y.center.flags.writeable and not y.component_change.flags.writeable


def test_nonbinary_fixed_scalar_retains_exact_rational_fallback():
    from lll import ilvis0_compiled_transport as c
    value=c.Value([.1,.2,.3],.1,.01);result=c.scale(value,F(1,3))
    for i in range(3):
        error=abs(F(result.center[i])-F(value.center[i])/3)
        assert F(result.component_remainder[i])>=F(value.component_remainder[i])/3+error


def test_norm_and_coordinate_caps_are_both_preserved():
    from lll.ilvis0_compiled_transport import Value,component
    value=Value([1,2,3],1,.1,component_change=[1,1,.01],component_remainder=[.1,.1,.001])
    assert value.change==1 and value.remainder==.1
    assert component(value,2).value.change<.011
    assert component(value,2).value.remainder==.001


def test_compiled_rotation_departures_enclose_exact_reference():
    from lll import ilvis0_compiled_relative as c,ilvis0_relative_rotation as old
    rng=np.random.default_rng(89)
    for _ in range(20):
        a,b=rng.normal(size=(2,3,3));x=old.Delta(a,.01,.001);y=old.Delta(b,.02,.002)
        xx=c.Delta(a,.01,.001);yy=c.Delta(b,.02,.002)
        for before,after in ((old.plus(x,y),c.plus(xx,yy)),(old.multiply(x,y),c.multiply(xx,yy))):
            np.testing.assert_array_equal(before.center,after.center)
            assert after.change>=before.change and after.remainder>=before.remainder
            assert after.norm>=before.norm
