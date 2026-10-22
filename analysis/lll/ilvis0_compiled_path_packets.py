# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compiled full-input packet branch; no complete history/clock qualification."""
import ctypes
from fractions import Fraction as F
import hashlib
import math
from pathlib import Path
import subprocess
import numpy as np
from .ilvis0_path_jets import Jet3
from .ilvis0_path_packets import Prediction
from .ilvis0_path_step import _pack,_state
from .ilvis0_compiled_bounds import _check


def _binary64(value):
    try:
        out=float(value)
        if not math.isfinite(out) or F(out)!=F(value):raise ValueError()
    except (ValueError,TypeError,OverflowError):
        raise ValueError('unchanged finite binary64 raw/configuration constants required') from None
    return out


def _raw(values,shape):
    if isinstance(values,np.ndarray) and values.dtype==np.float64:
        out=np.array(values,dtype=np.float64,order='C',copy=True)
    else:
        original=np.asarray(values,dtype=object)
        out=np.array([_binary64(v) for v in original.flat]).reshape(original.shape)
    if out.shape!=shape or not np.all(np.isfinite(out)):
        raise ValueError('complete finite three-axis raw inputs required')
    return out


class Backend:
    def __init__(self,library):
        self.library=library;array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        library.ilvis0_bounds_runtime_ok.argtypes=[];library.ilvis0_bounds_runtime_ok.restype=ctypes.c_int
        library.ilvis0_compiled_path_packets.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_size_t,
            array,array,array,array,array,ctypes.c_double,ctypes.c_double,array,array,array,array]
        library.ilvis0_compiled_path_packets.restype=ctypes.c_int

    def predict_branch(self,configuration,theta,dv,dt,parameters,*,time,packet_index,
            maximum_packets=1024,maximum_seconds=30.):
        if (type(packet_index) is not int or not 0<=packet_index<len(dt)
                or len(parameters)!=27 or not all(isinstance(p,Jet3) for p in parameters)
                or any(not -1<=p.exact[0][0]<=p.exact[0][1]<=1 for p in parameters)
                or type(maximum_packets) is not int or not 1<=maximum_packets<=1000000
                or packet_index+1>maximum_packets or not math.isfinite(maximum_seconds) or maximum_seconds<=0
                or len(theta)!=len(dt) or len(dv)!=len(dt)):
            raise ValueError('all27 columns, supported packet and finite allowances required')
        config=configuration;model=config['model'];profile=config['profile']
        if type(model) is not int or model not in (0,1,2) or type(profile) is not bool:
            raise ValueError('supported physical and processing candidate required')
        if len(config['limits'])!=27 or len(config['initial_c'])!=3 or len(config['initial_v'])!=3:
            raise ValueError('complete initial conditions and limits required')
        r=_raw(config['initial_r'],(3,3)).ravel()
        packed_config=np.array([_binary64(v) for v in (*config['initial_c'],*config['initial_v'],*r,
            *config['limits'],config['gravity'],config['radius'])])
        n=packet_index+1;periods=_raw(dt[:n],(n,))
        if np.any(periods<=0):raise ValueError('positive packet periods required')
        th=_raw(theta[:n],(n,3));vel=_raw(dv[:n],(n,3));p=_pack(parameters)
        coordinates=np.empty((3,4,2));state=np.empty((15,4,2));fraction=np.empty((4,2));start=np.empty(1)
        code=self.library.ilvis0_compiled_path_packets(model,int(profile),n,packed_config,th,vel,periods,p,
            _binary64(time),maximum_seconds,coordinates,state,fraction,start)
        if code==4:raise ValueError('packet derivative execution allowance exhausted')
        _check(code)
        return Prediction(tuple(Jet3(row.tolist()) for row in coordinates),_state(state),packet_index,
            Jet3(fraction.tolist()),float(start[0]))


def load_backend(directory,*,source_directory=None):
    source=Path(source_directory)/'ilvis0_compiled_path_packets.cpp' if source_directory else Path(__file__).with_suffix('.cpp')
    files=(source,*(source.with_name('ilvis0_'+name+'.cpp') for name in ('path_step','path_arithmetic','compiled_bounds')))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    digest=hashlib.sha256(''.join(hashes.values()).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    flags=['-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off']
    binary=directory/('compiled-path-packets-'+digest+'.so')
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    backend=Backend(ctypes.CDLL(str(binary)))
    if not backend.library.ilvis0_bounds_runtime_ok():raise ValueError('unsupported floating-point runtime')
    return backend,dict(sources=hashes,source_sha256=digest,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        flags=flags,compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],
        derivative_order=3,runtime_ieee_guard=True,stable_rotation_branches_only=True,
        cooperative_time_limit=True,raw_binary64_constants_preserved=True,
        floating_point_native_execution_covered=False,full_history_qualified=False,
        clock_partition_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')
