# SPDX-License-Identifier: AGPL-3.0-or-later
"""Search and check a continuous bounded path in the saved carrier geometry."""

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import Bounds, minimize

from .carrier_score_cadence import project_cadence


ITERATIONS = 160


def acceleration_quadrature(knots):
    """Square-root integration weights for a natural spline's linear acceleration."""
    knots = np.asarray(knots)
    width = np.diff(knots)
    if (knots.ndim != 1 or len(knots) < 2 or not np.isfinite(knots).all()
            or not (width > 0).all()):
        raise ValueError('strictly ordered, finite spline knots required')
    middle = knots[:-1]+width/2
    offset = width/(2*np.sqrt(3))
    return np.column_stack((middle-offset, middle+offset)).ravel(), np.sqrt(np.repeat(width/2, 2))


def ground_projection(support, values, station):
    return np.asarray(project_cadence(support, values, sorted(station),
                      interval_satellites=station)['projected_weights'])


def geometry_dilation(visible_cap, invisible_cap, buffer):
    """Map the tightened range domain to one that contains the relaxed domain."""
    if not np.isfinite([visible_cap, invisible_cap, buffer]).all() or not 0 <= buffer < min(visible_cap, invisible_cap):
        raise ValueError('the geometric remainder must fit within both range caps')
    scale = max((cap+buffer)/(cap-buffer) for cap in (visible_cap, invisible_cap))
    return float(np.nextafter(scale, np.inf))


def _constraint_maps(*, knots, times, anchor_indices, score_times, taps, operator, support,
                     station, caps, geometric_buffer_m, gap):
    knots, times = map(np.asarray, (knots, times))
    anchors = times[anchor_indices]
    indices = np.searchsorted(knots, anchors)
    if np.any(indices >= len(knots)) or not np.array_equal(knots[indices], anchors):
        raise ValueError('spline knots must contain the original anchors')
    spline = CubicSpline(knots, np.eye(len(knots)), bc_type='natural')
    quadrature, mass = acceleration_quadrature(knots)
    range_map = operator@np.kron(spline(times), np.eye(3))
    covered = ground_projection(support, range_map, station)
    acceleration = np.kron(spline(quadrature, 2)*mass[:, None], np.eye(3))
    range_scales = np.sqrt(operator.shape[0])*np.array([caps['visible_range_rms_m']-geometric_buffer_m,
                                                       caps['invisible_range_rms_m']-geometric_buffer_m])
    if np.any(range_scales <= 0) or caps['acceleration_rms_mps2'] <= 0 or gap <= 0:
        raise ValueError('positive range, acceleration and gap allowances required')
    matrices = (acceleration/(np.sqrt(knots[-1]-knots[0])*caps['acceleration_rms_mps2']),
                covered/range_scales[0], (range_map-covered)/range_scales[1])
    objective = (spline(score_times).T@taps).ravel()/gap
    anchor_components = (3*indices[:, None]+np.arange(3)).ravel()
    return matrices, objective, anchor_components


def search(**problem):
    """Use scaled convex constraints, then leave feasibility to a separate check."""
    matrices, objective, anchor_components = _constraint_maps(**problem)
    grams = np.array([matrix.T@matrix for matrix in matrices])
    limits = np.full(len(objective), np.inf)
    limits[anchor_components] = problem['caps']['anchor_axis_m']
    result = minimize(lambda x: -float(objective@x), np.zeros_like(objective), jac=lambda _: -objective,
                       bounds=Bounds(-limits, limits), method='SLSQP',
                       constraints=[dict(type='ineq', fun=lambda x: 1-(grams@x)@x,
                                         jac=lambda x: -2*(grams@x))],
                       options=dict(maxiter=ITERATIONS, ftol=1e-11))
    return result.x.reshape(-1, 3), result


def bracket(*, coordinate_caps, max_iterations=120, multipliers=None, **problem):
    """Bracket the maximum score change for the specified spline and caps."""
    from .quadratic_support_bound import solve_support

    matrices, objective, anchor_components = _constraint_maps(**problem)
    axes = np.zeros((len(anchor_components), len(objective)))
    axes[np.arange(len(anchor_components)), anchor_components] = 1/problem['caps']['anchor_axis_m']
    score = solve_support((*matrices, *(row[None, :] for row in axes)), objective,
                          coordinate_caps, max_iterations=max_iterations, multipliers=multipliers)
    score['positions'] = score.pop('point').reshape(-1, 3)
    return score


def verify(positions, *, knots, times, anchor_indices, score_times, taps, operator, support, station,
           caps, geometric_buffer_m, gap):
    """Measure the direct score and constraints from the finished spline."""
    spline = CubicSpline(knots, positions, bc_type='natural')
    quadrature, mass = acceleration_quadrature(knots)
    duration = knots[-1]-knots[0]
    aircraft = operator@spline(times).ravel()
    covered = ground_projection(support, aircraft, station)
    scale = np.sqrt(len(aircraft))
    values = dict(anchor_max_abs_m=float(np.max(abs(spline(np.asarray(times)[anchor_indices])))),
                  acceleration_rms_mps2=float(np.linalg.norm(mass[:, None]*spline(quadrature, 2))/np.sqrt(duration)),
                  range_rms_in_ground_m=float(np.linalg.norm(covered)/scale),
                  range_rms_outside_ground_m=float(np.linalg.norm(aircraft-covered)/scale),
                  score_shift=float(np.sum(taps*spline(score_times))))
    values['score_fraction'] = values['score_shift']/gap
    values['within_linear_and_geometry_caps'] = all(
        actual <= maximum for actual, maximum in (
            (values['anchor_max_abs_m'], caps['anchor_axis_m']),
            (values['acceleration_rms_mps2'], caps['acceleration_rms_mps2']),
            (values['range_rms_in_ground_m']+geometric_buffer_m, caps['visible_range_rms_m']),
            (values['range_rms_outside_ground_m']+geometric_buffer_m, caps['invisible_range_rms_m']),
        ))
    return values
