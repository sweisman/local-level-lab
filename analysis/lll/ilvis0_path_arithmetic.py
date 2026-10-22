# SPDX-License-Identifier: AGPL-3.0-or-later
"""Guarded compiled path arithmetic checked against the exact reference."""
import ctypes
import hashlib
from pathlib import Path
import subprocess
import numpy as np
from .ilvis0_path_jets import Jet3
from .ilvis0_compiled_bounds import _check,UnsupportedArithmetic


class Backend:
    def __init__(self,library):
        self.library=library;array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        library.ilvis0_bounds_runtime_ok.argtypes=[];library.ilvis0_bounds_runtime_ok.restype=ctypes.c_int
        library.ilvis0_path_arithmetic.argtypes=[ctypes.c_int,array,array,array]
        library.ilvis0_path_arithmetic.restype=ctypes.c_int

    def calculate(self,operation,a,b=None):
        if type(operation) is not int or not 0<=operation<=6:raise ValueError('supported path operation required')
        if (not isinstance(a,Jet3) or (b is not None and not isinstance(b,Jet3))
                or (operation<2 and b is None)):
            raise ValueError('complete actual-derivative input jets required')
        left=np.ascontiguousarray(a.report()['derivatives'],float)
        right=np.ascontiguousarray((b if b is not None else Jet3.constant(0)).report()['derivatives'],float)
        out=np.empty((4,2))
        _check(self.library.ilvis0_path_arithmetic(operation,left,right,out))
        if not np.all(np.isfinite(out)):raise UnsupportedArithmetic('finite path derivative endpoints required')
        return Jet3(out.tolist())


def load_backend(directory,*,source_directory=None):
    source=Path(source_directory)/'ilvis0_path_arithmetic.cpp' if source_directory else Path(__file__).with_suffix('.cpp')
    files=(source,source.with_name('ilvis0_compiled_bounds.cpp'))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    digest=hashlib.sha256(''.join(hashes.values()).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    flags=['-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off']
    binary=directory/('path-arithmetic-'+digest+'.so')
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    backend=Backend(ctypes.CDLL(str(binary)))
    if not backend.library.ilvis0_bounds_runtime_ok():raise UnsupportedArithmetic('unsupported runtime floating-point mode')
    return backend,dict(sources=hashes,source_sha256=digest,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        flags=flags,compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],
        runtime_ieee_guard=True,floating_point_native_execution_covered=False)
