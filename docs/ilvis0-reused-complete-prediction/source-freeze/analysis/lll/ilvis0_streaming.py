# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded-block native integration with source-bound, same-runtime checkpoints.

Input identity/order are caller declarations, not inferred physical continuity.
No receiver positions, fused navigation or observational decisions enter this API.
"""
import base64
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

import numpy as np

VERSION='ilvis0-streaming-native-v1'
SOURCES=('ilvis0_stream_value.c','ilvis0_stream_tangent.cpp','ilvis0_stream_body.h',
         'ilvis0_native.c','ilvis0_tangent.cpp','ilvis0_streaming.py')


def _encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def _digest(value):return hashlib.sha256(_encoded(value)).hexdigest()


def _array(value,shape):
    result=np.array(value,dtype=np.float64,order='C',copy=True)
    if result.shape!=shape or not np.all(np.isfinite(result)):
        raise ValueError('complete finite array with shape '+str(shape)+' required')
    return result


def load_kernel(directory,*,tangent):
    """Compile only new wrappers; neither existing mechanization is edited."""
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    source_root=Path(__file__).parent
    hashes={name:hashlib.sha256((source_root/name).read_bytes()).hexdigest() for name in SOURCES}
    compiler='c++' if tangent else 'cc'
    flags=['-O2','-std=c++17' if tangent else '-std=c99','-D_DEFAULT_SOURCE','-fPIC','-shared']
    identity=dict(version=VERSION,sources=hashes,compiler=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0],
        flags=flags,tangent=bool(tangent),python=platform.python_version(),numpy=np.__version__,
        machine=platform.machine(),system=platform.system(),byteorder=sys.byteorder,
        numerical_environment={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
    binary=directory/('stream-'+_digest(identity)+'.so')
    if not binary.exists():
        name='ilvis0_stream_tangent.cpp' if tangent else 'ilvis0_stream_value.c'
        descriptor,temporary=tempfile.mkstemp(prefix='stream-',suffix='.partial.so',dir=directory)
        os.close(descriptor)
        try:
            subprocess.run([compiler,*flags,str(source_root/name),'-lm','-o',temporary],check=True,capture_output=True)
            os.replace(temporary,binary)
        finally:
            if os.path.exists(temporary):os.unlink(temporary)
    identity['binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
    library=ctypes.CDLL(str(binary))
    array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    library.ilvis0_stream_size.argtypes=[];library.ilvis0_stream_size.restype=ctypes.c_size_t
    library.ilvis0_stream_clock.argtypes=[ctypes.c_void_p];library.ilvis0_stream_clock.restype=ctypes.c_double
    library.ilvis0_stream_count.argtypes=[ctypes.c_void_p];library.ilvis0_stream_count.restype=ctypes.c_size_t
    library.ilvis0_stream_init.argtypes=[ctypes.c_void_p,array,array,array,array,array,ctypes.c_int,
        ctypes.c_int,ctypes.c_double,ctypes.c_double]
    library.ilvis0_stream_init.restype=None
    library.ilvis0_stream_push.argtypes=[ctypes.c_void_p,ctypes.c_size_t,array,array,array,
        ctypes.c_size_t,array,array,array,ctypes.POINTER(ctypes.c_int)]
    library.ilvis0_stream_push.restype=ctypes.c_int
    return library,identity


class Stream:
    """One fixed parameter point. Process every supplied packet, including tails.

    Memory is O(block packets + block queries * tangent columns), not total
    recording length. Checkpoints are integrity checks, not authenticated files;
    restore only trusted checkpoints from the exact source/runtime environment.
    """
    def __init__(self,directory,*,initial_c,initial_v,initial_r,limits,point,model,
                 profile,gravity,radius,input_id,tangent=True):
        c=_array(initial_c,(3,));v=_array(initial_v,(3,));r=_array(initial_r,(3,3))
        limits=_array(limits,(27,));point=_array(point,(27,))
        if (isinstance(model,bool) or model not in (0,1,2) or not isinstance(profile,bool)
                or not isinstance(tangent,bool) or not isinstance(input_id,str) or not input_id
                or not math.isfinite(gravity) or gravity<=0. or not math.isfinite(radius) or radius<=0.
                or np.any(limits<0.) or np.any(abs(point)>1.) or limits[26]>1.
                or gravity+point[24]*limits[24]<=0.
                or np.any(1.+point[15:21]*limits[15:21]<=0.)
                or abs(c[0])>=math.pi/2-1e-6
                or not np.allclose(r.T@r,np.eye(3),rtol=0.,atol=1e-10)
                or abs(np.linalg.det(r)-1.)>1e-10):
            raise ValueError('supported model, rotation, positive physical domain and normalized parameters required')
        self._config=dict(initial_c=c.tolist(),initial_v=v.tolist(),initial_r=r.tolist(),
            limits=limits.tolist(),point=point.tolist(),model=model,profile=profile,
            gravity=float(gravity),radius=float(radius),input_id=input_id,tangent=tangent)
        self.tangent=tangent;self.time_offset=float(limits[25]*point[25]);self._last_query=None
        self._library,self.identity=load_kernel(directory,tangent=tangent)
        self._state=ctypes.create_string_buffer(self._library.ilvis0_stream_size())
        self._library.ilvis0_stream_init(self._state,c,v,r,limits,point,model,int(profile),gravity,radius)

    @property
    def elapsed_s(self):return self._library.ilvis0_stream_clock(self._state)

    @property
    def packet_count(self):return self._library.ilvis0_stream_count(self._state)

    @property
    def state_bytes(self):return ctypes.sizeof(self._state)

    def push(self,theta,dv,dt,times,*,packet_offset,elapsed_s):
        dt=np.array(dt,dtype=np.float64,order='C',copy=True)
        if dt.ndim!=1 or not len(dt) or not np.all(np.isfinite(dt)) or np.any(dt<=0.):
            raise ValueError('nonempty finite positive packet periods required')
        theta=_array(theta,(len(dt),3));dv=_array(dv,(len(dt),3))
        times=np.array(times,dtype=np.float64,order='C',copy=True)
        if (isinstance(packet_offset,bool) or not isinstance(packet_offset,(int,np.integer))
                or packet_offset!=self.packet_count or elapsed_s!=self.elapsed_s
                or times.ndim!=1 or not np.all(np.isfinite(times))
                or np.any(np.diff(times)<0.) or (len(times) and self._last_query is not None and times[0]<self._last_query)):
            raise ValueError('contiguous packet offset/clock and ordered query times required')
        end=self.elapsed_s
        for period in dt:
            following=end+float(period)
            if not math.isfinite(following) or following<=end:
                raise ValueError('packet period does not advance the exact elapsed clock')
            end=following
        corrected=times+self.time_offset
        if len(times) and (corrected[0]<self.elapsed_s or corrected[-1]>end):
            raise ValueError('query times must lie inside this contiguous block including its boundary')
        out=np.empty((len(times),3))
        jac=np.empty((len(times),3,27)) if self.tangent else np.empty(1)
        candidate=ctypes.create_string_buffer(self._state.raw,len(self._state))
        boundaries=ctypes.c_int()
        code=self._library.ilvis0_stream_push(candidate,len(dt),theta,dv,dt,len(times),times,
            out,jac,ctypes.byref(boundaries))
        if code or not np.all(np.isfinite(out)) or (self.tangent and not np.all(np.isfinite(jac))):
            raise ValueError('streaming prediction outside supported native domain (code '+str(code)+')')
        self._state=candidate
        if len(times):self._last_query=float(times[-1])
        return dict(positions=out,jacobian=jac if self.tangent else None,boundaries=boundaries.value)

    def checkpoint(self):
        result=dict(version=VERSION,config=self._config,environment=self.identity,
            state_base64=base64.b64encode(self._state.raw).decode('ascii'),
            elapsed_s=self.elapsed_s,packet_count=self.packet_count,last_query=self._last_query)
        result['sha256']=_digest(result)
        return json.loads(_encoded(result))

    @classmethod
    def restore(cls,directory,checkpoint,*,input_id):
        saved=json.loads(_encoded(checkpoint));digest=saved.pop('sha256',None)
        if digest!=_digest(saved) or saved.get('version')!=VERSION or saved['config']['input_id']!=input_id:
            raise ValueError('checkpoint integrity, version or input identity mismatch')
        stream=cls(directory,**saved['config'])
        if saved['environment']!=stream.identity:raise ValueError('checkpoint source or numerical environment mismatch')
        data=base64.b64decode(saved['state_base64'],validate=True)
        if len(data)!=stream.state_bytes:raise ValueError('checkpoint state size mismatch')
        stream._state=ctypes.create_string_buffer(data,len(data));stream._last_query=saved['last_query']
        if stream.elapsed_s!=saved['elapsed_s'] or stream.packet_count!=saved['packet_count']:
            raise ValueError('checkpoint state disagrees with clock/packet metadata')
        return stream
