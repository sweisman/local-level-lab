# SPDX-License-Identifier: AGPL-3.0-or-later
"""Successor packet adapter with explicit endpoint ownership and encoding."""
from dataclasses import dataclass
from fractions import Fraction as F
import ctypes
import hashlib
from pathlib import Path
import subprocess
from .ilvis0_compiled_path_packets import Backend as PreviousBackend,_raw,_binary64
from .ilvis0_path_motion import State
from .ilvis0_path_packets import Prediction
from .ilvis0_path_jets import Jet3


@dataclass(frozen=True)
class CompiledState(State):
    def report(self):
        report=super().report();report.pop('dyadic_bits')
        report.update(version='ilvis0-compiled-third-order-midpoint-state-v1',endpoint_encoding='outward binary64')
        return report


@dataclass(frozen=True)
class ClockPrediction(Prediction):
    one_sided:bool=False

    def report(self):
        result=super().report();result.update(version='ilvis0-clock-branch-prediction-v1',
            endpoint_encoding='outward binary64',partial_fraction_guard='nonnegative to native upper guard',
            one_sided_branch_requested=self.one_sided,native_floating_point_predicate_covered=False)
        return result


class Backend(PreviousBackend):
    def predict_branch(self,configuration,theta,dv,dt,parameters,*,time,packet_index,
            maximum_packets=1024,maximum_seconds=30.,allow_one_sided=False):
        if (type(packet_index) is not int or not 0<=packet_index<len(dt) or len(parameters)!=27
                or not all(isinstance(v,Jet3) for v in parameters) or type(allow_one_sided) is not bool):
            raise ValueError('complete clock path and explicit branch convention required')
        periods=_raw(dt[:packet_index+1],(packet_index+1,));start=0.
        for period in periods[:-1]:start+=float(period)
        end=start+float(periods[-1]);limit=F(_binary64(configuration['limits'][25]));query=F(_binary64(time))
        if limit<0:raise ValueError('nonnegative clock scale required')
        lo,hi=(query+limit*v for v in parameters[25].exact[0])
        if lo<F(start) or hi>F(end) or (packet_index>0 and lo==F(start) and not allow_one_sided):
            raise ValueError('query outside declared packet ownership; request endpoint limits explicitly')
        raw=super().predict_branch(configuration,theta,dv,dt,parameters,time=time,packet_index=packet_index,
            maximum_packets=maximum_packets,maximum_seconds=maximum_seconds)
        state=CompiledState(raw.state.coordinates,raw.state.velocity,raw.state.attitude)
        return ClockPrediction(raw.coordinates,state,raw.packet_index,raw.fraction,raw.start,allow_one_sided)


def load_backend(directory,*,source_directory=None):
    source=Path(source_directory)/'ilvis0_clock_path_packets.cpp' if source_directory else Path(__file__).with_suffix('.cpp')
    files=(source,*(source.with_name('ilvis0_'+name+'.cpp') for name in ('path_step','path_arithmetic','compiled_bounds')))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    digest=hashlib.sha256(''.join(hashes.values()).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    flags=['-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off']
    binary=directory/('clock-path-packets-'+digest+'.so')
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    backend=Backend(ctypes.CDLL(str(binary)))
    if not backend.library.ilvis0_bounds_runtime_ok():raise ValueError('unsupported floating-point runtime')
    return backend,dict(sources=hashes,source_sha256=digest,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        flags=flags,compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],
        derivative_order=3,runtime_ieee_guard=True,stable_rotation_branches_only=True,
        cooperative_time_limit=True,native_fraction_guard_supported=True,negative_fractions_supported=False,
        endpoint_encoding='outward binary64',raw_binary64_constants_preserved=True,
        floating_point_native_execution_covered=False,full_history_qualified=False,
        clock_partition_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')
