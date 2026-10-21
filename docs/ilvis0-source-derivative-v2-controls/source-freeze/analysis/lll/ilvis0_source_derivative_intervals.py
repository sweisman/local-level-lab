# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-memory source values and derivatives on an explicit physical domain.

This component has no training constraints or native geographic integration.
Its interval/derivative interpretation requires independent qualification;
it is not an observed-data adapter or a confidence calculation.
"""
import ctypes
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
from pathlib import Path
import subprocess
import numpy as np
from .ilvis0_compiled_bounds import _check
from .ilvis0_source_reference import _inputs
from .ilvis0_saved_prediction_audit import endpoint

VERSION='ilvis0-source-derivative-intervals-v1'


@dataclass(frozen=True)
class Kernel:
    initialize:object
    append:object
    rotation:object
    state_bytes:int


def load_kernel(directory,*,source_directory=None):
    source=(Path(source_directory)/'ilvis0_source_derivative_intervals.cpp') if source_directory else Path(__file__).with_suffix('.cpp')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,source.with_name('ilvis0_compiled_bounds.cpp'))}
    digest=hashlib.sha256(''.join(hashes.values()).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    binary=directory/('source-intervals-'+digest+'.so')
    flags=['-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off']
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    library=ctypes.CDLL(str(binary));array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    size=library.ilvis0_source_intervals_bytes;size.argtypes=[];size.restype=ctypes.c_size_t;n=size()
    if not 0<n<65536:raise ValueError('unsupported source interval state layout')
    initialize=library.ilvis0_source_intervals_init
    initialize.argtypes=[ctypes.c_void_p,ctypes.c_size_t]+[array]*6+[ctypes.c_double]*2;initialize.restype=ctypes.c_int
    append=library.ilvis0_source_intervals_append
    append.argtypes=[ctypes.c_void_p,ctypes.c_size_t,array,ctypes.c_double,array,array,array];append.restype=ctypes.c_int
    rotation=library.ilvis0_source_intervals_rotation;rotation.argtypes=[array]*3;rotation.restype=ctypes.c_int
    return Kernel(initialize,append,rotation,n),dict(version=VERSION,sources=hashes,state_bytes=n,flags=flags,
        compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),libm_accuracy_assumed=False)


def rotation_intervals(kernel,angle):
    angle=np.ascontiguousarray(angle,dtype=float)
    if angle.shape!=(3,) or not np.all(np.isfinite(angle)):raise ValueError('finite three-axis rotation required')
    values=np.empty((3,3,2));jac=np.empty((3,3,3,2));_check(kernel.rotation(angle,values,jac))
    values.setflags(write=False);jac.setflags(write=False)
    return dict(values=values,jacobian=jac)


def mean_value_radius(frame,values,rows,*,phase):
    """Transfer a supplied derivative enclosure to explicit numerical rows.

    The caller must establish that `frame` covers the same source and domain.
    Shape checks do not constitute physical derivative qualification.
    """
    if type(phase) is not int or phase not in (0,1):raise ValueError('source phase required')
    arrays=[np.asarray(v,float) for v in (frame['point_values'],frame['jacobian'],values,rows)]
    point,derivatives,values,rows=arrays
    if (tuple(a.shape for a in arrays)!=((2,2,3,2),(2,2,3,27,2),(2,2,3),(2,2,3,27))
            or not all(np.all(np.isfinite(a)) for a in arrays)
            or np.any(point[...,0]>point[...,1]) or np.any(derivatives[...,0]>derivatives[...,1])):
        raise ValueError('finite ordered intervals and all 27 supplied rows required')
    z,lo,hi=(np.asarray(frame[key],float) for key in ('center','lower','upper'))
    if (any(a.shape!=(27,) or not np.all(np.isfinite(a)) for a in (z,lo,hi)) or np.any(lo>hi)):
        raise ValueError('complete finite source domain required')
    widths=[max(abs(F(float(a))-F(float(c))),abs(F(float(b))-F(float(c))))
        for a,b,c in zip(lo,hi,z,strict=True)]
    result=np.empty((2,3))
    for source in range(2):
        for axis in range(3):
            c=F(float(values[phase,source,axis]));p=point[phase,source,axis]
            total=max(abs(F(float(p[0]))-c),abs(F(float(p[1]))-c))
            for interval,row,width in zip(derivatives[phase,source,axis],rows[phase,source,axis],widths,strict=True):
                r=F(float(row))
                total+=max(abs(F(float(interval[0]))-r),abs(F(float(interval[1]))-r))*width
            result[source,axis]=endpoint(total,True)
    result.setflags(write=False);return result


class Stream:
    def __init__(self,kernel,case,point,lower,upper,time_s,*,maximum_packets):
        dt,theta,dv,initial,limits,z=_inputs(case,point,time_s)
        lo=np.ascontiguousarray(lower,dtype=float);hi=np.ascontiguousarray(upper,dtype=float)
        if (lo.shape!=(27,) or hi.shape!=(27,) or not np.all(np.isfinite(lo))
                or not np.all(np.isfinite(hi)) or np.any(lo>hi)
                or type(maximum_packets) is not int or not 0<maximum_packets<=len(dt)):
            raise ValueError('finite ordered domain and bounded packet allowance required')
        self.dt=np.array(dt,copy=True);self.theta=np.array(theta,copy=True)
        for array in (self.dt,self.theta):array.setflags(write=False)
        self.lower=tuple(lo);self.upper=tuple(hi);self.center=tuple(z)
        self.kernel=kernel;self.state_bytes=kernel.state_bytes;self.maximum_packets=maximum_packets;self.visits=0
        self._buffer=ctypes.create_string_buffer(self.state_bytes)
        _check(kernel.initialize(self._buffer,self.state_bytes,initial,limits,z,lo,hi,dv[0],float(dt[0]),float(time_s)))

    def append(self):
        if self._buffer is None or self.visits>=self.maximum_packets:raise ValueError('source stream closed or packet allowance exhausted')
        point=np.empty((2,2,3,2));values=np.empty((2,2,3,2));jac=np.empty((2,2,3,27,2));index=self.visits
        code=self.kernel.append(self._buffer,self.state_bytes,self.theta[index],float(self.dt[index]),point,values,jac)
        self.visits+=1
        if code:self.close();_check(code)
        for array in (point,values,jac):array.setflags(write=False)
        return dict(version=VERSION,packet_index=index,point_values=point,values=values,jacobian=jac,
            lower=self.lower,upper=self.upper,center=self.center,parameter_count=27,state_bytes=self.state_bytes,
            source_derivatives_qualified=False,native_propagation_qualified=False,observational_coverage_qualified=False)

    def close(self):self._buffer=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
