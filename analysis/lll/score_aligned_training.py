# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propose earlier residual directions aligned with a later linear score."""


def score_directions(design, objective, lower, upper, *, cutoffs):
    """Use scaled singular vectors for proposals, while leaving the exact box intact."""
    import numpy as np

    design, objective, lo, hi = (np.asarray(v, float) for v in (design, objective, lower, upper))
    if (design.ndim != 2 or not design.size or objective.shape != (design.shape[1],)
            or objective.shape != lo.shape or lo.shape != hi.shape or np.any(lo > hi)
            or not all(np.isfinite(v).all() for v in (design, objective, lo, hi))
            or not cutoffs or any(not 0 < value < 1 for value in cutoffs)):
        raise ValueError('finite calibration box, aligned design and relative cutoffs required')
    widths = (hi-lo)/2.
    left, singular, right = np.linalg.svd(design*widths, full_matrices=False)
    target = objective*widths
    score = right @ target
    records = []
    for cutoff in cutoffs:
        use = (singular >= singular[0]*cutoff) & (singular > 0.)
        direction = left[:, use] @ (score[use]/singular[use])
        norm = np.max(np.abs(direction))
        records.append(dict(cutoff=cutoff, rank=int(np.count_nonzero(use)),
                            axis=direction/norm if norm else None))
    return records
