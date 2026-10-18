# SPDX-License-Identifier: AGPL-3.0-or-later
import ctypes
from pathlib import Path
import subprocess
import numpy as np
import pytest


def candidate():
    from lll import ilvis0_clock_brackets
    return ilvis0_clock_brackets


@pytest.mark.parametrize('point',[-.31,0.,.61])
def test_representable_boundary_has_verified_sides(point):
    times=np.array([1.0005,2.0015,3.0025,4.0035,5.0045])
    r=candidate().bracket(times,1200,.15,point)
    assert r['side_geometry_supported'] and r['queries']<=1024
    assert r['knots'][0]==-1. and r['knots'][-1]==1.
    assert r['knots'][1]<r['point']<r['knots'][-2]
    assert r['boundary_changed_epochs']>=1


def test_native_scalar_clock_agrees_on_both_sides(tmp_path):
    source=Path(__file__).with_name('ilvis0_clock_reference.cpp');binary=tmp_path/'clock.so'
    subprocess.run(['c++','-O2','-std=c++17','-fPIC','-shared',str(source),'-o',str(binary)],check=True,capture_output=True)
    fn=ctypes.CDLL(str(binary)).clock_indices
    fn.argtypes=[ctypes.c_size_t,ctypes.c_size_t,np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS'),ctypes.c_double,ctypes.c_double,np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS')]
    fn.restype=ctypes.c_int
    times=np.array([1.0005,2.0015,3.0025,4.0035,5.0045]);r=candidate().bracket(times,1200,.15,0.)
    ends=np.cumsum(np.full(1200,.005))
    for p in (r['point'],*r['side_points']):
        out=np.empty(len(times),dtype=np.int64)
        assert fn(1200,len(times),times,p,.15,out)==0
        assert np.array_equal(out,candidate().indices(ends,times,.15,p))


def test_finite_clock_query_budget_cannot_expand():
    with pytest.raises(RuntimeError,match='budget'):candidate().bracket(np.array([1.,2.]),600,.15,0.,maximum_queries=1)


@pytest.mark.parametrize('times',[np.array([1.,1.]),np.array([np.nan,2.]),np.array([.01,2.])])
def test_invalid_or_unsupported_saved_epochs_are_rejected(times):
    with pytest.raises(ValueError):candidate().bracket(times,600,.15,0.)
