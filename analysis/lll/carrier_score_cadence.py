# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project carrier score weights onto observable ground-clock-free range totals."""
import numpy as np


def project_cadence(support, dual, intervals, *, available=None, interval_satellites=None):
    """Project one weight vector or each column of an aligned range matrix."""
    dual = np.asarray(dual, float)
    offsets = np.r_[0, np.cumsum([len(prns) for prns in support])]
    if (dual.ndim not in (1, 2) or dual.shape[0] != offsets[-1] or not np.isfinite(dual).all()
            or any(len(set(prns)) != len(prns) for prns in support)):
        raise ValueError('finite carrier weights and unique aligned satellite rows required')
    projected = np.zeros_like(dual)
    index = [{prn: start+j for j, prn in enumerate(prns)} for start, prns in zip(offsets[:-1], support, strict=True)]
    previous = 0
    results = []
    for first, last in intervals:
        if not previous <= first < last <= len(support):
            raise ValueError('ordered nonoverlapping carrier intervals required')
        previous = last
        matched = set.intersection(*(set(prns) for prns in support[first:last]))
        if available is not None:
            matched.intersection_update(available)
        if interval_satellites is not None:
            matched.intersection_update(interval_satellites[first, last])
        prns = sorted(matched)
        if len(prns) < 2:
            continue
        positions = np.array([[row[prn] for prn in prns] for row in index[first:last]])
        mean = dual[positions].mean(axis=0)
        # Equal weight within the ground interval. The zero-sum satellite
        # weights cancel the separate unknown receiver clock in every pair.
        weights = mean-mean.mean(axis=0)
        projected[positions] = weights
        results.append(dict(first=first, last=last, satellites=prns, aggregate_weights=weights.tolist()))
    full, visible = np.linalg.norm(dual), np.linalg.norm(projected)
    return dict(intervals=results, projected_weights=projected.tolist(), projected_norm=float(visible),
                unobserved_norm=float(np.linalg.norm(dual-projected)),
                observable_norm_fraction=float(visible/full) if full else 0.)
