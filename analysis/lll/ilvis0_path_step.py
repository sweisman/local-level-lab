# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compiled interval midpoint component; stable rotation branches only."""
import ctypes
import hashlib
from pathlib import Path
import subprocess
import numpy as np
from .ilvis0_path_jets import Jet3
from .ilvis0_path_motion import State
from .ilvis0_compiled_bounds import _check


def _pack(jets):
    if not all(isinstance(v,Jet3) for v in jets):
        raise ValueError('complete actual-derivative jets required')
    return np.ascontiguousarray([v.report()['derivatives'] for v in jets],dtype=np.float64)


def _state(values):
    jets=tuple(Jet3(row.tolist()) for row in values)
    return State(jets[:3],jets[3:6],tuple(tuple(jets[6+3*i:9+3*i]) for i in range(3)))


class Backend:
    def __init__(self,library):
        self.library=library
        array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        library.ilvis0_bounds_runtime_ok.argtypes=[];library.ilvis0_bounds_runtime_ok.restype=ctypes.c_int
        library.ilvis0_path_step.argtypes=[ctypes.c_int,array,array,array]
        library.ilvis0_path_step.restype=ctypes.c_int
        library.ilvis0_path_rotation.argtypes=[array,array]
        library.ilvis0_path_rotation.restype=ctypes.c_int

    def step(self,model,state,theta,dv,period,gravity,radius,removal):
        if (type(model) is not int or model not in (0,1,2) or not isinstance(state,State)
                or len(theta)!=3 or len(dv)!=3):
            raise ValueError('supported model, complete state and three-axis increments required')
        packed_state=_pack((*state.coordinates,*state.velocity,*(v for row in state.attitude for v in row)))
        packed_input=_pack((*theta,*dv,period,gravity,radius,removal));out=np.empty((15,4,2))
        _check(self.library.ilvis0_path_step(model,packed_state,packed_input,out))
        return _state(out)

    def rotation(self,vector):
        if len(vector)!=3:raise ValueError('three complete rotation jets required')
        packed=_pack(vector);out=np.empty((9,4,2))
        _check(self.library.ilvis0_path_rotation(packed,out))
        return tuple(tuple(Jet3(out[3*i+j].tolist()) for j in range(3)) for i in range(3))


def load_backend(directory,*,source_directory=None):
    source=Path(source_directory)/'ilvis0_path_step.cpp' if source_directory else Path(__file__).with_suffix('.cpp')
    files=(source,source.with_name('ilvis0_path_arithmetic.cpp'),source.with_name('ilvis0_compiled_bounds.cpp'))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    digest=hashlib.sha256(''.join(hashes.values()).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    flags=['-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off']
    binary=directory/('path-step-'+digest+'.so')
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    backend=Backend(ctypes.CDLL(str(binary)))
    if not backend.library.ilvis0_bounds_runtime_ok():raise ValueError('unsupported floating-point runtime')
    return backend,dict(sources=hashes,source_sha256=digest,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        flags=flags,compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],
        derivative_order=3,runtime_ieee_guard=True,stable_rotation_branches_only=True,
        floating_point_native_execution_covered=False,full_history_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
