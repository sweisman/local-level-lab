# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional recorded IMU/GPS fits. Assumptions are not independent evidence.

Separate from the evidence-gated observed estimator and all calibrated policies.
Native integration retains every packet. The optional C accelerator implements
the reference midpoint equations, including a common hypothesized logging correction.
"""
import ctypes
import hashlib
import math
from pathlib import Path
import subprocess

import numpy as np

from . import ilvis0_estimator as estimator, ilvis0_forward as forward

VERSION = 'ilvis0-conditional-recorded-fit-v1'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
# Explicit development envelopes, NOT instrument specifications or confidence bounds.
LIMITS = {f'{name}_{axis}': limit for name, limit in (
    ('attitude', math.radians(10)), ('velocity', 20.), ('position', 100.),
    ('gyro_bias', math.radians(20)/3600), ('accel_bias', .25),
    ('gyro_gain', .02), ('accel_gain', .15), ('lever', 10.)) for axis in estimator.AXES}
LIMITS.update(attitude_z=math.pi, gravity_delta=.05, time_offset=.15)


class ConditionalBounds:
    def __init__(self, limits, *, fit_earth_removal):
        self.base = estimator.Bounds(limits)
        self.fit_earth_removal = fit_earth_removal
        self.limits = dict(self.base.limits, **({'earth_removal': 1.} if fit_earth_removal else {}))
        self.active = self.base.active + (('earth_removal',) if fit_earth_removal else ())

    def decode(self, point):
        point = np.asarray(point, float)
        if point.shape != (len(self.active),) or not np.all(np.isfinite(point)) or np.any(abs(point)>1):
            raise ValueError('invalid conditional bound coordinates')
        p = self.base.decode(point[:len(self.base.active)])
        p['earth_removal'] = float((point[-1]+1)/2) if self.fit_earth_removal else 0.
        return p


def load_kernel(directory):
    """Build a hash-addressed local accelerator with ordinary verified C arithmetic."""
    source = Path(__file__).with_name('ilvis0_native.c')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    binary = directory/('native-'+digest+'.so')
    if not binary.exists():
        temporary = binary.with_suffix('.partial.so')
        subprocess.run(['cc', '-O2', '-std=c99', '-D_DEFAULT_SOURCE', '-fPIC', '-shared',
                        str(source), '-lm', '-o', str(temporary)], check=True, capture_output=True)
        temporary.replace(binary)
    library = ctypes.CDLL(str(binary))
    function = library.ilvis0_predict
    array = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    function.argtypes = [ctypes.c_size_t, array, array, array, ctypes.c_size_t,
                         array, array, array, array, array, ctypes.c_int,
                         ctypes.c_double, ctypes.c_double, ctypes.c_double, array]
    function.restype = ctypes.c_int
    return function, dict(source_sha256=digest, binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                         compiler=subprocess.check_output(['cc', '--version'], text=True).splitlines()[0],
                         flags=['-O2', '-std=c99', '-D_DEFAULT_SOURCE', '-fPIC', '-shared'])


def reference_step(state, theta, dv, dt, model, gravity, radius, removal):
    """Common conventional Earth-rate restoration; never candidate-specific restoration."""
    if not 0<=removal<=1:
        raise ValueError('Earth-removal fraction outside [0,1]')
    c = np.array([state['latitude_rad'], state['longitude_rad'], state['height_m']])
    r = state['attitude_body_to_ned']; v = state['velocity_ned_mps']
    rate = forward.coordinate_rates(model, c[0], c[2], v, radius)
    middle = c+rate*dt/2

    def local(rate):
        context = forward.coordinate_kinematics(model, middle[0], middle[2], rate, radius)
        earth, transport = context['earth_rate_ned_rads'], context['transport_rate_ned_rads']
        standard = np.array([math.cos(middle[0]), 0., -math.sin(middle[0])])*7.2921150e-5
        win = earth+transport-removal*standard
        mid_r = forward.exp(-win*dt/2)@r@forward.exp(theta/2)
        next_r = forward.exp(-win*dt)@r@forward.exp(theta)
        a = forward.skew(2*earth+transport)*dt/2
        next_v = np.linalg.solve(np.eye(3)+a, (np.eye(3)-a)@v+mid_r@dv+gravity*dt)
        return next_r, next_v
    _, estimate = local(rate)
    rate = forward.coordinate_rates(model, middle[0], middle[2], (v+estimate)/2, radius)
    r, v = local(rate); c += rate*dt
    return dict(latitude_rad=c[0], longitude_rad=c[1], height_m=c[2],
                velocity_ned_mps=v, attitude_body_to_ned=r)


class ConditionalProblem(estimator.MotionProblem):
    def __init__(self, *args, fit_earth_removal=True, kernel=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.bounds = ConditionalBounds(self.bounds.limits, fit_earth_removal=fit_earth_removal)
        self.kernel = kernel

    def predict(self, point, model):
        p = self.bounds.decode(point)
        coordinates = np.array([self.initial['latitude_rad'], self.initial['longitude_rad'], self.initial['height_m']])
        coordinates += forward.coordinate_rates(model, coordinates[0], coordinates[2], estimator.vec(p, 'position'), self.radius)
        velocity = self.initial['velocity_ned_mps']+estimator.vec(p, 'velocity')
        rotation = self.initial['attitude_body_to_ned']@forward.exp(estimator.vec(p, 'attitude'))
        theta = (self.theta-estimator.vec(p,'gyro_bias')*self.dt[:,None])/(1+estimator.vec(p,'gyro_gain'))
        dv = (self.dv-estimator.vec(p,'accel_bias')*self.dt[:,None])/(1+estimator.vec(p,'accel_gain'))
        times = self.gps_times+p['time_offset']; lever = estimator.vec(p,'lever')
        gravity = self.gravity+p['gravity_delta']
        if self.kernel is not None:
            out = np.empty_like(self.gps)
            code = self.kernel(len(self.dt), np.ascontiguousarray(theta), np.ascontiguousarray(dv),
                np.ascontiguousarray(self.dt), len(times), np.ascontiguousarray(times),
                np.ascontiguousarray(coordinates), np.ascontiguousarray(velocity),
                np.ascontiguousarray(rotation), np.ascontiguousarray(lever), MODELS.index(model),
                gravity, self.radius or 6371000., p['earth_removal'], out)
            if code or not np.all(np.isfinite(out)):
                raise ValueError('native prediction outside supported domain')
            return out
        state = dict(latitude_rad=coordinates[0],longitude_rad=coordinates[1],height_m=coordinates[2],
                     velocity_ned_mps=velocity,attitude_body_to_ned=rotation)
        out=[]; j=0; start=0.
        for k,end in enumerate(self.ends):
            while j<len(times) and times[j]<=end:
                f=float(np.clip((times[j]-start)/self.dt[k],0,1))
                obs=state if f==0 else reference_step(state,theta[k]*f,dv[k]*f,self.dt[k]*f,
                    model,np.array([0.,0.,gravity]),self.radius,p['earth_removal'])
                c=np.array([obs['latitude_rad'],obs['longitude_rad'],obs['height_m']])
                out.append(c+forward.coordinate_rates(model,c[0],c[2],obs['attitude_body_to_ned']@lever,self.radius)); j+=1
            if j==len(times): break
            state=reference_step(state,theta[k],dv[k],self.dt[k],model,np.array([0.,0.,gravity]),self.radius,p['earth_removal'])
            start=float(end)
        if j!=len(times):raise ValueError('receiver prediction outside native support')
        return np.array(out)


def fit_conditional(problem, model, *, ledger, task, maximum_evaluations=200, start=None):
    """Explicitly authorized exploratory fit; never pass assumed evidence to fit_observed."""
    charge = ledger.charge(task, maximum_evaluations)
    # Reuse the bounded numerical solver, not its software-control authorization.
    # Four evaluations are reserved for recorded-data diagnostics/counterfactuals.
    result = estimator.fit_control(problem, model, maximum_evaluations=maximum_evaluations-4, start=start)
    result.update(version=VERSION, start_charge=charge, inference_scope='conditional exploratory fit of recorded data',
        maximum_evaluations=maximum_evaluations,
        processing_independence_established=False, calibration_bounds_supported=False,
        receiver_covariance_calibrated=False, clock_independently_established=False,
        scientific_eligible=False, scientific_decision='abstain')
    return result
