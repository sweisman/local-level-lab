# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extended residuals and all forward derivatives from bound native equations.

Historical arithmetic and stopping implementations are unchanged. This module
provides a separately qualifiable problem adapter, not a scientific decision.
"""
import ctypes
import hashlib
import math
from pathlib import Path
import subprocess

VERSION='ilvis0-wide-residual-tangent-v1'


def derive(source,*,expected_sha256):
    from .ilvis0_precision import extended_source
    if not isinstance(source,bytes) or hashlib.sha256(source).hexdigest()!=expected_sha256:
        raise ValueError('exact native source hash required')
    text=extended_source(source.decode());end='extern "C" int ilvis0_tangent('
    if text.count(end)!=1:raise ValueError('unsupported native tangent layout')
    text=text[:text.index(end)]
    replacements={
        'double *out,double *jacobian,int *boundaries,':
            'double *out,double *jacobian,const double *observations,double *difference,int *boundaries,',
        'if(profile) {p[26]=(p[26]+1)/2;}':
            'if(profile) {p[26]=(p[26]+1)/2;p[26].v=(point[26]*limits[26]+1)/2;}',
        'fraction=(times[j]+p[25]-start)/dt[k];':
            'fraction=(times[j]+p[25]-start)/dt[k];\n            fraction.v=(times[j]+static_cast<double>(p[25].v)-start)/dt[k];',
        'out[3*j+i]=value.v;':
            'out[3*j+i]=value.v;\n                difference[3*j+i]=static_cast<double>(value.v-static_cast<long double>(observations[3*j+i]));',
    }
    for old,new in replacements.items():
        if text.count(old)!=1:raise ValueError('unsupported native tangent layout: '+old)
        text=text.replace(old,new)
    suffix='''
extern "C" int ilvis0_wide_tangent(size_t n,const double *theta,const double *dv,const double *dt,
    size_t m,const double *times,const double *initial_c,const double *initial_v,
    const double *initial_r,const double *limits,const double *point,int model,int profile,
    double gravity,double radius,double *out,double *jacobian,const double *observations,
    double *difference,int *boundaries,int height_gravity,double anchor_height) {
    return tangent_gravity(n,theta,dv,dt,m,times,initial_c,initial_v,initial_r,limits,point,
        model,profile,gravity,radius,out,jacobian,observations,difference,boundaries,height_gravity,anchor_height);
}
extern "C" int ilvis0_wide_bits(){return std::numeric_limits<long double>::digits;}
'''
    return (text+suffix).encode()


def load(directory,*,gravity_anchor_height_m=None,expected_source_sha256=None):
    import numpy as np
    if gravity_anchor_height_m is not None and (not math.isfinite(gravity_anchor_height_m) or gravity_anchor_height_m<=-6371000.):
        raise ValueError('finite supported gravity anchor height required')
    original=Path(__file__).with_name('ilvis0_tangent.cpp').read_bytes();base=hashlib.sha256(original).hexdigest()
    raw=derive(original,expected_sha256=base if expected_source_sha256 is None else expected_source_sha256)
    sha=hashlib.sha256(raw).hexdigest();directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    source=directory/('wide-tangent-'+sha+'.cpp');binary=source.with_suffix('.so')
    if source.exists() and source.read_bytes()!=raw:raise ValueError('derived tangent source hash mismatch')
    if not source.exists():source.write_bytes(raw)
    flags=['-O2','-std=c++17','-fPIC','-shared']
    if not binary.exists():
        partial=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(partial)],check=True,capture_output=True);partial.replace(binary)
    library=ctypes.CDLL(str(binary));bits=library.ilvis0_wide_bits()
    if bits<=53:raise ValueError('genuinely wider arithmetic required')
    array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');function=library.ilvis0_wide_tangent
    function.argtypes=[ctypes.c_size_t,array,array,array,ctypes.c_size_t,array,array,array,array,array,array,
        ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,array,array,array,array,
        ctypes.POINTER(ctypes.c_int),ctypes.c_int,ctypes.c_double]
    function.restype=ctypes.c_int
    def kernel(*args,observations=None,difference=None):
        if len(args)!=18:raise ValueError('original tangent ABI required')
        # Forecasting supplies no receiver coordinates: its output is propagated
        # directly. These zero references merely fill an unused diagnostic buffer.
        if observations is None:observations=np.zeros((args[4],3))
        if difference is None:difference=np.empty((args[4],3))
        return function(*args[:-1],observations,difference,args[-1],int(gravity_anchor_height_m is not None),gravity_anchor_height_m or 0.)
    return kernel,dict(version=VERSION,original_source_sha256=base,source_sha256=sha,
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),internal_mantissa_bits=bits,
        residual_subtraction='before-binary64-cast',packet_clock_changed=False,clock_dispatch='binary64-frozen',
        profile_mapping='binary64-frozen',query_fraction='binary64-frozen',parameter_products='binary64-frozen',
        gravity_anchor_height_m=gravity_anchor_height_m,compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],flags=flags)


def evaluate(base,point,model,*,kernel):
    import numpy as np
    from .ilvis0_shape import PARAMETERS
    from .ilvis0_exploratory import MODELS
    if model not in MODELS:raise ValueError('supported physical candidate required')
    base.bounds.decode(point);u=dict(zip(base.bounds.active,point))
    expanded=np.array([u.get(name,0.) for name in PARAMETERS]);limits=np.array([base.bounds.limits.get(name,0.) for name in PARAMETERS])
    c=np.array([base.initial[k] for k in ('latitude_rad','longitude_rad','height_m')])
    out=np.empty_like(base.gps);delta=np.empty_like(base.gps);jac=np.empty((out.size,27));boundaries=ctypes.c_int()
    code=kernel(len(base.dt),np.ascontiguousarray(base.theta),np.ascontiguousarray(base.dv),np.ascontiguousarray(base.dt),
        len(base.gps_times),np.ascontiguousarray(base.gps_times),c,np.ascontiguousarray(base.initial['velocity_ned_mps']),
        np.ascontiguousarray(base.initial['attitude_body_to_ned']),limits,expanded,MODELS.index(model),
        int(base.bounds.fit_earth_removal),base.gravity,base.radius or 6371000.,out,jac,ctypes.byref(boundaries),
        observations=np.ascontiguousarray(base.gps),difference=delta)
    if code or any(not np.all(np.isfinite(v)) for v in (out,delta,jac)):
        raise ValueError('wide tangent prediction outside supported native domain')
    columns=[PARAMETERS.index(name) for name in base.bounds.active]
    return out,delta,jac[:,columns],boundaries.value


def problem(base,*,kernel):
    from .ilvis0_shape import TangentProblem
    if not isinstance(base,TangentProblem) or not callable(kernel):raise ValueError('explicit native problem and wider kernel required')
    class WideProblem(TangentProblem):
        def prediction_tangent(self,point,model):
            out,delta,jac,b=evaluate(self,point,model,kernel=kernel)
            return out,jac,b
        def predict(self,point,model):return self.prediction_tangent(point,model)[0]
        def residual(self,point,model):return self.residual_tangent(point,model)[0]
        def residual_tangent(self,point,model):
            import numpy as np
            from scipy.linalg import solve_triangular
            from .ilvis0_precision_value import _whiten
            out,delta,jac,b=evaluate(self,point,model,kernel=kernel)
            if np.any(np.abs(np.abs(delta[:,1])-math.pi)<32*np.finfo(float).eps):
                raise ValueError('longitude derivative crosses wrapping discontinuity')
            return _whiten(self,delta,'stable'),self.whiten_columns(jac),b
    result=WideProblem.__new__(WideProblem);result.__dict__=base.__dict__.copy();result.tangent_kernel=kernel
    result.native_residual_difference_supported=True
    return result
