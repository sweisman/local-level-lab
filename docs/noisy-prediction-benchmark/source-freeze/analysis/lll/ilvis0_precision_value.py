# SPDX-License-Identifier: AGPL-3.0-or-later
"""Precision-only value probes derived from the unchanged tangent equations.

No optimizer or stopping labels are exposed. Binary64 clock scheduling and
parameter conversion remain fixed. Extended residuals are subtracted before
the ABI converts them back to binary64. This is diagnostic, not a fit method.
"""
import ctypes
import hashlib
import math
from pathlib import Path
import subprocess

VERSION='ilvis0-scalar-precision-diagnostic-v1'


def derive(source,*,expected_sha256,precision):
    if not isinstance(source,bytes) or hashlib.sha256(source).hexdigest()!=expected_sha256:
        raise ValueError('exact base source hash required')
    if precision not in ('double','long_double'):raise ValueError('supported precision required')
    text=source.decode('utf-8')
    begin='static void mul(';end='extern "C" int ilvis0_tangent('
    if text.count(begin)!=1 or text.count(end)!=1:raise ValueError('unsupported tangent layout')
    body=text[text.index(begin):text.index(end)]
    replacements={
        'static int tangent_gravity(':'static int precision_value(',
        'double *out,double *jacobian,int *boundaries,':
            'double *out,const double *observations,double *difference,int *boundaries,',
        'p[i]=point[i]*limits[i];p[i].d[i]=limits[i];':'p[i]=point[i]*limits[i];',
        'if(profile) {p[26]=(p[26]+1)/2;}':'if(profile) {p[26]=(static_cast<double>(p[26].v)+1)/2;}',
        'times[j]+p[25].v<=end':'times[j]+static_cast<double>(p[25].v)<=end',
        'fraction=(times[j]+p[25]-start)/dt[k];':
            'fraction=(times[j]+static_cast<double>(p[25].v)-start)/dt[k];',
        'for(int h=0;h<27;h++)jacobian[(3*j+i)*27+h]=value.d[h];':
            'difference[3*j+i]=static_cast<double>(value.v-Real(observations[3*j+i]));',
    }
    for old,new in replacements.items():
        if body.count(old)!=1:raise ValueError('unsupported tangent layout: '+old)
        body=body.replace(old,new)
    real='double' if precision=='double' else 'long double'
    prefix='''// Derived scalar diagnostics; mechanization comes from the bound tangent source.
#include <cmath>
#include <cstddef>
#include <cstring>
#include <limits>
using Real=REAL;
struct Dual {
    Real v;
    Dual(Real value=0):v(value) {}
    Dual& operator+=(const Dual& b) {v+=b.v;return *this;}
};
static Dual operator+(const Dual&a,const Dual&b){return a.v+b.v;}
static Dual operator-(const Dual&a,const Dual&b){return a.v-b.v;}
static Dual operator-(const Dual&a){return -a.v;}
static Dual operator*(const Dual&a,const Dual&b){return a.v*b.v;}
static Dual operator/(const Dual&a,const Dual&b){return a.v/b.v;}
static Dual sin(const Dual&a){return std::sin(a.v);}
static Dual cos(const Dual&a){return std::cos(a.v);}
static Dual sqrt(const Dual&a){return std::sqrt(a.v);}
static Dual pow(const Dual&a,double b){return std::pow(a.v,Real(b));}
static bool operator<(const Dual&a,double b){return a.v<b;}
'''.replace('REAL',real)
    suffix='''
extern "C" int ilvis0_precision_value(size_t n,const double *theta,const double *dv,const double *dt,
    size_t m,const double *times,const double *initial_c,const double *initial_v,
    const double *initial_r,const double *limits,const double *point,int model,int profile,
    double gravity,double radius,double *out,const double *observations,double *difference,
    int *boundaries,int height_gravity,double anchor_height) {
    return precision_value(n,theta,dv,dt,m,times,initial_c,initial_v,initial_r,limits,point,
        model,profile,gravity,radius,out,observations,difference,boundaries,height_gravity,anchor_height);
}
extern "C" int ilvis0_precision_bits(){return std::numeric_limits<Real>::digits;}
'''
    return (prefix+body+suffix).encode()


def load(directory,*,precision,gravity_anchor_height_m=None,expected_source_sha256=None):
    import numpy as np
    if gravity_anchor_height_m is not None and (not math.isfinite(gravity_anchor_height_m) or gravity_anchor_height_m<=-6371000.):
        raise ValueError('finite supported gravity anchor height required')
    original=Path(__file__).with_name('ilvis0_tangent.cpp').read_bytes()
    base=hashlib.sha256(original).hexdigest()
    generated=derive(original,expected_sha256=base if expected_source_sha256 is None else expected_source_sha256,precision=precision)
    sha=hashlib.sha256(generated).hexdigest();directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    source=directory/('precision-value-'+sha+'.cpp');binary=source.with_suffix('.so')
    if source.exists() and source.read_bytes()!=generated:raise ValueError('generated source hash mismatch')
    if not source.exists():source.write_bytes(generated)
    flags=['-O2','-std=c++17','-fPIC','-shared']
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    library=ctypes.CDLL(str(binary));bits=library.ilvis0_precision_bits()
    if (precision=='double' and bits!=53) or (precision=='long_double' and bits<=53):
        raise ValueError('unsupported platform precision')
    function=library.ilvis0_precision_value
    array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    function.argtypes=[ctypes.c_size_t,array,array,array,ctypes.c_size_t,array,array,array,array,array,array,
        ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,array,array,array,ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,ctypes.c_double]
    function.restype=ctypes.c_int
    def kernel(*args):return function(*args,int(gravity_anchor_height_m is not None),gravity_anchor_height_m or 0.)
    return kernel,dict(version=VERSION,source_sha256=base,derived_source_sha256=sha,
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),precision=precision,mantissa_bits=bits,
        clock_mantissa_bits=53,clock_dispatch='binary64-frozen',profile_mapping='binary64-frozen',
        residual_subtraction='before-binary64-cast',gravity_anchor_height_m=gravity_anchor_height_m,
        compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],flags=flags)


def longitude_residual(values):
    import numpy as np
    result=np.array(values,dtype=float,copy=True)
    if not np.all(np.isfinite(result)):raise ValueError('finite longitude residual required')
    outside=(result < -math.pi)|(result >= math.pi)
    result[outside]=(result[outside]+math.pi)%(2*math.pi)-math.pi
    return result


def _whiten(problem,delta,longitude):
    from scipy.linalg import solve_triangular
    if longitude=='legacy':return problem.whiten(delta)
    stable=delta.copy();stable[:,1]=longitude_residual(stable[:,1])
    if getattr(problem,'observation_error',None) is not None:return problem.whiten_stacked(stable.ravel())
    return solve_triangular(problem.cholesky,stable.ravel(),lower=True)


def calculate(problem,point,model,*,kernel,longitude):
    import numpy as np
    from .ilvis0_shape import PARAMETERS
    from .ilvis0_exploratory import MODELS
    if longitude not in ('legacy','stable'):raise ValueError('explicit longitude residual convention required')
    if model not in MODELS:raise ValueError('supported candidate required')
    problem.bounds.decode(point)
    names=problem.bounds.active;u=dict(zip(names,point))
    expanded=np.array([u.get(name,0.) for name in PARAMETERS])
    limits=np.array([problem.bounds.limits.get(name,0.) for name in PARAMETERS])
    c=np.array([problem.initial['latitude_rad'],problem.initial['longitude_rad'],problem.initial['height_m']])
    out=np.empty_like(problem.gps);delta=np.empty_like(problem.gps);boundaries=ctypes.c_int()
    code=kernel(len(problem.dt),np.ascontiguousarray(problem.theta),np.ascontiguousarray(problem.dv),
        np.ascontiguousarray(problem.dt),len(problem.gps_times),np.ascontiguousarray(problem.gps_times),c,
        np.ascontiguousarray(problem.initial['velocity_ned_mps']),np.ascontiguousarray(problem.initial['attitude_body_to_ned']),
        limits,expanded,MODELS.index(model),int(problem.bounds.fit_earth_removal),problem.gravity,problem.radius or 6371000.,
        out,np.ascontiguousarray(problem.gps),delta,ctypes.byref(boundaries))
    if code or not np.all(np.isfinite(out)) or not np.all(np.isfinite(delta)):
        raise ValueError('precision prediction outside supported native domain')
    residual=_whiten(problem,delta,longitude)
    return dict(coordinates=out,coordinate_difference=delta,residual=residual,boundaries=boundaries.value)


def compare(problem,points,*,source_residuals,source_converged,model,kernel_factory,reserve,save,save_bytes,check_continue):
    import io
    import numpy as np
    from .studies.artifacts import digest
    from .ilvis0_solver_position import physical_residual_step
    points=np.asarray(points,float);reference=np.asarray(source_residuals,float)
    if (points.shape!=(2,len(problem.bounds.active)) or reference.shape!=(2,problem.gps.size)
            or type(source_converged) is not bool or not np.all(np.isfinite(points))
            or not np.all(np.isfinite(reference))):raise ValueError('two complete unchanged saved points required')
    for point in points:problem.bounds.decode(point)
    records=[];modes={};native_calls=0
    for precision in ('double','long_double'):
        check_continue();kernel,metadata=kernel_factory(precision);save('compilation-'+precision+'.json',metadata)
        pairs=[]
        for index,point in enumerate(points):
            check_continue();reserve(native_calls=1,packet_visits=len(problem.dt)*len(problem.gps_times));native_calls+=1
            value=calculate(problem,point,model,kernel=kernel,longitude='legacy' if precision=='double' else 'stable')
            stable=_whiten(problem,value['coordinate_difference'],'stable')
            name=f'{precision}-{index}.npz';stream=io.BytesIO()
            arrays=dict(point=point,coordinates=value['coordinates'],coordinate_difference=value['coordinate_difference'],
                stable_residual=stable)
            if precision=='double':arrays['legacy_residual']=value['residual']
            np.savez_compressed(stream,**arrays);raw=stream.getvalue();save_bytes(name,raw)
            records.append(dict(precision=precision,index=index,artifact=name,sha256=digest(raw),boundaries=value['boundaries']))
            if precision=='double' and not np.array_equal(value['residual'],reference[index]):
                raise ValueError('binary64 value path differs from frozen residual; no further probes permitted')
            pairs.append(dict(stable=stable,legacy=value['residual'],delta=value['coordinate_difference']))
        for suffix in (('legacy','stable') if precision=='double' else ('stable',)):
            first,last=(v[suffix] for v in pairs);cost0=float(first@first);cost1=float(last@last)
            physical=physical_residual_step(problem,_whiten(problem,pairs[1]['delta']-pairs[0]['delta'],'stable'))
            label=('long-double' if precision=='long_double' else 'double')+'-'+suffix
            modes[label]=dict(baseline_cost=cost0,corrected_cost=cost1,
                relative_cost_change=abs(cost1-cost0)/max(cost0,cost1,1.),
                position_rms_neu_m=np.sqrt(np.mean(physical*physical,axis=0)).tolist(),
                position_max_abs_neu_m=np.max(abs(physical),axis=0).tolist())
    result=dict(version=VERSION,passed=True,model=model,source_converged=source_converged,labels_changed=False,
        native_calls=native_calls,packet_query_visits=native_calls*len(problem.dt)*len(problem.gps_times),
        active_parameters=list(problem.bounds.active),modes=modes,artifacts=records,
        binary64_reference_exact=True,optimizer_starts=0,scientific_decision='abstain',confidence_calibrated=False)
    save('precision.json',result)
    return result
