# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shape-first, instrument-informed conditional refinement of native IMU/GPS fits.

Sensitivity limits are hypotheses, not per-unit calibration or confidence bounds.
Constant gyro bias, stochastic noise and time-varying drift are distinct quantities.
The historical broad stress-test sources and evidence-gated estimator stay unchanged.
"""
import ctypes
import hashlib
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import least_squares

from . import ilvis0_estimator as estimator, ilvis0_exploratory as explore

VERSION = 'ilvis0-shape-first-tangent-v1'
BIAS_CASES_DPH = (.1, 1.)
PARAMETERS = estimator.PARAMETERS + ('earth_removal',)


def instrument_limits(bias_dph):
    """Change only constant gyro offset; leave other unknowns explicitly generous.

    .1 is an optimistic residual-calibration sensitivity, inspired by the POS510
    system drift figure. 1 is a wider sensitivity informed by LN200 family bias
    repeatability. Neither is a verified hard bound on these legacy raw streams.
    Raw-family specifications differ by variant; these cases do not span all of them.
    """
    if bias_dph not in BIAS_CASES_DPH:
        raise ValueError('preregistered .1/1 degree/hour sensitivity cases required')
    limits = dict(explore.LIMITS)
    for axis in estimator.AXES:
        limits['gyro_bias_'+axis] = math.radians(bias_dph)/3600
    return limits


def load_tangent(directory):
    source = Path(__file__).with_name('ilvis0_tangent.cpp')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    binary = directory/('tangent-'+digest+'.so')
    flags = ['-O2', '-std=c++17', '-fPIC', '-shared']
    if not binary.exists():
        temporary = binary.with_suffix('.partial.so')
        subprocess.run(['c++', *flags, str(source), '-o', str(temporary)],
                       check=True, capture_output=True)
        temporary.replace(binary)
    library = ctypes.CDLL(str(binary)); function = library.ilvis0_tangent
    array = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    function.argtypes = [ctypes.c_size_t, array, array, array, ctypes.c_size_t,
        array, array, array, array, array, array, ctypes.c_int, ctypes.c_int,
        ctypes.c_double, ctypes.c_double, array, array, ctypes.POINTER(ctypes.c_int)]
    function.restype = ctypes.c_int
    return function, dict(source_sha256=digest,
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        compiler=subprocess.check_output(['c++', '--version'], text=True).splitlines()[0], flags=flags)


class TangentProblem(explore.ConditionalProblem):
    def __init__(self, *args, tangent_kernel, **kwargs):
        super().__init__(*args, **kwargs)
        self.tangent_kernel = tangent_kernel

    def prediction_tangent(self, point, model):
        self.bounds.decode(point)
        u = dict(zip(self.bounds.active, point))
        expanded = np.array([u.get(name, 0.) for name in PARAMETERS])
        limits = np.array([self.bounds.limits.get(name, 0.) for name in PARAMETERS])
        c = np.array([self.initial['latitude_rad'], self.initial['longitude_rad'], self.initial['height_m']])
        out = np.empty_like(self.gps); jac = np.empty((out.size, 27)); boundaries = ctypes.c_int()
        code = self.tangent_kernel(len(self.dt), np.ascontiguousarray(self.theta),
            np.ascontiguousarray(self.dv), np.ascontiguousarray(self.dt), len(self.gps_times),
            np.ascontiguousarray(self.gps_times), c,
            np.ascontiguousarray(self.initial['velocity_ned_mps']),
            np.ascontiguousarray(self.initial['attitude_body_to_ned']), limits, expanded,
            explore.MODELS.index(model), int(self.bounds.fit_earth_removal),
            self.gravity, self.radius or 6371000., out, jac, ctypes.byref(boundaries))
        if code or not np.all(np.isfinite(out)) or not np.all(np.isfinite(jac)):
            raise ValueError('tangent prediction outside supported native domain')
        indices = [PARAMETERS.index(name) for name in self.bounds.active]
        return out, jac[:, indices], boundaries.value

    def residual_tangent(self, point, model):
        out, jac, boundaries = self.prediction_tangent(point, model)
        return self.whiten(out-self.gps), solve_triangular(self.cholesky, jac, lower=True), boundaries


def fit_shape_candidate(problem, model, *, start=None, maximum_evaluations=200):
    """Exact forward derivatives and column scaling, with counted native sweeps.

    One sweep returns both values and derivatives, including calibration, initial
    rotation, lever arm, Earth correction and fractional-epoch latency. The limited
    initialization stage releases all nuisance directions in the final profile.
    Budget includes a fresh final tangent and reserves two value-only diagnostics.
    """
    if not 4 <= maximum_evaluations <= 200:
        raise ValueError('finite evaluation allowance in [4,200] required')
    point = np.zeros(len(problem.bounds.active)) if start is None else np.array(start, float)
    problem.bounds.decode(point)
    calls = 0; cache = None; best = None; limit = maximum_evaluations-3

    def evaluate(u, fresh=False):
        nonlocal calls, cache, best
        if not fresh and cache is not None and np.array_equal(u, cache[0]):
            return cache[1:]
        if calls >= limit:
            raise estimator.EvaluationLimit('native tangent evaluation allowance exhausted')
        calls += 1
        residual, jac, boundaries = problem.residual_tangent(u, model)
        cache = (u.copy(), residual, jac, boundaries)
        cost = float(residual@residual)
        if best is None or cost < best[0]:
            best = (cost, u.copy())
        return residual, jac, boundaries

    staged = [i for i, name in enumerate(problem.bounds.active)
              if name.startswith(('attitude_', 'velocity_', 'position_', 'accel_gain_'))]
    stage_message = 'no staged parameters'; stage_calls = 0
    if staged and len(point) > len(staged) and maximum_evaluations >= 40:
        initial = point.copy(); end_stage = calls+min(25, maximum_evaluations//5)
        def expand(x):
            full = initial.copy(); full[staged] = x; return full
        def stage_fun(x):
            if calls >= end_stage:
                raise estimator.EvaluationLimit('initialization stage complete')
            return evaluate(expand(x))[0]
        try:
            sol = least_squares(stage_fun, initial[staged],
                jac=lambda x: evaluate(expand(x))[1][:, staged], bounds=(-1., 1.),
                x_scale='jac', ftol=None, xtol=1e-11, gtol=1e-8,
                max_nfev=min(25, maximum_evaluations//5))
            stage_message = str(sol.message)
        except estimator.EvaluationLimit as error:
            stage_message = str(error)
        point = best[1].copy(); stage_calls = calls
    success = False; message = 'not started'
    try:
        sol = least_squares(lambda u: evaluate(u)[0], point,
            jac=lambda u: evaluate(u)[1], bounds=(-1., 1.), x_scale='jac',
            ftol=None, xtol=1e-11, gtol=1e-8, max_nfev=limit-calls)
        success = bool(sol.success); message = str(sol.message)
    except estimator.EvaluationLimit as error:
        message = str(error)
    if best is None:
        raise ValueError('no finite candidate evaluation')
    cost, point = best
    # Reserve was independent of optimizer termination; always check a fresh AD sweep.
    limit = maximum_evaluations-2
    residual, jac, boundaries = evaluate(point, fresh=True)
    gradient = jac.T@residual; projected = gradient.copy()
    projected[(point <= -1+1e-6)&(gradient > 0)] = 0
    projected[(point >= 1-1e-6)&(gradient < 0)] = 0
    scaling = np.maximum(np.linalg.norm(jac, axis=0), 1.)*max(np.linalg.norm(residual), 1.)
    stationarity = float(np.max(abs(projected)/scaling)) if len(point) else 0.
    singular = np.linalg.svd(jac, compute_uv=False)
    return dict(version=VERSION, model=model, parameters=problem.bounds.decode(point),
        normalized_parameters=point.tolist(), active_parameters=list(problem.bounds.active),
        residual_sum_squares=float(residual@residual), evaluations=calls,
        maximum_evaluations=maximum_evaluations, derivative_method='forward automatic differentiation, 27 tangent lanes',
        initialization_evaluations=stage_calls, initialization_message=stage_message,
        solver_reported_success=success, converged=success and stationarity <= 1e-4,
        exact_projected_gradient_relative=stationarity, stationarity_tolerance=1e-4,
        singular_values=singular.tolist(), message=message,
        gps_epochs_at_packet_boundaries=boundaries,
        latency_derivative_convention='left interval at a packet boundary; adjacent measured rates may differ',
        active_bounds=[name for name, u in zip(problem.bounds.active, point) if abs(u) >= .999],
        constant_bias_is_measured_drift=False, scientific_eligible=False,
        scientific_decision='abstain', calibration_bounds_supported=False,
        processing_independence_established=False, receiver_covariance_calibrated=False,
        clock_independently_established=False)


def hierarchical_profile(cases):
    """Shape preference must survive every declared case before rotation is reported.

    A signed profile difference is a CONDITIONAL numerical preference, not a
    calibrated statistical detection. Scientific decisions always abstain here.
    Rotation diagnostics are withheld for flat, mixed, tied or unresolved shape.
    Both globe members are profiled internally to avoid presuming rotation at stage1.
    """
    from .ilvis0_refinement import globe_disc_profile
    if not cases or len({c['case_id'] for c in cases}) != len(cases):
        raise ValueError('nonempty unique matched assumption cases required')
    profiles = [dict(case_id=c['case_id'], **globe_disc_profile(c['fits'])) for c in cases]
    contrasts = [r['conditional_disc_minus_globe_cost'] for r in profiles]
    if any(x is None for x in contrasts):
        preference = 'unresolved'
    elif all(x > 0 for x in contrasts):
        preference = 'globe'
    elif all(x < 0 for x in contrasts):
        preference = 'flat'
    else:
        preference = 'ambiguous'
    rotation = None
    if preference == 'globe':
        rotation = []
        for case in cases:
            rows = {f['model']: f for f in case['fits']}
            rotation.append(dict(case_id=case['case_id'],
                conditional_still_minus_rotating_cost=rows['sphere_still']['residual_sum_squares']-
                    rows['sphere_rotating']['residual_sum_squares']))
    return dict(version=VERSION, comparison_order=['globe_family_vs_flat', 'rotating_vs_still_given_globe'],
        shape_profiles=profiles, conditional_shape_preference=preference,
        rotation_diagnostics=rotation,
        rotation_withheld_reason=None if rotation is not None else 'shape is not consistently resolved in favor of globe',
        scientific_shape_decision='abstain', scientific_rotation_decision='abstain',
        calibrated=False, scope='local conditional sensitivity results, not global minima or statistical detection')
