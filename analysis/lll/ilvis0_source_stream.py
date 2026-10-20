# SPDX-License-Identifier: AGPL-3.0-or-later
"""Constant-memory source rows at the actual native midpoint/end prefixes."""
import ctypes
from dataclasses import dataclass
import hashlib
from pathlib import Path
import subprocess
import numpy as np
from .ilvis0_source_reference import _inputs


@dataclass(frozen=True)
class Kernel:
    initialize:object
    append:object
    state_bytes:int


def load_stream(directory,*,source_directory=None):
    source=(Path(source_directory)/'ilvis0_source_stream.cpp') if source_directory is not None else Path(__file__).with_suffix('.cpp')
    parent=source.with_name('ilvis0_tangent.cpp')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,parent)}
    digest=hashlib.sha256(''.join(hashes.values()).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    binary=directory/('source-stream-'+digest+'.so');flags=['-O2','-std=c++17','-fPIC','-shared']
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    library=ctypes.CDLL(str(binary));size=library.ilvis0_source_stream_bytes
    size.argtypes=[];size.restype=ctypes.c_size_t;state_bytes=size()
    if not 0<state_bytes<16384:raise ValueError('unsupported bounded source-state layout')
    array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    initialize=library.ilvis0_source_stream_init
    initialize.argtypes=[ctypes.c_void_p,ctypes.c_size_t,array,array,array,array,ctypes.c_double,ctypes.c_double]
    initialize.restype=ctypes.c_int;append=library.ilvis0_source_stream_append
    append.argtypes=[ctypes.c_void_p,ctypes.c_size_t,array,ctypes.c_double,array,array,array]
    append.restype=ctypes.c_int
    return Kernel(initialize,append,int(state_bytes)),dict(sources=hashes,
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),state_bytes=int(state_bytes),
        compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],flags=flags)


class SourceStream:
    """Each append is a source step, to be precharged by its study/consumer."""
    def __init__(self,kernel,case,point,time_s,*,maximum_packets):
        dt,theta,dv,initial,limits,z=_inputs(case,point,time_s)
        if type(maximum_packets)!=int or not 0<maximum_packets<=len(dt):
            raise ValueError('finite source packet allowance within the input required')
        self.kernel=kernel;self.dt=np.array(dt,copy=True);self.theta=np.array(theta,copy=True)
        self.dt.setflags(write=False);self.theta.setflags(write=False)
        self.visits=0;self.maximum_packets=maximum_packets
        self.state_bytes=kernel.state_bytes;self._buffer=ctypes.create_string_buffer(self.state_bytes)
        code=kernel.initialize(self._buffer,self.state_bytes,initial,limits,z,dv[0],float(dt[0]),float(time_s))
        if code:raise ValueError('unsupported source initialization: '+str(code))

    def append(self):
        if self._buffer is None:raise ValueError('source stream is closed')
        if self.visits>=self.maximum_packets:raise ValueError('source packet allowance exhausted')
        index=self.visits;values=np.empty((2,2,3));jac=np.empty((2,2,3,27));timing=np.empty(5)
        code=self.kernel.append(self._buffer,self.state_bytes,self.theta[index],float(self.dt[index]),values,jac,timing)
        self.visits+=1
        if code:
            self.close()
            raise ValueError('unsupported source prefix: '+str(code))
        values.setflags(write=False);jac.setflags(write=False)
        return dict(values=values,jacobian=jac,packet_index=index,packet_start_s=float(timing[0]),
            packet_end_s=float(timing[1]),fraction=float(timing[2]),time_slope=float(timing[3]),
            query_time_s=float(timing[4]),parameter_count=27,
            clock_branch='preceding packet at an exact endpoint',state_bytes=self.state_bytes,
            native_propagation_qualified=False,observational_coverage_qualified=False)

    def close(self):self._buffer=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
