# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact residual-shift control for a native turning-route solver test."""

import numpy as np


class ShiftedProblem:
    """Keep the native trajectory derivative; set one feasible point to zero."""

    def __init__(self, base, target_residual, model):
        target_residual = np.asarray(target_residual, float)
        if (target_residual.ndim != 1 or not len(target_residual)
                or not np.all(np.isfinite(target_residual)) or not isinstance(model, str)):
            raise ValueError('complete finite native target residual required')
        self.base = base
        self.target_residual = target_residual.copy()
        self.model = model

    def __getattr__(self, name):
        return getattr(self.base, name)

    def residual_tangent(self, point, model):
        if model != self.model:
            raise ValueError('unchanged model required')
        residual, jacobian, boundaries = self.base.residual_tangent(point, model)
        residual = np.asarray(residual, float)
        jacobian = np.asarray(jacobian, float)
        if (residual.shape != self.target_residual.shape
                or jacobian.shape != (len(residual), len(point))
                or not np.all(np.isfinite(residual)) or not np.all(np.isfinite(jacobian))):
            raise ValueError('complete native residual and derivative required')
        return residual-self.target_residual, jacobian, boundaries


def start_point(target, index):
    target = np.asarray(target, float)
    if (target.ndim != 1 or not len(target) or not np.all(np.isfinite(target))
            or np.any(abs(target) > 1) or type(index) is not int or index not in (0, 1)):
        raise ValueError('feasible target and declared start required')
    if index == 0:
        return np.zeros(len(target))
    return np.clip(target+.05*np.sin(np.arange(len(target))+1), -.95, .95)
