# SPDX-License-Identifier: AGPL-3.0-or-later
"""Opt-in native training problems for the matched field and offset study."""

import math

from .ilvis0_estimator import AXES, Bounds
from .ilvis0_exploratory import LIMITS, MODELS
from .ilvis0_receiver_force import DISC_WITH_FIELD
from .ilvis0_shape import TangentProblem
from .ilvis0_training_forecast import initialize_training


MATCHED_MODELS = (*MODELS, DISC_WITH_FIELD)
OFFSET_CAPS_DPH = (1., 3., 10., 20.)


def matched_limits(gyro_offset_dph):
    if gyro_offset_dph not in OFFSET_CAPS_DPH:
        raise ValueError('declared matched gyro-offset cap required')
    limits = dict(LIMITS)
    for axis in AXES:
        limits[f'gyro_bias_{axis}'] = math.radians(gyro_offset_dph) / 3600.
    return limits


class MatchedTrainingProblem(TangentProblem):
    """Bind one diagnostic candidate to its training initialization."""

    def __init__(self, *args, matched_model, **kwargs):
        if matched_model not in MATCHED_MODELS:
            raise ValueError('declared matched candidate required')
        self.matched_model = matched_model
        super().__init__(*args, **kwargs)

    def kernel_model(self, model):
        if model != self.matched_model:
            raise ValueError('candidate differs from matched training model')
        return MATCHED_MODELS.index(model)

    def metric_model(self, model):
        return 'flat_still' if model == DISC_WITH_FIELD else model


def matched_training_problem(times, gps, *, theta, dv, dt, covariance, model,
                             limits, profile, clock, maximum_interval_s,
                             kernel, tangent_kernel):
    if model not in MATCHED_MODELS or not callable(kernel) or not callable(tangent_kernel):
        raise ValueError('declared matched model and both native kernels required')
    metric = 'flat_still' if model == DISC_WITH_FIELD else model
    initial, gravity = initialize_training(
        times, gps, theta=theta, dv=dv, dt=dt, model=metric,
        maximum_interval_s=maximum_interval_s, clock=clock)
    return MatchedTrainingProblem(
        theta, dv, dt, times, gps, covariance, initial, Bounds(limits),
        matched_model=model, kernel=kernel, tangent_kernel=tangent_kernel,
        fit_earth_removal=profile, clock_hypothesis=clock,
        processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=maximum_interval_s, gravity_mps2=gravity,
        disc_radius_m=6371000.)
