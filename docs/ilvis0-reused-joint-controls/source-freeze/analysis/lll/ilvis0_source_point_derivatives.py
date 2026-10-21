# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-memory enclosures of ideal source values and derivatives at a point.

Knot derivatives enclose both one-sided conventions. This component alone
does not bound native arithmetic error or qualify geographic predictions.
"""
import ctypes
from dataclasses import dataclass
import hashlib
from pathlib import Path
import subprocess
import numpy as np
from .ilvis0_compiled_bounds import _check
from .ilvis0_source_reference import _inputs

VERSION='ilvis0-source-point-derivatives-v1'


@dataclass(frozen=True)
class Kernel:
    initialize:object
    append:object
    state_bytes:int


def load_kernel(directory,*,source_directory=None):
    source=(Path(source_directory)/'ilvis0_source_point_derivatives.cpp') if source_directory else Path(__file__).with_suffix('.cpp')
    paths=(source,source.with_name('ilvis0_source_derivative_intervals.cpp'),source.with_name('ilvis0_compiled_bounds.cpp'))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    flags=['-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off']
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    digest=hashlib.sha256(repr((hashes,flags,compiler)).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    binary=directory/('source-point-'+digest+'.so')
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    library=ctypes.CDLL(str(binary));array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    size=library.ilvis0_source_point_bytes;size.argtypes=[];size.restype=ctypes.c_size_t;n=size()
    if not 0<n<65536:raise ValueError('unsupported point derivative state layout')
    initialize=library.ilvis0_source_point_init
    initialize.argtypes=[ctypes.c_void_p,ctypes.c_size_t]+[array]*4+[ctypes.c_double]*2
    initialize.restype=ctypes.c_int
    append=library.ilvis0_source_point_append
    append.argtypes=[ctypes.c_void_p,ctypes.c_size_t,array,ctypes.c_double,array,array];append.restype=ctypes.c_int
    return Kernel(initialize,append,n),dict(version=VERSION,sources=hashes,state_bytes=n,flags=flags,
        compiler=compiler,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),libm_accuracy_assumed=False)


class Stream:
    def __init__(self,kernel,case,point,time_s,*,maximum_packets):
        dt,theta,dv,initial,limits,z=_inputs(case,point,time_s)
        if type(maximum_packets) is not int or not 0<maximum_packets<=len(dt):
            raise ValueError('bounded packet allowance required')
        self.dt=np.array(dt,copy=True);self.theta=np.array(theta,copy=True)
        for array in (self.dt,self.theta):array.setflags(write=False)
        self.center=tuple(z);self.kernel=kernel;self.state_bytes=kernel.state_bytes
        self.maximum_packets=maximum_packets;self.visits=0
        self._buffer=ctypes.create_string_buffer(self.state_bytes)
        _check(kernel.initialize(self._buffer,self.state_bytes,initial,limits,z,dv[0],float(dt[0]),float(time_s)))

    def append(self):
        if self._buffer is None or self.visits>=self.maximum_packets:
            raise ValueError('point derivative stream closed or packet allowance exhausted')
        values=np.empty((2,2,3,2));jac=np.empty((2,2,3,27,2));index=self.visits
        code=self.kernel.append(self._buffer,self.state_bytes,self.theta[index],float(self.dt[index]),values,jac)
        self.visits+=1
        if code:self.close();_check(code)
        for array in (values,jac):array.setflags(write=False)
        return dict(version=VERSION,packet_index=index,point_values=values,point_jacobian=jac,
            center=self.center,parameter_count=27,state_bytes=self.state_bytes,
            source_derivatives_qualified=False,native_propagation_qualified=False,
            observational_coverage_qualified=False,scientific_decision='abstain')

    def close(self):self._buffer=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
