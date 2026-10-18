# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh verification of saved fixed-time endpoints, without optimization."""
from types import SimpleNamespace

import numpy as np

from .ilvis0_boundary_adapter import displacement_metrics
from .ilvis0_fixed_time_profile import FixedTimeProblem
from .ilvis0_solver_position import verify_stability


def verify_endpoint(ledger, identity, native, model, bounds, saved_full_point,
                    anchor_normalized, physical_step):
    """At most three diagnostic tangents; retain the full timing derivative."""
    def charged(u, chosen_model):
        return ledger.call(identity, 'diagnostic', 'tangent', native, u, chosen_model)

    view = FixedTimeProblem(SimpleNamespace(bounds=bounds, residual_tangent=charged),
                            anchor_normalized)
    point = np.asarray(saved_full_point, float)
    reduced = view.reduce(point)
    residual, jacobian, edges = charged(point, model)
    residual, jacobian = np.asarray(residual, float), np.asarray(jacobian, float)
    if (residual.ndim != 1 or not len(residual)
            or jacobian.shape != (len(residual), len(point))
            or not np.all(np.isfinite(residual)) or not np.all(np.isfinite(jacobian))):
        raise ValueError('finite full native residual and tangent required')
    repeated, repeated_jacobian, _ = charged(point, model)
    if not np.array_equal(jacobian, repeated_jacobian):
        raise ValueError('same-point native tangent is not repeatable')
    repeat = displacement_metrics(residual, repeated, physical_step)
    result = dict(conditional_verified=False, free_time_converged=False,
                  repeat=repeat, full_timing_gradient=float(jacobian[:, view.index] @ residual),
                  center_native=(residual, jacobian, edges))
    if not repeat['passed']:
        return result
    stability = verify_stability(reduced, residual, jacobian[:, view.keep],
        lambda u, **kwargs: view.residual_tangent(u, model), physical_step)
    result.update(conditional_verified=bool(stability['passed']), stability=stability)
    return result
