# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recheck the conditional remainder before the unchanged joint-schema bridge."""
from dataclasses import replace

from .ilvis0_conditional_remainder import enclose
from .ilvis0_direct_interface import bridge as original_bridge,matched_bounds
from .ilvis0_directional_acceleration import DirectionalAcceleration
from .ilvis0_conditioned_acceleration import ConditionedAcceleration
from .ilvis0_transform_native import TransformReference
from . import ilvis0_remainder_native as candidate


def bridge(report,reference,proof,native_center,scale):
    if (not isinstance(report,candidate.TransformEnclosure) or not isinstance(reference,TransformReference)
            or not isinstance(proof,(DirectionalAcceleration,ConditionedAcceleration))):
        raise ValueError('typed conditional bound, reference and proof required')
    metadata=report.metadata
    if any(k not in metadata for k in ('lower','upper','conditional_acceleration_remainder')):
        raise ValueError('complete conditional remainder certificate required')
    _,components=proof.match(reference.report(),metadata['lower'],metadata['upper'])
    a=reference.acceleration
    expected=enclose(a.jacobian,metadata['lower'],metadata['upper'],reference.parent.center,
        components,a.remainder)
    if metadata['conditional_acceleration_remainder']!=expected:
        raise ValueError('conditional remainder certificate or source domain changed')
    # Retain all existing source/cap/center checks and exact center transfer.
    result=original_bridge(report,reference,proof,native_center,scale)
    updated=dict(result.metadata,native_candidate_version=candidate.VERSION,
        bridge_version='ilvis0-conditional-remainder-joint-schema-v1')
    return replace(result,metadata=updated)
