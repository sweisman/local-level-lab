# SPDX-License-Identifier: AGPL-3.0-or-later
"""One-packet state/input differential of the source-bound native equations."""
import ctypes
import hashlib
from pathlib import Path

VERSION='native-packet-noise-step-v1'


def derive(source,bridge,*,expected_source_sha256,expected_bridge_sha256,expected_wide_loader_sha256):
    from . import ilvis0_wide_tangent as wide
    sha=lambda value:hashlib.sha256(value).hexdigest()
    if (not isinstance(source,bytes) or not isinstance(bridge,bytes) or sha(source)!=expected_source_sha256
            or sha(bridge)!=expected_bridge_sha256 or sha(Path(wide.__file__).read_bytes())!=expected_wide_loader_sha256):
        raise ValueError('exact native/bridge/wider-loader source hash required')
    text=wide.derive(source,expected_sha256=expected_source_sha256);marker=b'static int tangent_gravity('
    if text.count(marker)!=1:raise ValueError('unsupported source-bound native header')
    header=text[:text.index(marker)]
    if header.count(b'std::array<long double,27>')!=1 or header.count(b'i<27')!=9:
        raise ValueError('unsupported complete dual derivative layout')
    header=header.replace(b'std::array<long double,27>',b'std::array<long double,15>').replace(b'i<27',b'i<15')
    return header+bridge


def load(directory,*,expected_source_sha256,expected_bridge_sha256,expected_wide_loader_sha256,reserve_build):
    import numpy as np
    from .native_build import cpp
    original=Path(__file__).with_name('ilvis0_tangent.cpp').read_bytes()
    bridge=Path(__file__).with_name('ilvis0_noise_bridge.cpp').read_bytes()
    raw=derive(original,bridge,expected_source_sha256=expected_source_sha256,
        expected_bridge_sha256=expected_bridge_sha256,expected_wide_loader_sha256=expected_wide_loader_sha256)
    binary,compiled=cpp(directory,raw,prefix='noise-step',expected_sha256=hashlib.sha256(raw).hexdigest(),reserve_build=reserve_build)
    library=ctypes.CDLL(str(binary));bits=library.lll_noise_step_bits();size=library.lll_noise_step_size()
    if bits<=53 or bits!=np.finfo(np.longdouble).nmant+1 or size!=np.dtype(np.longdouble).itemsize:
        raise ValueError('matching genuinely wider native/NumPy scalar ABI required')
    extended=np.ctypeslib.ndpointer(dtype=np.longdouble,flags='C_CONTIGUOUS')
    double=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');function=library.lll_noise_step
    function.argtypes=[extended]*6+[ctypes.c_int,ctypes.c_int,ctypes.c_double,extended,ctypes.c_int,
        extended,double,extended,double];function.restype=ctypes.c_int
    return function,dict(compiled,version=VERSION,original_source_sha256=expected_source_sha256,
        bridge_source_sha256=expected_bridge_sha256,wide_loader_source_sha256=expected_wide_loader_sha256,
        internal_mantissa_bits=bits,scalar_bytes=size,state_error_columns=9,input_error_columns=6,
        state_error_order=['attitude_body_x','attitude_body_y','attitude_body_z','velocity_north_mps',
            'velocity_east_mps','velocity_down_mps','latitude_rad','longitude_rad','height_m'],
        input_error_order=['corrected_dtheta_x_rad','corrected_dtheta_y_rad','corrected_dtheta_z_rad',
            'corrected_delta_v_x_mps','corrected_delta_v_y_mps','corrected_delta_v_z_mps'],
        input_derivative_convention='additive_corrected_increment',mean_arithmetic='native-long-double',
        scientific_equations_reused=True,clock_dispatch_in_bridge=False,
        caller_must_preserve_query_packet_association=True,observed_fitting_authorized=False)


def evaluate(kernel,*,coordinates,velocity,rotation,theta,delta_v,dt,model,gravity,radius,removal,
             anchor_height,lever,derivatives,reserve):
    import math
    import numpy as np
    if (type(model) is not int or model not in (0,1,2) or type(derivatives) is not bool or not callable(reserve)):
        raise ValueError('explicit candidate, derivative mode and native accounting required')
    values=[]
    for raw,shape in ((coordinates,(3,)),(velocity,(3,)),(rotation,(3,3)),(theta,(3,)),(delta_v,(3,)),(lever,(3,))):
        a=np.array(raw,dtype=np.longdouble,copy=True,order='C')
        if a.shape!=shape or not np.all(np.isfinite(a)):raise ValueError('finite aligned native state/input arrays required')
        values.append(a)
    c,v,r,th,dv,arm=values
    scalars=np.array([dt,gravity,radius,removal],dtype=np.longdouble)
    if (not np.all(np.isfinite(scalars)) or dt<=0 or gravity<=0 or radius<=0 or not 0<=removal<=1
            or abs(c[0])>=math.pi/2-1e-6 or np.max(abs(r.T@r-np.eye(3)))>1e-8
            or np.linalg.det(r.astype(float))<=0 or (anchor_height is not None and
                (not math.isfinite(anchor_height) or anchor_height<=-6371000.))):
        raise ValueError('supported physical state, scalar domain and proper orientation required')
    state=np.zeros(15,dtype=np.longdouble);jacobian=np.zeros((9,15));observation=np.zeros(3,dtype=np.longdouble)
    observed_jacobian=np.zeros((3,15));reserve(native_calls=1)
    code=kernel(c,v,r,th,dv,scalars,model,int(anchor_height is not None),anchor_height or 0.,arm,int(derivatives),
        state,jacobian,observation,observed_jacobian)
    if code or any(not np.all(np.isfinite(a)) for a in (state,jacobian,observation,observed_jacobian)):
        raise ValueError('native one-packet differential outside supported domain')
    return dict(coordinates=state[:3],velocity=state[3:6],rotation=state[6:].reshape(3,3),
        observation=observation,state_jacobian=jacobian,observation_jacobian=observed_jacobian)
