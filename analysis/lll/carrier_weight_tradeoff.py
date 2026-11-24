# SPDX-License-Identifier: AGPL-3.0-or-later
"""Continuous acceleration response and damped carrier-score weights."""

import numpy as np
from scipy.linalg import eigh


def anchor_response(times, anchors):
    """Return the position Green functions in an exact L2 quadrature basis."""
    times, anchors = (np.asarray(value, dtype=float) for value in (times, anchors))
    if (times.ndim != 1 or anchors.ndim != 1 or len(times) < 2 or len(anchors) < 2
            or not all(np.isfinite(values).all() and (np.diff(values) > 0).all()
                       for values in (times, anchors))
            or anchors[0] != times[0] or anchors[-1] != times[-1]
            or not np.isin(anchors, times).all()):
        raise ValueError('ordered score and carrier times must include the exact anchors')
    widths = np.diff(times)
    midpoints, offsets = times[:-1]+widths/2, widths/(2*np.sqrt(3))
    quadrature_times = np.column_stack((midpoints-offsets, midpoints+offsets)).reshape(-1, 1)
    spans = np.minimum(np.searchsorted(anchors, times, side='right')-1, len(anchors)-2)
    start, stop = anchors[spans], anchors[spans+1]
    # x(t) equals the integral of this kernel against acceleration when
    # position is fixed at both ends of the anchor span.
    earlier = np.minimum(times, quadrature_times)
    later = np.maximum(times, quadrature_times)
    response = -(earlier-start)*(stop-later)/(stop-start)
    response = np.where((quadrature_times >= start) & (quadrature_times <= stop), response, 0.)
    return response*np.sqrt(np.repeat(widths/2, 2))[:, None]


def weighted_candidates(response, score, operator, ratios):
    """Solve the declared ridge path once in the response column space."""
    ratios = np.asarray(ratios, dtype=float)
    if (response.ndim != 2 or score.shape != (len(response), 3)
            or operator.shape[1] != 3*response.shape[1] or not operator.shape[0]
            or ratios.ndim != 1 or not np.isfinite(ratios).all() or np.any(ratios <= 0)):
        raise ValueError('matched score, range operator and positive damping ratios required')
    basis, triangular = np.linalg.qr(response, mode='reduced')
    # Apply the same acceleration response to each coordinate without
    # allocating the much larger Kronecker product.
    ranges = np.vstack([(operator[:, axis::3]@triangular.T).T for axis in range(3)])
    target = (basis.T@score).T.ravel()
    eigenvalues, axes = eigh(ranges@ranges.T)
    maximum = eigenvalues[-1]
    if maximum <= 0:
        raise ValueError('the carrier operator supplies no acceleration response')
    coordinates = axes.T@target
    eigenvalues = np.maximum(eigenvalues, 0.)
    return [ranges.T@(axes@(coordinates/(eigenvalues+maximum*ratio**2))) for ratio in ratios]
