# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind receiver-selected local trajectories to joint gyro-free force error."""

import math
import numpy as np

from .ilvis0_force_magnitude_covariance import MAX_RECEIVER_EPOCHS, propagate
from .ilvis0_error_model import Spec
from .ilvis0_receiver_force import MATCHED_MODELS, MODELS
from .ilvis0_receiver_support import (
    SupportPolicy, motion_from_enhanced_positions, motion_from_gga_fixes)
from .ilvis0_receiver_trajectory import (
    local_trajectory_from_enhanced_spec, local_trajectory_from_gga,
    local_trajectory_from_gga_spec)
from .ilvis0_structured_force_projection import project_candidate_forces


VERSION = 'ilvis0-joint-receiver-force-v3'
MAX_EMBEDDED_WEIGHT_BYTES = 128*1024*1024


def assess(fixes, coordinate_covariance, *, targets_s, policy, degree, model,
           background_rate_rads, gravity_mps2, disc_radius_m):
    """Select common GPS windows and propagate one supplied covariance.

    Targets and support policy come from outside this function. Support uses
    receiver motion only, before the physical model is evaluated. Rejected
    target windows remain visible. No IMU or fused navigation is read here.
    """
    fixes = tuple(fixes)
    targets = np.asarray(targets_s, dtype=float)
    covariance = np.asarray(coordinate_covariance, dtype=float)
    n = len(fixes)
    if (model not in MODELS or
            not all(math.isfinite(value) for value in
                    (background_rate_rads, gravity_mps2, disc_radius_m)) or
            gravity_mps2 <= 0. or disc_radius_m <= 0. or
            (model != 'sphere_rotating' and background_rate_rads != 0.)):
        raise ValueError('explicit supported physical model and constants required')
    if (not 3 <= n <= MAX_RECEIVER_EPOCHS or
            targets.ndim != 1 or len(targets) == 0 or
            not np.all(np.isfinite(targets)) or
            np.any(np.diff(targets) <= 0) or
            covariance.shape != (3*n, 3*n) or
            not np.all(np.isfinite(covariance)) or
            not np.allclose(covariance, covariance.T, rtol=1e-12, atol=0.)):
        raise ValueError('finite ordered receiver targets and joint covariance required')
    try:
        np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError as error:
        raise ValueError('positive definite joint receiver covariance required') from error
    rows = []
    jets = []
    weights = []
    supported_indices = []
    for index, target in enumerate(targets):
        record = local_trajectory_from_gga(
            fixes, covariance, target_s=float(target), policy=policy,
            degree=degree)
        selected = record['support']['selected_indices']
        rows.append(dict(target_s=float(target), selected_indices=selected,
                         supported=selected is not None,
                         support=record['support']))
        if selected is None:
            continue
        first, last = selected
        local = record['derivative_weights']
        if local.shape != (9, 3*(last-first+1)):
            raise ValueError('receiver derivative weights differ from selected support')
        embedded = np.zeros((9, 3*n))
        embedded[:, 3*first:3*(last+1)] = local
        trajectory = record['trajectory']
        jets.append(np.concatenate([trajectory[key]
                                    for key in ('position', 'rate', 'acceleration')]))
        weights.append(embedded)
        supported_indices.append(index)
    propagated = (propagate(np.asarray(jets), np.asarray(weights), covariance,
                            model=model,
                            background_rate_rads=background_rate_rads,
                            gravity_mps2=gravity_mps2,
                            disc_radius_m=disc_radius_m)
                  if jets else None)
    return dict(version=VERSION, source='primary_receiver_gga',
                model=model, targets=rows,
                supported_target_indices=supported_indices,
                required_force_magnitude_mps2=(
                    None if propagated is None else
                    propagated['required_force_magnitude_mps2']),
                receiver_sensitivity=(
                    None if propagated is None else
                    propagated['receiver_sensitivity']),
                conditional_covariance_mps4=(
                    None if propagated is None else
                    propagated['conditional_covariance_mps4']),
                receiver_covariance_calibrated=False,
                gyro_observations_used=False,
                fused_navigation_used=False,
                scientific_decision='abstain')


def assess_candidates(fixes, coordinate_covariance, *, targets_s, policy,
                      degree, background_rate_rads, gravity_mps2,
                      disc_radius_m):
    """Preserve GPS-error correlation across all three physical candidates.

    Block order follows ``MODELS``; each block follows supported target order.
    The covariance is conditional on the supplied receiver law and selected
    windows. It is not a calibrated likelihood or an Earth-model decision.
    """
    fixes = tuple(fixes)
    results = {
        model: assess(
            fixes, coordinate_covariance, targets_s=targets_s,
            policy=policy, degree=degree, model=model,
            background_rate_rads=(background_rate_rads
                                   if model == 'sphere_rotating' else 0.),
            gravity_mps2=gravity_mps2, disc_radius_m=disc_radius_m)
        for model in MODELS}
    first = results[MODELS[0]]
    windows = [row['selected_indices'] for row in first['targets']]
    if any([row['selected_indices'] for row in results[model]['targets']]
           != windows for model in MODELS[1:]):
        raise ValueError('candidate support differs across physical models')
    if first['supported_target_indices']:
        sensitivity = np.vstack([
            results[model]['receiver_sensitivity'] for model in MODELS])
        covariance = np.asarray(coordinate_covariance, dtype=float)
        joint = sensitivity @ covariance @ sensitivity.T
        joint = (joint + joint.T)/2.
    else:
        joint = None
    return dict(version=VERSION, source='primary_receiver_gga',
                model_order=MODELS,
                supported_target_indices=first['supported_target_indices'],
                selected_indices=windows,
                required_force_magnitude_mps2={
                    model: results[model]['required_force_magnitude_mps2']
                    for model in MODELS},
                joint_covariance_mps4=joint,
                receiver_covariance_calibrated=False,
                support_selection_uncertainty_accounted=False,
                gyro_observations_used=False,
                fused_navigation_used=False,
                scientific_decision='abstain')


def assess_candidates_structured(fixes, spec, *, targets_s, policy, degree,
                                 background_rate_rads, gravity_mps2,
                                 disc_radius_m, transforms=None,
                                 source_kind='primary_receiver_gga',
                                 include_matched_disc=False):
    """Apply one supplied structured GPS law to all selected model contrasts.

    Only local derivative windows use dense covariance. Full-record joint
    force covariance uses the structured projection. Rejected targets remain
    visible, and a fixed workspace bound prevents accidental huge allocation.
    """
    fixes = tuple(fixes)
    targets = np.asarray(targets_s, dtype=float)
    n = len(fixes)
    if (not isinstance(spec, Spec) or not isinstance(policy, SupportPolicy) or
            type(include_matched_disc) is not bool or
            not 3 <= n or
            source_kind not in ('primary_receiver_gga',
                                'primary_receiver_enhanced_position') or
            targets.ndim != 1 or not len(targets) or
            not np.all(np.isfinite(targets)) or
            np.any(np.diff(targets) <= 0.) or
            not all(math.isfinite(value) for value in
                    (background_rate_rads, gravity_mps2, disc_radius_m)) or
            gravity_mps2 <= 0. or disc_radius_m <= 0.):
        raise ValueError('ordered receiver support, policy, error law and physical constants required')
    if 27*n*len(targets)*8 > MAX_EMBEDDED_WEIGHT_BYTES:
        raise ValueError('embedded receiver weights exceed declared workspace')
    if source_kind == 'primary_receiver_gga':
        motion = motion_from_gga_fixes(
            fixes, maximum_gap_s=policy.maximum_gap_s)
        local_trajectory = local_trajectory_from_gga_spec
    else:
        motion = motion_from_enhanced_positions(
            fixes, maximum_gap_s=policy.maximum_gap_s)
        local_trajectory = local_trajectory_from_enhanced_spec
    times = motion['times_s']
    rows = []
    jets = []
    weights = []
    supported = []
    for index, target in enumerate(targets):
        record = local_trajectory(
            fixes, spec, target_s=float(target), policy=policy,
            degree=degree, transforms=transforms)
        selected = record['support']['selected_indices']
        rows.append(dict(target_s=float(target), selected_indices=selected,
                         support=record['support']))
        if selected is None:
            continue
        first, last = selected
        local = record['derivative_weights']
        if local.shape != (9, 3*(last-first+1)):
            raise ValueError('receiver derivative weights differ from selected support')
        embedded = np.zeros((9, 3*n))
        embedded[:, 3*first:3*(last+1)] = local
        trajectory = record['trajectory']
        jets.append(np.concatenate([trajectory[key]
                                    for key in ('position', 'rate', 'acceleration')]))
        weights.append(embedded)
        supported.append(index)
    projected = (project_candidate_forces(
        times, spec, np.asarray(jets), np.asarray(weights),
        transforms=transforms,
        background_rate_rads=background_rate_rads,
        gravity_mps2=gravity_mps2, disc_radius_m=disc_radius_m,
        include_matched_disc=include_matched_disc)
        if jets else None)
    candidates = MATCHED_MODELS if include_matched_disc else MODELS
    result = dict(version=VERSION, source=source_kind,
                model_order=candidates, targets=rows,
                selected_indices=[row['selected_indices'] for row in rows],
                supported_target_indices=supported,
                required_force_magnitude_mps2=(
                    projected['required_force_magnitude_mps2'] if projected else
                    {model: None for model in candidates}),
                joint_covariance_mps4=(
                    projected['joint_covariance_mps4'] if projected else None),
                maximum_embedded_weight_bytes=MAX_EMBEDDED_WEIGHT_BYTES,
                receiver_covariance_calibrated=False,
                support_selection_uncertainty_accounted=False,
                gyro_observations_used=False,
                fused_navigation_used=False,
                scientific_decision='abstain')
    if include_matched_disc:
        result['required_force_ned_mps2'] = (
            projected['required_force_ned_mps2'] if projected else
            {model: None for model in candidates})
    return result
