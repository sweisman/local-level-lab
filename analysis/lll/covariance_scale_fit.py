# SPDX-License-Identifier: AGPL-3.0-or-later
"""Dense reference fit for additive Gaussian forecast-error covariance terms."""


def training_contrasts(roots, draws, design, parameter_scales, *, rank_rtol):
    """Remove the scaled training mean design from errors and covariance roots."""
    import numpy as np

    draws = np.asarray(draws, float)
    design = np.asarray(design, float)
    scales = np.asarray(parameter_scales, float)
    if (draws.ndim != 2 or not draws.size or design.ndim != 2
            or design.shape[0] != draws.shape[1] or design.shape[1] < 1
            or scales.shape != (design.shape[1],) or np.any(scales <= 0)
            or not all(np.isfinite(values).all() for values in (draws, design, scales))
            or not 0 < rank_rtol < 1):
        raise ValueError('aligned training data and mean design with positive parameter scales required')
    scaled = design * scales
    if not np.isfinite(scaled).all():
        raise ValueError('unrepresentable scaled training mean design')
    basis, singular, _ = np.linalg.svd(scaled, full_matrices=True)
    rank = int(np.count_nonzero(singular > singular[0] * rank_rtol))
    contrast = basis[:, rank:]
    if not contrast.shape[1]:
        raise ValueError('no residual degrees of freedom in training mean design')

    restricted = {}
    for name, root in roots.items():
        root = np.asarray(root, float)
        if root.ndim != 2 or root.shape[0] != len(contrast) or not np.isfinite(root).all():
            raise ValueError('covariance roots must cover exactly the training rows')
        projected = contrast.T @ root
        # A removed root can leave numerical residue. Normalizing that residue
        # in the variance rank test would turn roundoff into information.
        if np.linalg.norm(projected) <= rank_rtol * np.linalg.norm(root):
            projected.fill(0.)
        restricted[name] = projected
    return restricted, draws @ contrast


def fit_training(groups, *, log_bounds, max_evaluations, rank_rtol):
    """Fit covariance scales by restricted likelihood with an unknown linear mean."""
    restricted = (training_contrasts(*group, rank_rtol=rank_rtol) for group in groups)
    return fit(restricted, log_bounds=log_bounds, max_evaluations=max_evaluations)


def fit(groups, *, log_bounds, max_evaluations):
    """Fit variance multipliers at a fixed, known forecast mean.

    Each group is (named covariance roots, error draws). Rows of error draws
    must be independent. Correlated epochs belong in the same row with their
    joint covariance. This reference calculation is for small designs.
    """
    import numpy as np
    from scipy.linalg import cho_factor, cho_solve
    from scipy.optimize import minimize

    lower, upper = map(float, log_bounds)
    with np.errstate(over='ignore', under='ignore'):
        variance_bounds = np.exp([lower, upper])
    if not (lower < upper and np.isfinite([lower, upper]).all()
            and np.isfinite(variance_bounds).all() and variance_bounds[0] > 0
            and isinstance(max_evaluations, int) and max_evaluations > 0):
        raise ValueError('finite log-variance bounds and a positive evaluation limit required')

    names = None
    design = []
    for roots, draws in groups:
        if names is None:
            names = tuple(roots)
        if len(names) < 2 or set(names) != roots.keys():
            raise ValueError('each group must have the same two or more named components')
        draws = np.asarray(draws, float)
        if draws.ndim != 2 or not draws.size or not np.isfinite(draws).all():
            raise ValueError('each group requires finite, nonempty rows of error draws')
        arrays = [np.asarray(roots[name], float) for name in names]
        if any(root.ndim != 2 or root.shape[0] != draws.shape[1]
               or not np.isfinite(root).all() for root in arrays):
            raise ValueError('each covariance root must align with the error draws')
        covariance = np.asarray([root @ root.T for root in arrays])
        design.append((covariance, draws.T @ draws / len(draws), len(draws)))
    if not design:
        raise ValueError('at least one covariance design required')

    # An invertible covariance whitening preserves dependence between terms.
    # Normalize before testing it to avoid dependence on the input units.
    derivatives = np.concatenate([c.reshape(len(names), -1) for c, _, _ in design], axis=1)
    norms = np.linalg.norm(derivatives, axis=1, keepdims=True)
    normalized = derivatives / np.where(norms > 0, norms, 1.)
    singular = np.linalg.svd(normalized, compute_uv=False)
    rank = int(np.count_nonzero(singular > singular[0] * 1e-10))
    evaluations = 0

    def result(status, variances=None):
        return dict(status=status, rank=rank, evaluations=evaluations, variances=variances)

    if rank < len(names):
        return result('unidentifiable')
    total_draws = sum(count for _, _, count in design)

    class EvaluationLimit(Exception):
        pass

    def objective(log_variance):
        nonlocal evaluations
        if evaluations == max_evaluations:
            raise EvaluationLimit
        evaluations += 1
        variance = np.exp(log_variance)
        loss = 0.
        gradient = np.zeros_like(log_variance)
        for components, scatter, count in design:
            covariance = np.einsum('i,ijk->jk', variance, components)
            factors = cho_factor(covariance, lower=True)
            inverse = cho_solve(factors, np.eye(len(covariance)))
            weight = count / total_draws
            loss += weight * (2. * np.log(factors[0].diagonal()).sum()
                              + np.sum(inverse * scatter))
            derivative = inverse - inverse @ scatter @ inverse
            gradient += weight * variance * np.einsum('ijk,jk->i', components, derivative)
        return loss, gradient

    try:
        optimum = minimize(objective, np.full(len(names), np.clip(0., lower, upper)),
                           method='L-BFGS-B', jac=True, bounds=[(lower, upper)] * len(names),
                           options=dict(maxfun=max_evaluations, maxiter=max_evaluations,
                                        ftol=1e-14, gtol=1e-8))
    except EvaluationLimit:
        return result('budget_exhausted')

    at_lower = optimum.x - lower <= 1e-8
    at_upper = upper - optimum.x <= 1e-8
    projected_gradient = np.where((at_lower & (optimum.jac >= 0))
                                  | (at_upper & (optimum.jac <= 0)), 0., optimum.jac)
    if not optimum.success or not np.all(np.abs(projected_gradient) <= 1e-6):
        return result('budget_exhausted' if evaluations >= max_evaluations else 'stopping_failure')
    status = 'bound' if np.any(at_lower | at_upper) else 'interior'
    return result(status, dict(zip(names, np.exp(optimum.x).tolist(), strict=True)))
