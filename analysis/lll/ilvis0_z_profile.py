# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze nuisance coordinates without modifying the underlying fitter or measurements."""
import numpy as np


class FixedBounds:
    def __init__(self, original, fixed):
        self.original = original
        if not fixed or any(n not in original.active for n in fixed):
            raise ValueError('fixed coordinates must name active parameters')
        if any(not np.isfinite(v) or abs(v)>1 for v in fixed.values()):
            raise ValueError('invalid fixed normalized coordinate')
        self.fixed = dict(fixed)
        self.active = tuple(n for n in original.active if n not in fixed)
        self.indices = [original.active.index(n) for n in self.active]
        self.limits = dict(original.limits)

    def expand(self, point):
        point = np.asarray(point, float)
        if point.shape != (len(self.active),) or not np.all(np.isfinite(point)) or np.any(abs(point)>1):
            raise ValueError('invalid free coordinates')
        full = np.array([self.fixed.get(n, 0.) for n in self.original.active])
        full[self.indices] = point
        self.original.decode(full)
        return full

    def decode(self, point):
        return self.original.decode(self.expand(point))


class FixedProblem:
    def __init__(self, original, fixed):
        self.original = original
        self.bounds = FixedBounds(original.bounds, fixed)
        self.last = None

    def expand(self, point):
        return self.bounds.expand(point)

    def residual_tangent(self, point, model):
        full = self.expand(point)
        residual, jacobian, boundaries = self.original.residual_tangent(full, model)
        self.last = (np.array(point, float), model, np.array(residual), np.array(jacobian))
        return residual, jacobian[:, self.bounds.indices], boundaries

    def diagnostics(self, point, model):
        if self.last is None or self.last[1]!=model or not np.array_equal(self.last[0], point):
            raise ValueError('diagnostics require the saved final tangent at fitted coordinates')
        point, _, residual, full_jac = self.last
        jac = full_jac[:, self.bounds.indices]
        full_gradient = full_jac.T@residual
        gradient = jac.T@residual
        projected = gradient.copy()
        projected[(point <= -1+1e-6)&(gradient>0)] = 0
        projected[(point >= 1-1e-6)&(gradient<0)] = 0
        scale = np.maximum(np.linalg.norm(jac, axis=0), 1.)*max(np.linalg.norm(residual), 1.)
        scaled = projected/scale
        _, singular, vt = np.linalg.svd(jac, full_matrices=False)
        return dict(full_coordinate_order=list(self.original.bounds.active),
            free_coordinate_order=list(self.bounds.active), fixed_normalized_coordinates=self.bounds.fixed,
            full_normalized_parameters=self.expand(point).tolist(), full_gradient=full_gradient.tolist(),
            gradient=gradient.tolist(), projected_gradient=projected.tolist(),
            scaled_projected_gradient=scaled.tolist(), singular_values=singular.tolist(),
            right_singular_vectors=vt.tolist(),
            saved_stationarity=float(np.max(abs(scaled))) if len(scaled) else 0.,
            accepted_step_history_available=False, diagnostic_extra_native_passes=0)
