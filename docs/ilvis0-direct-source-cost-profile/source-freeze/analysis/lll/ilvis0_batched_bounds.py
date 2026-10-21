# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate batched interface; C++ retains finite-input and IEEE-mode checks.

Python owns contiguous binary64 buffers and validates their lengths before
passing addresses. No unchecked public pointer entry point is exposed.
"""
import ctypes
import hashlib
from pathlib import Path
import subprocess
import numpy as np
from .ilvis0_compiled_bounds import _check,UnsupportedArithmetic


def _array(value,size=None):
    result=np.ascontiguousarray(np.asarray(value,dtype=np.float64).ravel())
    if size is not None and result.size!=size:raise ValueError('declared array size required')
    return result


def _address(array):return array.ctypes.data


def _result(out,shape):
    n=(out.size-2)//2
    return dict(component_change=out[:n].reshape(shape),component_remainder=out[n:2*n].reshape(shape),
        change=float(out[2*n]),remainder=float(out[2*n+1]))


class Backend:
    def __init__(self,library):
        self.library=library;p=ctypes.c_void_p;z=ctypes.c_size_t
        signatures={
            'ilvis0_bounds_runtime_ok':[],
            'ilvis0_bounds_norm':[z,p,p],
            'ilvis0_bounds_positive':[ctypes.c_int,ctypes.c_double,ctypes.c_double,p],
            'ilvis0_bounds_matrix_norm':[p,p],
            'ilvis0_bounds_matrix':[ctypes.c_int]+[p]*6,
            'ilvis0_batched_vector':[ctypes.c_int,z]+[p]*10,
            'ilvis0_batched_finalize':[z,p,p,ctypes.c_double,ctypes.c_double,p]}
        for name,args in signatures.items():
            function=getattr(library,name);function.argtypes=args;function.restype=ctypes.c_int

    def norm(self,values):
        a=_array(values)
        if not 1<=len(a)<=9:raise ValueError('one to nine entries required')
        out=np.empty(1);_check(self.library.ilvis0_bounds_norm(len(a),_address(a),_address(out)))
        return float(out[0])

    def positive(self,op,a,b):
        out=np.empty(1)
        _check(self.library.ilvis0_bounds_positive(op,float(a),float(b),_address(out)))
        return float(out[0])

    def matrix_norm(self,values):
        a=_array(values,9);out=np.empty(1)
        _check(self.library.ilvis0_bounds_matrix_norm(_address(a),_address(out)))
        return float(out[0])

    def vector(self,op,a,ad,ar,ag,b,bd,br,bg,center):
        c=_array(center);n=len(c)
        if op not in range(6) or n not in (1,3) or (op>=2 and n!=3):raise ValueError('supported vector operation required')
        an=9 if op>=4 else (1 if op==2 else n);bn=1 if op==1 else n
        arrays=[_array(v,size) for v,size in zip((a,ad,ar,ag,b,bd,br,bg),(an,an,an,3,bn,bn,bn,3),strict=True)]
        out=np.empty(2*n+2)
        _check(self.library.ilvis0_batched_vector(op,n,*map(_address,arrays),_address(c),_address(out)))
        return _result(out,np.shape(center))

    def matrix(self,op,a,ag,b,bg,center):
        arrays=[_array(v,size) for v,size in zip((a,ag,b,bg,center),(9,3,9,3,9),strict=True)]
        out=np.empty(2);_check(self.library.ilvis0_bounds_matrix(op,*map(_address,arrays),_address(out)))
        return out

    def finalize(self,change,remainder,global_change,global_remainder):
        d=_array(change);r=_array(remainder,len(d));n=len(d)
        if n not in (1,3):raise ValueError('scalar or three-vector required')
        out=np.empty(2*n+2)
        _check(self.library.ilvis0_batched_finalize(n,_address(d),_address(r),float(global_change),float(global_remainder),_address(out)))
        return _result(out,np.shape(change))


def load_backend(directory,*,source_directory=None):
    source=(Path(source_directory)/'ilvis0_batched_bounds.cpp') if source_directory else Path(__file__).with_suffix('.cpp')
    files=(source,source.with_name('ilvis0_compiled_bounds.cpp'))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    digest=hashlib.sha256(''.join(hashes.values()).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    flags=['-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off']
    binary=directory/('batched-bounds-'+digest+'.so')
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    backend=Backend(ctypes.CDLL(str(binary)))
    if not backend.library.ilvis0_bounds_runtime_ok():raise UnsupportedArithmetic('unsupported runtime floating-point mode')
    return backend,dict(source_sha256=digest,sources=hashes,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        flags=flags,compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],runtime_ieee_guard=True,
        batched_component_norm_intersection=True)
