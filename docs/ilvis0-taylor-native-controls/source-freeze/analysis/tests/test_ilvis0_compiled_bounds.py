# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import importlib.util
import math
import subprocess
import numpy as np
import pytest


def test_compiled_bound_backend_exists():
    assert importlib.util.find_spec('lll.ilvis0_compiled_bounds') is not None


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    from lll.ilvis0_compiled_bounds import load_backend
    return load_backend(tmp_path_factory.mktemp('compiled-bounds'))[0]


def test_norm_encloses_exact_squares_across_scales(kernel):
    vectors=[[0,0,0],[0,0,9.81],[1,1,1],[1e-300,-2e-300,0],
        [1e300,-2e300,1e-300],[float.fromhex('0x0.0000000000001p-1022'),0,0]]
    for vector in vectors:
        result=kernel.norm(vector)
        assert F(result)**2>=sum((F(v)**2 for v in vector),F(0))
    assert kernel.norm([0,0,9.81])==9.81


def test_matrix_norm_encloses_exact_gram_bound(kernel):
    matrices=[np.eye(3),np.zeros((3,3)),np.array([[1,1,0],[1,-1,0],[0,0,1e-150]]),
        np.array([[1e300,-2e300,0],[1e300,2e300,0],[0,0,1e-300]])]
    matrices+=list(np.random.default_rng(72).normal(size=(20,3,3)))
    for matrix in matrices:
        gram=[[sum((F(matrix[k,i])*F(matrix[k,j]) for k in range(3)),F(0)) for j in range(3)] for i in range(3)]
        squared=min(sum((gram[i][i] for i in range(3)),F(0)),max(sum(abs(v) for v in row) for row in gram))
        assert F(kernel.matrix_norm(matrix))**2>=squared
    assert kernel.matrix_norm(np.eye(3))==1


def test_vector_radius_operations_cover_exact_reference(kernel):
    from lll import ilvis0_directional_values as d,ilvis0_directional_matrices as m
    rng=np.random.default_rng(515)
    for _ in range(30):
        a=rng.normal(size=3);b=rng.normal(size=3);da=rng.uniform(.001,.1,3);db=rng.uniform(.001,.1,3)
        ra=da/8;rb=db/7;aa=d.Value(a,da,ra);bb=d.Value(b,db,rb);s=-.7
        cases=[(0,a,da,ra,b,db,rb,d.add(aa,bb)),
            (1,a,da,ra,[s],[0.],[0.],d.scale(aa,s)),
            (2,[s],[.01],[.001],b,db,rb,d.scalar_product(d.Value(s,.01,.001),bb)),
            (3,a,da,ra,b,db,rb,d.cross(aa,bb))]
        matrix=rng.normal(size=(3,3));md=.01;mr=.001
        cases.append((5,matrix,np.full((3,3),md),np.full((3,3),mr),b,db,rb,
            m.apply(m.Matrix(matrix,np.full((3,3),md),np.full((3,3),mr)),bb)))
        for op,x,dx,rx,y,dy,ry,expected in cases:
            gx=[kernel.norm(np.asarray(dx).ravel()),kernel.norm(np.asarray(rx).ravel()),kernel.matrix_norm(x) if op==5 else 0.]
            gy=[kernel.norm(np.asarray(dy).ravel()),kernel.norm(np.asarray(ry).ravel()),0.]
            out=kernel.vector(op,x,dx,rx,gx,y,dy,ry,gy,expected.center)
            assert np.all(out['component_change']>=expected.change)
            assert np.all(out['component_remainder']>=expected.remainder)


def test_reference_center_rounding_is_preserved(kernel):
    a=np.array([.1,.2,.3]);b=np.array([.2,-.1,.7]);center=a+b;zero=np.zeros(3)
    out=kernel.vector(0,a,zero,zero,[0,0,0],b,zero,zero,[0,0,0],center)
    error=[abs(F(c)-F(x)-F(y)) for c,x,y in zip(center,a,b,strict=True)]
    assert any(error)
    assert all(F(r)>=e for r,e in zip(out['component_remainder'],error,strict=True))
    assert F(out['remainder'])**2>=sum((e*e for e in error),F(0))


def test_matrix_composition_bounds_include_center_error(kernel):
    rng=np.random.default_rng(91)
    for op in (0,1):
        for _ in range(12):
            a,b=rng.normal(size=(2,3,3));center=a+b if op==0 else a@b
            ga=[.01,.001,kernel.matrix_norm(a)];gb=[.02,.002,kernel.matrix_norm(b)]
            out=kernel.matrix(op,a,ga,b,gb,center)
            if op==0:
                base_d=F(ga[0])+F(gb[0]);base_r=F(ga[1])+F(gb[1])
                exact=[[F(a[i,j])+F(b[i,j]) for j in range(3)] for i in range(3)]
            else:
                base_d=F(ga[2])*F(gb[0])+F(gb[2])*F(ga[0])+F(ga[0])*F(gb[0])
                base_r=F(ga[2])*F(gb[1])+F(gb[2])*F(ga[1])+F(ga[0])*F(gb[0])
                exact=[[sum((F(a[i,k])*F(b[k,j]) for k in range(3)),F(0)) for j in range(3)] for i in range(3)]
            error=sum(((F(center[i,j])-exact[i][j])**2 for i in range(3) for j in range(3)),F(0))
            assert F(out[0])>=base_d and (F(out[0])-base_d)**2>=error
            assert F(out[1])>=base_r and (F(out[1])-base_r)**2>=error


def test_nonfinite_and_unrepresentable_bounds_rejected(kernel):
    from lll.ilvis0_compiled_bounds import UnsupportedArithmetic
    for value in ([math.inf,0,0],[math.nan,0,0],[np.finfo(float).max]*3):
        with pytest.raises((ValueError,UnsupportedArithmetic)):kernel.norm(value)


def test_structural_product_and_positive_operations_remain_outward(kernel):
    assert F(kernel.positive(0,.1,.2))>=F(.1)+F(.2)
    assert F(kernel.positive(1,.1,.2))>=F(.1)*F(.2)
    center=np.eye(3);out=kernel.matrix(2,center,[.01,.001,1],center,[.02,.002,1],center)
    assert F(out[0])>=F(.01)+F(.02)
    assert F(out[1])>=F(.001)+F(.002)+F(.01)*F(.02)


def test_runtime_guard_rejects_changed_rounding_mode(kernel,tmp_path):
    import ctypes
    from lll.ilvis0_compiled_bounds import UnsupportedArithmetic
    source=tmp_path/'rounding.cpp';binary=tmp_path/'rounding.so'
    source.write_text('#include <cfenv>\nextern "C" int upward(){return FE_UPWARD;}\n'
        'extern "C" int get(){return std::fegetround();}\nextern "C" int set(int x){return std::fesetround(x);}\n')
    subprocess.run(['c++','-shared','-fPIC',str(source),'-o',str(binary)],check=True,capture_output=True)
    probe=ctypes.CDLL(str(binary));probe.set.argtypes=[ctypes.c_int];saved=probe.get()
    try:
        assert probe.set(probe.upward())==0
        with pytest.raises(UnsupportedArithmetic):kernel.norm([1.,2.,3.])
    finally:assert probe.set(saved)==0
    assert kernel.norm([1.,2.,3.])>=math.sqrt(14)


def test_positive_radii_enclose_subnormal_products_and_cancellation_centers(kernel):
    tiny=float.fromhex('0x0.0000000000001p-1022')
    for a,b in ((tiny,.5),(1e-300,1e-100),(1e-200,1e-120),(tiny,tiny),(1e300,1e-300)):
        assert F(kernel.positive(1,a,b))>=F(a)*F(b)
        assert F(kernel.positive(0,a,b))>=F(a)+F(b)
    zero=np.zeros(3)
    a=np.array([1e-300,-1e-300,tiny]);b=np.array([1e-100,1e-100,.5])
    center=np.cross(a,b)
    result=kernel.vector(3,a,zero,zero,[0,0,0],b,zero,zero,[0,0,0],center)
    for i in range(3):
        j,k=(i+1)%3,(i+2)%3
        error=abs(F(center[i])-F(a[j])*F(b[k])+F(a[k])*F(b[j]))
        assert F(result['component_remainder'][i])>=error


def test_runtime_guard_rejects_flush_to_zero_and_denormals_are_zero(kernel,tmp_path):
    import ctypes
    import platform
    from lll.ilvis0_compiled_bounds import UnsupportedArithmetic
    if platform.machine().lower() not in ('x86_64','amd64','i386','i686'):
        pytest.skip('SSE control-register check is specific to x86')
    source=tmp_path/'subnormal.cpp';binary=tmp_path/'subnormal.so'
    source.write_text('#include <xmmintrin.h>\nextern "C" unsigned get(){return _mm_getcsr();}\n'
        'extern "C" void set(unsigned x){_mm_setcsr(x);}\n')
    subprocess.run(['c++','-shared','-fPIC',str(source),'-o',str(binary)],check=True,capture_output=True)
    probe=ctypes.CDLL(str(binary));probe.get.restype=ctypes.c_uint;probe.set.argtypes=[ctypes.c_uint]
    saved=probe.get()
    for flag in (1<<15,1<<6):
        try:
            probe.set(saved|flag)
            with pytest.raises(UnsupportedArithmetic):kernel.norm([1.,2.,3.])
        finally:probe.set(saved)
