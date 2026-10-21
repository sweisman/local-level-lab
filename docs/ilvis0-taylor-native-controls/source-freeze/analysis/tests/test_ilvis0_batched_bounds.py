# SPDX-License-Identifier: AGPL-3.0-or-later
"""The batched path must reproduce the separate guarded operations exactly."""
import importlib.util
import numpy as np
import pytest


def test_batched_backend_exists():
    assert importlib.util.find_spec('lll.ilvis0_batched_bounds') is not None


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_compiled_bounds import load_backend as old
    from lll.ilvis0_batched_bounds import load_backend as new
    return old(tmp_path_factory.mktemp('separate'))[0],new(tmp_path_factory.mktemp('batched'))[0]


def finish(old,result):
    d=np.minimum(result['component_change'],result['change'])
    r=np.minimum(result['component_remainder'],result['remainder'])
    return dict(component_change=d,component_remainder=r,
        change=min(result['change'],old.norm(d)),remainder=min(result['remainder'],old.norm(r)))


def test_all_vector_operations_equal_the_original_finished_result(kernels):
    old,new=kernels;rng=np.random.default_rng(7723)
    for _ in range(24):
        for op in range(6):
            n=3;an=9 if op>=4 else (1 if op==2 else n);bn=1 if op==1 else n
            a=rng.normal(size=an);b=rng.normal(size=bn)
            ad=rng.uniform(0,.1,an);bd=rng.uniform(0,.1,bn)
            ag=[old.norm(ad[:3]),.003,old.matrix_norm(a) if an==9 else 0.]
            bg=[old.norm(bd),.004,0.];center=rng.normal(size=n)
            args=(op,a,ad,ad/9,ag,b,bd,bd/8,bg,center)
            expected=finish(old,old.vector(*args));actual=new.vector(*args)
            for name in expected:np.testing.assert_array_equal(actual[name],expected[name])
    zero=np.zeros(1)
    args=(0,[.1],zero,zero,[0,0,0],[.2],zero,zero,[0,0,0],np.array(.1+.2))
    for name,value in finish(old,old.vector(*args)).items():
        np.testing.assert_array_equal(new.vector(*args)[name],value)


def test_norm_matrix_and_public_validation_are_preserved(kernels):
    old,new=kernels
    for x in ([0,0,0],[0,0,9.81],[1e-300,-2e-300,0],[1e300,-2e300,1e-300]):
        assert new.norm(x)==old.norm(x)
    for matrix in (np.eye(3),np.arange(9).reshape(3,3)):
        assert new.matrix_norm(matrix)==old.matrix_norm(matrix)
        for op in range(3):
            args=(op,matrix,[.01,.001,3.],matrix,[.02,.002,3.],matrix@matrix)
            np.testing.assert_array_equal(new.matrix(*args),old.matrix(*args))
    for x in ([],[1]*10,[float('nan')],[float('inf')]):
        with pytest.raises(ValueError):new.norm(x)
    with pytest.raises(ValueError):new.matrix_norm([1,2,3])
    with pytest.raises(ValueError):new.vector(2,[1,2,3],[0]*3,[0]*3,[0]*3,[1]*3,[0]*3,[0]*3,[0]*3,[1]*3)


def test_finalization_retains_both_norm_and_axis_caps(kernels):
    old,new=kernels
    expected=finish(old,dict(component_change=np.array([1,1,.01]),
        component_remainder=np.array([.1,.1,.001]),change=1.,remainder=.1))
    actual=new.finalize([1,1,.01],[.1,.1,.001],1.,.1)
    for name in expected:np.testing.assert_array_equal(actual[name],expected[name])
    with pytest.raises(ValueError):new.finalize([1,-1,0],[0,0,0],1.,1.)


def test_transport_values_and_operations_are_bitwise_equal(tmp_path):
    from fractions import Fraction
    from lll import ilvis0_compiled_transport as old,ilvis0_batched_transport as new
    from lll.ilvis0_local_step_bounds import Matrix
    new.configure_backend(tmp_path);rng=np.random.default_rng(59)
    def compare(a,b):
        for name in ('center','change','remainder','component_change','component_remainder'):
            np.testing.assert_array_equal(getattr(a,name),getattr(b,name))
        assert not b.center.flags.writeable and not b.component_change.flags.writeable
    for _ in range(20):
        c=rng.normal(size=(2,3));d=rng.uniform(.01,.1,(2,3))
        aa=[old.Value(c[i],.1,.02,component_change=d[i],component_remainder=d[i]/10) for i in range(2)]
        bb=[new.Value(c[i],.1,.02,component_change=d[i],component_remainder=d[i]/10) for i in range(2)]
        for a,b in zip(aa,bb):compare(a,b)
        matrix=Matrix(np.eye(3),.01,.001,'rotation')
        for module,values in ((old,aa),(new,bb)):
            a,b=values
            results=[module.add(a,b),module.cross(a,b),module.scale(a,-.7),
                module.scale(a,Fraction(1,3)),module.matrix_vector(matrix,a),
                module.scalar_product(module.Value(.3,.01,.001),a)]
            if module is old:reference=results
            else:
                for x,y in zip(reference,results):compare(x,y)
