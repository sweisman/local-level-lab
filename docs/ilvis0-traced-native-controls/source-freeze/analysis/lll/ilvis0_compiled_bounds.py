# SPDX-License-Identifier: AGPL-3.0-or-later
"""Guarded outward-arithmetic primitives; independent of frozen native engines."""
import ctypes
import hashlib
from pathlib import Path
import subprocess
import numpy as np


class UnsupportedArithmetic(ValueError):pass


def _array(value,size=None):
    a=np.ascontiguousarray(np.asarray(value,float).ravel())
    if (size is not None and a.size!=size) or not np.all(np.isfinite(a)):
        raise ValueError('finite arrays of the declared shape required')
    return a


def _check(code):
    if code:raise UnsupportedArithmetic({1:'unsupported IEEE rounding or subnormal mode',
        2:'unsupported arithmetic input',3:'no finite outward bound'}.get(code,'compiled arithmetic failure'))


class Backend:
    def __init__(self,library):
        self.library=library;array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        library.ilvis0_bounds_runtime_ok.argtypes=[];library.ilvis0_bounds_runtime_ok.restype=ctypes.c_int
        library.ilvis0_bounds_norm.argtypes=[ctypes.c_size_t,array,array]
        library.ilvis0_bounds_positive.argtypes=[ctypes.c_int,ctypes.c_double,ctypes.c_double,array]
        library.ilvis0_bounds_positive.restype=ctypes.c_int
        library.ilvis0_bounds_matrix_norm.argtypes=[array,array]
        library.ilvis0_bounds_vector.argtypes=[ctypes.c_int,ctypes.c_size_t]+[array]*10
        library.ilvis0_bounds_matrix.argtypes=[ctypes.c_int]+[array]*6
        for name in ('norm','matrix_norm','vector','matrix'):getattr(library,'ilvis0_bounds_'+name).restype=ctypes.c_int

    def norm(self,values):
        a=_array(values)
        if not 1<=len(a)<=9:raise ValueError('one to nine entries required')
        result=np.empty(1);_check(self.library.ilvis0_bounds_norm(len(a),a,result));return float(result[0])

    def positive(self,op,a,b):
        result=np.empty(1);_check(self.library.ilvis0_bounds_positive(op,float(a),float(b),result));return float(result[0])

    def matrix_norm(self,values):
        a=_array(values,9);result=np.empty(1)
        _check(self.library.ilvis0_bounds_matrix_norm(a,result));return float(result[0])

    def vector(self,op,a,ad,ar,ag,b,bd,br,bg,center):
        c=_array(center);n=len(c)
        if op not in range(6) or n not in (1,3) or (op>=2 and n!=3):raise ValueError('supported vector operation required')
        an=9 if op>=4 else (1 if op==2 else n);bn=1 if op==1 else n
        arrays=[_array(v,size) for v,size in zip((a,ad,ar,ag,b,bd,br,bg),(an,an,an,3,bn,bn,bn,3),strict=True)]
        out=np.empty(2*n+2);_check(self.library.ilvis0_bounds_vector(op,n,*arrays,c,out))
        return dict(component_change=out[:n].reshape(np.shape(center)),component_remainder=out[n:2*n].reshape(np.shape(center)),
            change=float(out[2*n]),remainder=float(out[2*n+1]))

    def matrix(self,op,a,ag,b,bg,center):
        arrays=[_array(v,size) for v,size in zip((a,ag,b,bg,center),(9,3,9,3,9),strict=True)]
        out=np.empty(2);_check(self.library.ilvis0_bounds_matrix(op,*arrays,out));return out


def load_backend(directory,*,source_directory=None):
    source=(Path(source_directory)/'ilvis0_compiled_bounds.cpp') if source_directory else Path(__file__).with_suffix('.cpp')
    digest=hashlib.sha256(source.read_bytes()).hexdigest();directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    flags=['-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off']
    binary=directory/('outward-bounds-'+digest+'.so')
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    backend=Backend(ctypes.CDLL(str(binary)))
    if not backend.library.ilvis0_bounds_runtime_ok():raise UnsupportedArithmetic('unsupported runtime floating-point mode')
    return backend,dict(source_sha256=digest,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),flags=flags,
        compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],runtime_ieee_guard=True)
