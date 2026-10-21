# SPDX-License-Identifier: AGPL-3.0-or-later
"""The new Python entry points must retain the C++ floating-mode guard."""
import ctypes
import platform
import subprocess
import numpy as np
import pytest


def test_batched_calls_reject_changed_rounding_and_subnormal_modes(tmp_path):
    from lll.ilvis0_batched_bounds import load_backend
    from lll.ilvis0_compiled_bounds import UnsupportedArithmetic
    backend=load_backend(tmp_path)[0]
    source=tmp_path/'modes.cpp';binary=tmp_path/'modes.so'
    code='#include <cfenv>\nextern "C" int get_round(){return std::fegetround();}\n'
    code+='extern "C" int set_round(int v){return std::fesetround(v);}\nextern "C" int upward(){return FE_UPWARD;}\n'
    sse=platform.machine().lower() in ('x86_64','amd64','i386','i686')
    if sse:
        code+='#include <xmmintrin.h>\nextern "C" unsigned get_sse(){return _mm_getcsr();}\n'
        code+='extern "C" void set_sse(unsigned v){_mm_setcsr(v);}\n'
    source.write_text(code)
    subprocess.run(['c++','-shared','-fPIC',str(source),'-o',str(binary)],check=True,capture_output=True)
    probe=ctypes.CDLL(str(binary));probe.set_round.argtypes=[ctypes.c_int]
    def reject():
        for call in (lambda:backend.norm([1.,2.,3.]),lambda:backend.finalize([.1]*3,[.01]*3,1.,1.),
            lambda:backend.matrix_norm(np.eye(3)),lambda:backend.positive(0,.1,.2),
            lambda:backend.vector(0,[1.]*3,[.1]*3,[.01]*3,[1.,1.,0.],
                [1.]*3,[.1]*3,[.01]*3,[1.,1.,0.],[2.]*3)):
            with pytest.raises(UnsupportedArithmetic):call()
    rounding=probe.get_round()
    try:
        assert probe.set_round(probe.upward())==0
        reject()
    finally:assert probe.set_round(rounding)==0
    if sse:
        probe.get_sse.restype=ctypes.c_uint;probe.set_sse.argtypes=[ctypes.c_uint]
        saved=probe.get_sse()
        for flag in (1<<15,1<<6):
            try:probe.set_sse(saved|flag);reject()
            finally:probe.set_sse(saved)
    assert backend.norm([0.,0.,9.81])==9.81
