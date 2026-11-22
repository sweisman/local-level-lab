# SPDX-License-Identifier: AGPL-3.0-or-later
"""Profile a common accelerometer calibration with free attitude at each epoch."""

import numpy as np
from scipy.linalg import solve_triangular

from .ilvis0_receiver_force import MATCHED_MODELS
from .ilvis0_scalar_nonlinear import Problem, fit


class _WeightedForceProblem:
    def __init__(self, problem, covariance):
        self.problem = problem
        self.limits = problem.limits
        self.cholesky = np.linalg.cholesky(covariance)

    def residual(self, point):
        return solve_triangular(self.cholesky, self.problem.residual(point), lower=True)

    def jacobian(self, point):
        return solve_triangular(self.cholesky, self.problem.jacobian(point), lower=True)


def fit_gyro_free(body_specific_force, target_indices, receiver_assessment, *, model,
                 limits, accelerometer_covariance_mps4, start, maximum_evaluations):
    """Fit one declared candidate on the receiver-selected force history.

    The caller supplies accelerometer summaries aligned to the supported
    target indices. The fit uses the candidate's block of the shared receiver
    covariance plus a supplied independent accelerometer covariance. It keeps
    both fixed at their declared linearization for the entire fit. The scalar
    magnitude objective profiles unrestricted direction alignment, leaving the
    rotation around each force vector free. It makes no model decision.
    """
    indices = list(target_indices)
    if (tuple(receiver_assessment['model_order']) != MATCHED_MODELS or model not in MATCHED_MODELS
            or receiver_assessment['gyro_observations_used'] is not False
            or receiver_assessment['fused_navigation_used'] is not False
            or not indices or indices != receiver_assessment['supported_target_indices']
            or any(type(index) is not int or index < 0 for index in indices)
            or any(right <= left for left, right in zip(indices, indices[1:]))):
        raise ValueError('matched receiver-selected target indices required')
    count = len(indices)
    joint = np.asarray(receiver_assessment['joint_covariance_mps4'], float)
    accelerometer = np.asarray(accelerometer_covariance_mps4, float)
    if (joint.shape != (len(MATCHED_MODELS)*count,)*2
            or accelerometer.shape != (count, count)
            or any(not np.isfinite(value).all() or not np.allclose(
                value, value.T, rtol=1e-12, atol=0.) for value in (joint, accelerometer))):
        raise ValueError('finite symmetric receiver and accelerometer covariances required')
    if np.linalg.eigvalsh(accelerometer)[0] <= 0.:
        raise ValueError('positive definite declared accelerometer covariance required')
    first = MATCHED_MODELS.index(model) * count
    block = slice(first, first + count)
    problem = Problem(
        body_specific_force, receiver_assessment['required_force_ned_mps2'][model],
        [limits[f'accel_gain_{axis}'] for axis in 'xyz'] +
        [limits[f'accel_bias_{axis}'] for axis in 'xyz'] + [limits['gravity_delta']])
    if len(problem.body) != count:
        raise ValueError('force histories must cover every receiver-selected target')
    try:
        weighted = _WeightedForceProblem(problem, joint[block, block] + accelerometer)
    except np.linalg.LinAlgError as error:
        raise ValueError('positive definite total force covariance required') from error
    result = fit(weighted, start, max_evaluations=maximum_evaluations)
    residual = problem.residual(result['point'])
    result.update(model=model, supported_target_indices=indices,
                  whitened_force_residual=result['residual_mps2'],
                  residual_mps2=residual.tolist(),
                  rms_mps2=float(np.linalg.norm(residual) / np.sqrt(count)),
                  force_covariance_log_determinant=float(
                      2. * np.log(np.diag(weighted.cholesky)).sum()),
                  endpoint_reporting_evaluations=1,
                  shared_calibration_over_all_targets=True,
                  attitude_identified=False, motion_constraints_imposed=False,
                  force_covariance_calibrated=False)
    return result
