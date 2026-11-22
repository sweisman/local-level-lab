# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propose an affine contrast using the state at the forecast cut."""

from .calibration_maximum_margin import PROPOSAL_SECONDS


def forecast_factors(operator, *, cut):
    """Return the history-to-state and state-to-forecast maps separately."""
    import numpy as np

    if not 0 < cut < operator.epoch_count:
        raise ValueError('cut must separate nonempty earlier and later windows')
    axes, states = operator.observation_dimension, operator.state_dimension
    history = np.empty((states, axes*cut))
    update = np.eye(states)
    for index in reversed(range(cut)):
        gain = operator._gain[index]
        history[:, axes*index:axes*(index+1)] = update @ gain
        update = update @ (operator._transition[index] - gain @ operator._observation[index])
    forecast = []
    update = np.eye(states)
    for index in range(cut, operator.epoch_count):
        forecast.append(operator._observation[index] @ update)
        update = operator._transition[index] @ update
    return history, np.vstack(forecast)


def propose_compact(operator, nominal, design, metric, lower, upper, smooth, *, cut, iterations):
    """Minimize the maximum coordinate error, with one link per filter state."""
    import warnings

    import numpy as np
    from scipy.optimize import OptimizeWarning, linprog
    from scipy.sparse import bmat, csr_matrix, eye

    history, projection = forecast_factors(operator, cut=cut)
    states, early = history.shape
    late = projection.shape[0]
    # Normalize the state rows so their magnitudes follow the earlier error.
    scale = np.sum(np.abs(history), axis=1)
    scale[scale == 0.] = 1.
    history /= scale[:, None]
    projection *= scale

    design = design * np.asarray(metric)[:, None]
    nominal = np.asarray(nominal, dtype=float)
    lower, upper = np.asarray(lower), np.asarray(upper)
    radius = (upper-lower)/2.
    center = lower+radius
    conditional_design = design[early:] - projection @ (history @ design[:early])
    conditional_offset = nominal[early:] - projection @ (history @ nominal[:early]) + conditional_design @ center
    drift = np.asarray(smooth, dtype=float)[early:]
    free_terms = len(center)+drift.shape[1]
    sample_count = early+late
    term_matrix = csr_matrix(np.column_stack((conditional_design*radius, drift)))
    equal = bmat([[term_matrix, None, -eye(late), csr_matrix(projection), csr_matrix((late, 1))],
                  [csr_matrix((states, free_terms)), csr_matrix(history), None, -eye(states), None]], format='csr')
    margin = csr_matrix(-np.ones((sample_count, 1)))
    limits = bmat([[csr_matrix((sample_count, free_terms)), eye(sample_count),
                    csr_matrix((sample_count, states)), margin],
                   [None, -eye(sample_count), None, margin]], format='csr')
    objective = np.zeros(free_terms+sample_count+states+1)
    objective[-1] = 1.
    bounds = [(-1., 1.) if width else (0., 0.) for width in radius]
    bounds += [(None, None)]*(drift.shape[1]+sample_count+states)+[(0., None)]
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Unrecognized options detected:.*threads', category=OptimizeWarning)
        fit = linprog(objective, A_ub=limits, b_ub=np.zeros(2*sample_count), A_eq=equal,
                      b_eq=np.r_[-conditional_offset, np.zeros(states)], bounds=bounds, method='highs-ipm',
                      options=dict(maxiter=iterations, time_limit=PROPOSAL_SECONDS, threads=1,
                                   ipm_optimality_tolerance=1e-10, primal_feasibility_tolerance=1e-9,
                                   dual_feasibility_tolerance=1e-9))
    result = dict(status=int(fit.status), iterations=int(fit.nit), crossover_iterations=int(fit.crossover_nit),
                  objective=None, point=None, smooth=None, earlier_error=None, later_taps=None,
                  equality_nonzeros=int(equal.nnz), state_rows=states,
                  dense_conditioning_entries=early*late, compact_conditioning_entries=states*(early+late))
    if fit.success:
        result.update(point=np.clip(center+radius*fit.x[:len(center)], lower, upper).tolist(),
                      smooth=fit.x[len(center):free_terms].tolist(),
                      earlier_error=fit.x[free_terms:free_terms+early].tolist(),
                      later_taps=fit.eqlin.marginals[:late].tolist(), objective=float(fit.fun))
    return result
