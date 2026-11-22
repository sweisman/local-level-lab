# SPDX-License-Identifier: AGPL-3.0-or-later
"""Differentiate the native-innovation likelihood with low-rank added covariance."""

from .esa_innovation_persistence import PersistenceScore, transitions


def loss_and_gradient(baseline, times, point):
    """Return the Gaussian loss and its derivative in six log coordinates."""
    import numpy as np
    from scipy.linalg import cho_solve

    point = np.asarray(point, dtype=float)
    if point.shape != (6,) or not np.isfinite(point).all():
        raise ValueError('six finite log parameters required')
    score = PersistenceScore(baseline, times, point[:4])
    variance_parameters, memory = np.exp(point[:4]), np.exp(point[4:])
    phi = transitions(times, score.response, *memory)
    sigma = np.sqrt((1.-phi)*(1.+phi))
    if np.any(sigma <= 0.):
        raise ValueError('strictly positive innovation variance required')
    phi_column, sigma_column = phi[:, None, None], sigma[:, None, None]

    def whiten(data):
        white = data.copy()
        white[1:] = (data[1:]-phi_column*data[:-1])/sigma_column
        return white

    white = whiten(score.data)
    flat = white.reshape(-1, white.shape[-1])
    y, root = flat[:, 0], flat[:, 1:]
    # Integrate the extra covariance after whitening. Differentiate the
    # minimized quadratic at its optimum and the log determinant of its factor.
    factor = np.linalg.cholesky(baseline.identity+root.T@root)
    coefficients = cho_solve((factor, True), root.T@y, check_finite=False)
    error = y-root@coefficients
    root_score = cho_solve((factor, True), root.T, check_finite=False).T-np.outer(error, coefficients)
    sensitivity = np.column_stack((error, root_score)).reshape(white.shape)
    loss = (baseline.normalization + .5*(error@error+coefficients@coefficients)
            + np.log(factor.diagonal()).sum() + 3.*np.log(sigma).sum())

    response = score.response[:, None]
    variance = variance_parameters[:3]+variance_parameters[3]*response
    loss += .5*np.log(variance).sum()
    variance_derivatives = (*np.diag(variance_parameters[:3]), variance_parameters[3]*response)
    gradient = []
    for derivative in variance_derivatives:
        relative = derivative/variance
        white_derivative = whiten(-.5*relative[:, :, None]*score.data)
        gradient.append(.5*relative.sum()+(sensitivity*white_derivative).sum())

    response = score.response[1:]
    for blend, tau in zip((1.-response, response), memory, strict=True):
        ratio = np.diff(times)/tau
        phi_derivative = blend*np.exp(-ratio)*ratio
        log_sigma_derivative = -phi*phi_derivative/sigma**2
        white_derivative = (-phi_derivative[:, None, None]*score.data[:-1]/sigma_column
                            -white[1:]*log_sigma_derivative[:, None, None])
        gradient.append(3.*log_sigma_derivative.sum()+(sensitivity[1:]*white_derivative).sum())
    return float(loss), np.asarray(gradient)
