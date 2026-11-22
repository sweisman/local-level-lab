# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check a whole later affine path against the earlier calibration region."""

import numpy as np
from scipy.optimize import lsq_linear
from scipy.stats import chi2

from .ilvis0_bounded_prediction import Region
from .state_space_covariance import LinearInnovations


def _split(operator, training_epochs):
    if (not isinstance(operator, LinearInnovations) or type(training_epochs) is not int
            or not 1 <= training_epochs < operator.epoch_count):
        raise ValueError('fixed covariance operator and nonempty chronological split required')
    return operator.observation_dimension * training_epochs


def innovation_remainder(operator, coordinate_bounds, *, training_epochs):
    """Carry supported coordinate-wise remainder bounds through whitening."""
    cut = _split(operator, training_epochs)
    coordinates = np.asarray(coordinate_bounds, float)
    d = operator.observation_dimension
    if (coordinates.shape != (operator.epoch_count * d,)
            or not np.isfinite(coordinates).all() or np.any(coordinates < 0.0)):
        raise ValueError('finite nonnegative remainder bound for each coordinate required')
    state = np.zeros(operator.state_dimension)
    whitened = np.empty((operator.epoch_count, d))
    # Use an absolute-value state envelope. Only the previous envelope is
    # carried, so earlier remainder is included after the cut without forming
    # a dense whitening matrix.
    slack = 8.0 * np.finfo(float).eps * max(d, len(state))
    for index, row in enumerate(coordinates.reshape(-1, d)):
        transition = operator._transition[index]
        observation = operator._observation[index]
        gain = operator._gain[index]
        lower = operator._lower[index]
        innovation = row + abs(observation) @ state
        output = whitened[index]
        for axis in range(d):
            output[axis] = ((innovation[axis] + abs(lower[axis, :axis]) @ output[:axis])
                            / lower[axis, axis]) * (1.0 + slack)
        update = abs(transition - gain @ observation)
        update += slack * (abs(transition) + abs(gain) @ abs(observation))
        state = (update @ state + abs(gain) @ row) * (1.0 + slack)
    earlier = float(np.linalg.norm(whitened.ravel()[:cut])) * (1.0 + slack)
    later = float(np.linalg.norm(whitened.ravel()[cut:])) * (1.0 + slack)
    if not np.isfinite([earlier, later]).all():
        raise ValueError('unrepresentable whitened remainder allowance')
    return earlier, later


def assess_recording(operator, residual, design, bounds, *, training_epochs, scale,
                     coordinate_remainder_bounds, alpha_training, alpha_future,
                     design_is_fixed=False, rank_tolerance=1e-10):
    """Use one fixed error operator for the earlier region and later path.

    Coordinate remainder bounds must hold across the supplied calibration box
    before whitening. Missing bounds lead to abstention.
    """
    cut = _split(operator, training_epochs)
    n = operator.observation_dimension * operator.epoch_count
    path = np.asarray(residual, float)
    design = np.asarray(design, float)
    if (path.shape != (n,) or design.ndim != 2 or design.shape[0] != n
            or not 1 <= design.shape[1] <= 27):
        raise ValueError('complete path and every parameter column required')
    earlier_remainder, later_remainder = (None, None)
    if coordinate_remainder_bounds is not None:
        earlier_remainder, later_remainder = innovation_remainder(
            operator, coordinate_remainder_bounds, training_epochs=training_epochs)
    innovations = operator.whiten(np.column_stack((path, design)))
    region = Region(innovations[:cut, 0], innovations[:cut, 1:], bounds, scale=scale,
                    covariance_id=operator.configuration, remainder_radius=earlier_remainder,
                    alpha=alpha_training, design_is_fixed=design_is_fixed,
                    rank_tolerance=rank_tolerance)
    return assess(region, innovations[cut:, 0], innovations[cut:, 1:], alpha=alpha_future,
                  future_innovation_remainder_radius=later_remainder)


def _compact(design, values):
    # Orthogonal reduction preserves squared costs and bounds the size of each
    # trial least-squares solve independently of trajectory length.
    reduced = np.linalg.qr(np.column_stack((design, values)), mode='r')
    return reduced[:, :-1], reduced[:, -1]


def _box_minimum(design, values, lower, upper):
    point = lower.copy()
    free = lower < upper
    if free.any():
        target = values - design[:, ~free] @ lower[~free]
        fit = lsq_linear(design[:, free], target, bounds=(lower[free], upper[free]),
                         method='bvls', tol=1e-12, max_iter=100)
        point[free] = np.clip(fit.x, lower[free], upper[free])
    if not np.isfinite(point).all():
        raise ValueError('unrepresentable calibration trial')
    return point


def _cost_support(design, values, point, lower, upper):
    residual = design @ point - values
    cost = float(residual @ residual)
    gradient = 2.0 * (residual @ design)
    box_offset = np.minimum(gradient * (lower - point), gradient * (upper - point))
    magnitude = abs(values) + abs(design) @ np.maximum(abs(lower), abs(upper))
    # Allow for roundoff in row reductions, scalar products and cancellation.
    slack = (64.0 * np.finfo(float).eps * max(design.shape)
             * float(magnitude @ magnitude))
    return cost, gradient, float(box_offset.sum()), slack


def assess(region, future_residual, future_design, *, alpha,
           future_innovation_remainder_radius):
    """Compare an earlier confidence region with a whole later-path ball.

    Supply all nuisance columns in the same order and units as the earlier
    region. The future arrays must be innovations from the same fixed joint
    covariance law. Its stated scale and remainder allowances must cover the
    training-conditioned future, including any earlier remainder transmitted
    by the conditioning operation.
    """
    if not isinstance(region, Region):
        raise ValueError('earlier calibration region required')
    values = np.asarray(future_residual, float)
    design = np.asarray(future_design, float)
    if (values.ndim != 1 or not len(values)
            or design.shape != (len(values), region.parameter_count)
            or not np.isfinite(values).all() or not np.isfinite(design).all()):
        raise ValueError('finite future innovations and a column for every parameter required')
    failure_bound = region.scale.failure_probability + region.alpha + alpha
    if not np.isfinite(failure_bound) or not 0.0 < alpha or failure_bound >= 1.0:
        raise ValueError('total failure allowance must lie strictly between zero and one')
    remainder = future_innovation_remainder_radius
    result = dict(status='unsupported', scientific_decision='abstain', witness=None,
                  covariance_id=region.covariance_id, scale_source_id=region.scale.source_id,
                  future_rows=len(values), reference_failure_probability_bound=failure_bound)
    if remainder is not None and (not np.isfinite(remainder) or remainder < 0.0):
        raise ValueError('finite nonnegative innovation remainder radius required')
    if not region.supported or remainder is None:
        return result

    lower, upper = region.bounds.T
    earlier_design = region.singular[:, None] * region.basis.T
    earlier_values = earlier_design @ region.center
    earlier_limit = region.radius ** 2
    future_limit = (region.scale.upper * np.sqrt(chi2.isf(alpha, len(values))) + remainder) ** 2
    if not np.isfinite([earlier_limit, future_limit]).all():
        raise ValueError('unrepresentable joint path limits')
    compact_design, compact_values = _compact(design, values)
    earlier_point = _box_minimum(earlier_design, earlier_values, lower, upper)
    future_point = _box_minimum(compact_design, compact_values, lower, upper)
    result.update(status='inconclusive', earlier_limit=earlier_limit,
                  future_limit=future_limit, future_cost_lower_bound=0.0)

    def verify(point, multiplier):
        ec, eg, eo, es = _cost_support(earlier_design, earlier_values, point, lower, upper)
        fc, fg, _, fs = _cost_support(design, values, point, lower, upper)
        if ec + eo - es > earlier_limit:
            result['status'] = 'incompatible_earlier'
            return ec
        gradient = fg + multiplier * eg
        offset = np.minimum(gradient * (lower - point), gradient * (upper - point)).sum()
        penalty = multiplier * (ec - earlier_limit)
        slack = fs + multiplier * (es + 16.0 * np.finfo(float).eps * earlier_limit)
        lower_bound = fc + penalty + offset - slack
        if not np.isfinite([ec, fc, lower_bound]).all():
            raise ValueError('unrepresentable joint path cost bound')
        result['future_cost_lower_bound'] = max(result['future_cost_lower_bound'], lower_bound)
        if ec <= earlier_limit and fc <= future_limit:
            result.update(status='compatible_witness', witness=point.tolist(),
                          witness_earlier_cost=ec, witness_future_cost=fc)
        elif result['future_cost_lower_bound'] > future_limit:
            result['status'] = 'incompatible'
        return ec

    for point in (earlier_point, future_point):
        verify(point, 0.0)
        if result['status'] != 'inconclusive':
            return result
    if not region.rank:
        return result

    # Trial multipliers seek a tight lower bound. Any nonnegative multiplier
    # works for the bound, regardless of the optimizer's stopping status.
    earlier_norm = float(np.linalg.norm(earlier_design))
    future_norm = float(np.linalg.norm(compact_design))
    if future_norm == 0.0:
        return result
    log_weight = np.clip(2.0 * (np.log2(future_norm) - np.log2(earlier_norm)), -256., 256.)
    low, high = log_weight - 32.0, log_weight + 32.0
    for _ in range(32):
        middle = (low + high) / 2.0
        multiplier = 2.0 ** middle
        weight = np.sqrt(multiplier)
        point = _box_minimum(np.vstack((compact_design, weight * earlier_design)),
                             np.concatenate((compact_values, weight * earlier_values)),
                             lower, upper)
        earlier_cost = verify(point, multiplier)
        if result['status'] != 'inconclusive':
            break
        if earlier_cost > earlier_limit:
            low = middle
        else:
            high = middle
    return result
