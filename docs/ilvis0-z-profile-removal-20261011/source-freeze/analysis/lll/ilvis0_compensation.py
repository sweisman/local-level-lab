# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate linear-within-packet compensation experiment; never production repair.

Ordinary rate integrals, not already-compensated finite increments, are assumed.
Coning and rotating-force series are checked against independent continuous ODEs.
"""
import ctypes
import hashlib
import math
from pathlib import Path
import subprocess

import numpy as np

from . import ilvis0_estimator as estimator, ilvis0_exploratory as explore
from . import ilvis0_geographic_controls as controls, ilvis0_shape as shape

VERSION='ilvis0-linear-packet-compensation-controls-v1'
MODES=('baseline','linear','coning','sculling','combined')


def validate(mode,convention):
    if mode not in MODES or convention not in ('ordinary_rate_integrals','already_compensated'):
        raise ValueError('explicit supported mode and increment convention required')
    if mode!='baseline' and convention!='ordinary_rate_integrals':
        raise ValueError('corrections require ordinary rate integrals; do not compensate twice')


def packet(theta,dv,h,alpha,beta,fraction,mode,*,convention):
    validate(mode,convention)
    arrays=[np.asarray(x,float) for x in (theta,dv,alpha,beta)]
    if (any(x.shape!=(3,) or not np.all(np.isfinite(x)) for x in arrays)
        or not math.isfinite(h) or h<=0 or not math.isfinite(fraction) or not 0<=fraction<=1):
        raise ValueError('finite vectors, positive interval and supported fraction required')
    theta,dv,alpha,beta=arrays
    if mode=='baseline':return theta*fraction,dv*fraction
    t=h*fraction
    w=theta/h+alpha*(t-h)/2; force=dv/h+beta*(t-h)/2
    angle=w*t; velocity=force*t
    if mode in ('coning','combined'):angle=angle+t**3*np.cross(w,alpha)/12
    if mode in ('sculling','combined'):
        velocity=velocity+t**3*(np.cross(w,np.cross(w,force))/24+
            (np.cross(w,beta)-np.cross(alpha,force))/12)
    return angle,velocity


def load_kernel(directory):
    source=Path(__file__).with_name('ilvis0_compensation.cpp')
    dependency=source.with_name('ilvis0_tangent.cpp')
    digest=hashlib.sha256(source.read_bytes()+dependency.read_bytes()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    binary=directory/f'compensation-{digest}.so';flags=['-O2','-std=c++17','-fPIC','-shared']
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    library=ctypes.CDLL(str(binary));function=library.ilvis0_compensated_tangent
    array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    function.argtypes=[ctypes.c_size_t,array,array,array,ctypes.c_size_t,array,array,array,array,array,array,
        ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,array,array,ctypes.POINTER(ctypes.c_int)]
    function.restype=ctypes.c_int
    return function,dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        dependency_sha256=hashlib.sha256(dependency.read_bytes()).hexdigest(),
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],flags=flags)


class CompensatedProblem(shape.TangentProblem):
    def __init__(self,*args,mode,convention,**kwargs):
        validate(mode,convention)
        super().__init__(*args,**kwargs)
        if mode!='baseline' and len(self.dt)<3:raise ValueError('three contiguous intervals required for slopes')
        self.mode=mode;self.convention=convention

    def prediction_tangent(self,point,model):
        self.bounds.decode(point)
        u=dict(zip(self.bounds.active,point))
        expanded=np.array([u.get(name,0.) for name in shape.PARAMETERS])
        limits=np.array([self.bounds.limits.get(name,0.) for name in shape.PARAMETERS])
        coordinates=np.array([self.initial['latitude_rad'],self.initial['longitude_rad'],self.initial['height_m']])
        out=np.empty_like(self.gps);jac=np.empty((out.size,27));boundaries=ctypes.c_int()
        code=self.tangent_kernel(len(self.dt),np.ascontiguousarray(self.theta),np.ascontiguousarray(self.dv),
            np.ascontiguousarray(self.dt),len(self.gps_times),np.ascontiguousarray(self.gps_times),coordinates,
            np.ascontiguousarray(self.initial['velocity_ned_mps']),np.ascontiguousarray(self.initial['attitude_body_to_ned']),
            limits,expanded,explore.MODELS.index(model),int(self.bounds.fit_earth_removal),MODES.index(self.mode),
            self.gravity,self.radius or 6371000.,out,jac,ctypes.byref(boundaries))
        if code or not np.all(np.isfinite(out)) or not np.all(np.isfinite(jac)):
            raise ValueError('compensated prediction outside supported domain')
        return out,jac[:,[shape.PARAMETERS.index(name) for name in self.bounds.active]],boundaries.value

    def predict(self,point,model):return self.prediction_tangent(point,model)[0]


def problem(f,kernel,mode,*,convention):
    sigma=np.tile(.01/f['metric'],len(f['gps_times']))
    return CompensatedProblem(f['theta'],f['dv'],f['dt'],f['gps_times'],f['gps'],np.diag(sigma**2),
        f['initial'],estimator.Bounds(controls.LIMITS),fit_earth_removal=False,kernel=None,tangent_kernel=kernel,
        mode=mode,convention=convention,clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=6371000.)
