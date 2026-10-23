# SPDX-License-Identifier: AGPL-3.0-or-later
"""Typed copy/retarget of untruncated source states, not whole native bounds."""
from copy import copy
import ctypes
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import math
from pathlib import Path
import re
import subprocess


@dataclass(frozen=True)
class Kernel:
    initialize:object
    append:object
    fork:object
    state_bytes:int
    identity:str
    query_lower:object


def load_kernels(directory,*,source_directory=None):
    import numpy as np
    base=Path(source_directory) if source_directory else Path(__file__).parent
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    flags=['-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off']
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    def dependencies(path,found):
        if path.name in found:return
        raw=path.read_bytes();found[path.name]=hashlib.sha256(raw).hexdigest()
        for include in re.findall(rb'#include\s+"([^"]+)"',raw):dependencies(path.with_name(include.decode()),found)
    kernels={};metadata={};array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    for family,kinds in (('reference',('reference',)),('intervals',('interval','point'))):
        source=base/f'ilvis0_source_prefix_{family}.cpp';hashes={};dependencies(source,hashes)
        identity=hashlib.sha256(repr((hashes,flags,compiler)).encode()).hexdigest()
        binary=directory/f'source-prefix-{family}-{identity}.so'
        if not binary.exists():
            temporary=binary.with_suffix('.partial.so')
            subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
            temporary.replace(binary)
        library=ctypes.CDLL(str(binary))
        for kind in kinds:
            prefix='ilvis0_prefix_'+kind+'_';size=getattr(library,prefix+'bytes')
            size.argtypes=[];size.restype=ctypes.c_size_t;n=int(size())
            if not 0<n<65536:raise ValueError('unsupported bounded source-prefix layout')
            initialize=getattr(library,prefix+'init');initialize.restype=ctypes.c_int
            initialize.argtypes=[ctypes.c_void_p,ctypes.c_size_t]+[array]*(6 if kind=='interval' else 4)+[ctypes.c_double]*2
            append=getattr(library,prefix+'append');append.restype=ctypes.c_int
            append.argtypes=[ctypes.c_void_p,ctypes.c_size_t,array,ctypes.c_double]+[array]*(2 if kind=='point' else 3)
            fork=getattr(library,prefix+'fork');fork.restype=ctypes.c_int
            fork.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_double,ctypes.c_double]
            floor=getattr(library,prefix+'query_lower');floor.restype=ctypes.c_int
            floor.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_double,ctypes.c_double,ctypes.POINTER(ctypes.c_double)]
            kernels[kind]=Kernel(initialize,append,fork,n,identity+':'+kind,floor)
        metadata[family]=dict(sources=hashes,compiler=compiler,flags=flags,identity=identity,
            binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    return kernels,metadata


@dataclass(frozen=True)
class Binding:
    identity:str
    reference:str
    kind:str
    kernel_identity:str
    state_bytes:int
    clock_lower:F
    clock_upper:F
    support_end:F


def make_stream(kernels,kind,case,point,time_s,*,lower,upper,reference_binding,maximum_packets):
    import numpy as np
    from lll.ilvis0_source_reference import _inputs
    from lll.ilvis0_source_stream import SourceStream
    from lll.ilvis0_source_derivative_intervals import Stream as Intervals
    from lll.ilvis0_source_point_derivatives import Stream as Point
    if kind not in ('reference','interval','point') or not isinstance(kernels.get(kind),Kernel):
        raise ValueError('typed source-prefix kernel required')
    if not isinstance(reference_binding,str) or not reference_binding:raise ValueError('explicit source reference binding required')
    dt,theta,dv,initial,limits,z=_inputs(case,point,time_s)
    lo=np.asarray(lower,float);hi=np.asarray(upper,float)
    if (lo.shape!=(27,) or hi.shape!=(27,) or not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi))
            or np.any(lo>hi)):
        raise ValueError('finite complete physical domain and retained source expansion required')
    clock_lower=F(float(limits[25]))*F(float(min(lo[25],z[25])))
    clock_upper=F(float(limits[25]))*F(float(max(hi[25],z[25])))
    support=F(float(sum(dt)))
    if F(float(time_s))+clock_lower<0 or F(float(time_s))+clock_upper>support:
        raise ValueError('entire source clock domain must lie within support')
    kernel=kernels[kind];digest=hashlib.sha256((reference_binding+kernel.identity).encode())
    for a in (dt,theta,dv,initial,limits,z,lo,hi):
        a=np.ascontiguousarray(a,float);digest.update(str(a.shape).encode());digest.update(a.tobytes())
    arguments=dict(maximum_packets=maximum_packets)
    if kind=='reference':stream=SourceStream(kernel,case,z,time_s,**arguments)
    elif kind=='point':stream=Point(kernel,case,z,time_s,**arguments)
    else:stream=Intervals(kernel,case,z,lo,hi,time_s,**arguments)
    stream._prefix_binding=Binding(digest.hexdigest(),reference_binding,kind,kernel.identity,kernel.state_bytes,
        clock_lower,clock_upper,support)
    stream.prefix_reused_packets=0;return stream


def _checked_target(stream,time_s,reference_binding):
    binding=getattr(stream,'_prefix_binding',None)
    if (not isinstance(binding,Binding) or binding.reference!=reference_binding
            or not isinstance(stream.kernel,Kernel) or binding.kernel_identity!=stream.kernel.identity
            or binding.state_bytes!=stream.kernel.state_bytes or stream.state_bytes!=binding.state_bytes
            or stream._buffer is None or not math.isfinite(time_s)):
        raise ValueError('open typed source state and identical reference binding required')
    lower=F(float(time_s))+binding.clock_lower;upper=F(float(time_s))+binding.clock_upper
    if lower<0 or upper>binding.support_end:raise ValueError('entire forked clock domain must lie within source support')
    return lower


def fork_floor(stream,time_s,*,reference_binding):
    """Conservative query floor from typed C++ arithmetic and exact clock input.

    A scheduler must also cover the outward cumulative duration bound before
    advancing its canonical prefix. Reading a buffer at a guessed offset is
    neither necessary nor supported.
    """
    from lll.ilvis0_saved_prediction_audit import endpoint
    lower=_checked_target(stream,time_s,reference_binding);result=ctypes.c_double()
    code=stream.kernel.query_lower(stream._buffer,stream.state_bytes,float(time_s),endpoint(lower,False),ctypes.byref(result))
    if code or not math.isfinite(result.value):raise ValueError('unsupported typed source query floor')
    return result.value


def fork_stream(stream,time_s,*,reference_binding):
    """Copy all typed state; preserve charged packet position and input identity."""
    from lll.ilvis0_saved_prediction_audit import endpoint
    lower=_checked_target(stream,time_s,reference_binding)
    child=copy(stream);child._buffer=ctypes.create_string_buffer(stream.state_bytes)
    code=stream.kernel.fork(child._buffer,child.state_bytes,stream._buffer,stream.state_bytes,
        float(time_s),endpoint(lower,False))
    if code:raise ValueError('source prefix is clipped, at a knot, incompatible or outside its complete prefix: '+str(code))
    child.prefix_reused_packets=stream.visits
    return child
