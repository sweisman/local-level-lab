# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive shape-first result for matched generated candidate envelopes."""

from .matched_candidate_case import MODELS


def shape_first(covered, converged):
    """Summarize a generated control; never promote it to scientific evidence."""
    if (set(covered) != set(MODELS) or set(converged) != set(MODELS)
            or any(type(covered[m]) is not bool or type(converged[m]) is not bool
                   for m in MODELS)):
        raise ValueError('complete three-candidate Boolean results required')
    result = dict(shape='abstain', background_field='abstain',
                  scientific_decision='abstain')
    if not all(converged.values()):
        return result
    globe = covered['sphere_rotating'] or covered['sphere_still']
    flat = covered['flat_still']
    if globe == flat:
        return result
    result['shape'] = 'globe' if globe else 'flat'
    if globe:
        rotating = covered['sphere_rotating']
        still = covered['sphere_still']
        if rotating != still:
            result['background_field'] = ('specified_nonzero' if rotating
                                          else 'zero')
    return result
