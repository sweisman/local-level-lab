# SPDX-License-Identifier: AGPL-3.0-or-later
"""Gyro-free force envelopes over receiver windows allowed by an error box."""

import math

import numpy as np

from .ilvis0_derivative_bounds import jet_error_bounds
from .ilvis0_error_model import Spec, covariance
from .ilvis0_force_bounds import force_bounds
from .ilvis0_joint_receiver_force import MAX_EMBEDDED_WEIGHT_BYTES
from .ilvis0_receiver_derivatives import LocalPolynomial
from .ilvis0_receiver_force import FIELD_MODELS, MATCHED_MODELS
from .ilvis0_receiver_support import SupportPolicy, motion_from_gga_fixes, select_support
from .ilvis0_receiver_trajectory import MAX_LOCAL_RECEIVER_EPOCHS, _selected_coordinates
from .ilvis0_structured_force_projection import project_candidate_forces
from .ilvis0_support_stability import bound_support
from .models import WGS84_A, WGS84_E2


def screening_errors(times, coordinates, errors, speed):
    """Enclose changes in the WGS84 GGA screening rates for fixed timestamps."""
    n = len(times)
    first = np.maximum(0, np.arange(n)-1)
    last = np.minimum(n-1, np.arange(n)+1)
    elapsed = times[last]-times[first]
    displacement = coordinates[last, :2]-coordinates[first, :2]
    displacement[:, 1] = (displacement[:, 1]+np.pi)%(2*np.pi)-np.pi
    endpoint_error = errors[last]+errors[first]
    phi, _, height = coordinates.T
    phi_error, _, height_error = errors.T
    if (np.any(abs(phi)+phi_error >= math.acos(1e-3))
            or np.any(abs(displacement[:, 1])+endpoint_error[:, 1] >= np.pi)):
        raise ValueError('position error box crosses a receiver screening chart boundary')

    # Global latitude derivative bounds, using |sin(phi) cos(phi)| <= 1.
    minimum = 1.-WGS84_E2
    prime_limit = WGS84_A/math.sqrt(minimum)
    prime_slope = prime_limit*WGS84_E2/minimum
    meridian_slope = 3.*prime_slope
    height_limit = abs(height)+height_error
    metric_error = np.column_stack((
        meridian_slope*phi_error + height_error,
        (prime_slope+prime_limit+height_limit)*phi_error + height_error))
    horizontal = ((prime_limit+height_limit[:, None])*endpoint_error[:, :2]
                  + abs(displacement)*metric_error)/elapsed[:, None]
    radius = np.linalg.norm(horizontal, axis=1)
    # A disk of radius r around a nonzero velocity subtends asin(r/speed).
    ratio = np.divide(radius, speed, out=np.ones(n), where=speed > 0.)
    angle = np.where(radius == 0., 0.,
                     np.where(ratio < 1., np.arcsin(np.minimum(1., ratio)), np.pi))
    return dict(speed_error_mps=float(radius.max()),
                course_error_deg=float(np.rad2deg(angle.max())),
                vertical_error_mps=float((endpoint_error[:, 2]/elapsed).max()))


def assess(fixes, *, spec, targets_s, policy, degree, derivative_envelopes,
           coordinate_error_bounds, background_rate_rads, gravity_bounds_mps2,
           disc_radius_m, return_receiver_weights=False):
    """Keep every possible longest window, then bound its four force predictions.

    The coordinate box is simultaneous over the whole supplied GGA record.
    The structured covariance retains shared errors in the separate linearized
    window estimates. Neither input specifies a calibrated error law here.
    """
    rows = tuple(fixes)
    targets = np.asarray(targets_s, dtype=float)
    envelopes = np.asarray(derivative_envelopes, dtype=float)
    errors = np.asarray(coordinate_error_bounds, dtype=float)
    gravity = np.asarray(gravity_bounds_mps2, dtype=float)
    n = len(rows)
    if (not isinstance(spec, Spec) or not isinstance(policy, SupportPolicy)
            or targets.ndim != 1 or not len(targets)
            or not np.isfinite(targets).all() or np.any(np.diff(targets) <= 0.)
            or degree not in (2, 3, 4) or envelopes.shape != (degree+2, 3)
            or not np.isfinite(envelopes).all() or np.any(envelopes < 0.)
            or errors.shape != (n, 3) or not np.isfinite(errors).all() or np.any(errors < 0.)
            or gravity.shape != (2,) or not np.isfinite(gravity).all()
            or not 0. < gravity[0] <= gravity[1]
            or not math.isfinite(background_rate_rads)
            or not math.isfinite(disc_radius_m) or disc_radius_m <= 0.):
        raise ValueError('ordered targets and explicit receiver, derivative and physical bounds required')
    motion = motion_from_gga_fixes(rows, maximum_gap_s=policy.maximum_gap_s)
    times = np.asarray(motion['times_s'])
    coordinates = _selected_coordinates(rows, 0, n-1, motion['ellipsoidal_height_m'])
    motion_errors = screening_errors(times, coordinates, errors, np.asarray(motion['speed_mps']))
    target_records, branches, supports = [], [], []
    for index, target in enumerate(targets):
        selected = select_support(times, motion['speed_mps'], motion['course_deg'],
                                  motion['vertical_rate_mps'], target_s=float(target), policy=policy)
        possible = bound_support(motion, selected, policy=policy, **motion_errors)
        statuses = possible['candidate_status']
        choices = []
        for window, status in reversed(list(zip(selected['windows'], statuses, strict=True))):
            if status != 'certain_reject':
                choices.append(window)
            if status == 'certain_accept':
                break
        choices.reverse()
        widths = [window['half_window_s'] for window in choices]
        branches.extend((index, width) for width in widths)
        supports.extend(choices)
        target_records.append(dict(target_s=float(target),
            nominal_choice_s=selected['selected_half_window_s'],
            possible_choices_s=[*widths, None] if 'certain_accept' not in statuses else widths,
            candidate_status=statuses))

    result = dict(targets=target_records, branches=branches, model_order=MATCHED_MODELS,
                  motion_errors=motion_errors, joint_covariance_mps4=None,
                  required_force_magnitude_mps2=None, magnitude_ranges_mps2=None,
                  gyro_observations_used=False, fused_navigation_used=False,
                  receiver_covariance_calibrated=False, selection_box_propagated=True,
                  scientific_decision='abstain')
    if not branches:
        return result
    if 27*n*len(branches)*8 > MAX_EMBEDDED_WEIGHT_BYTES:
        raise ValueError('embedded receiver weights exceed declared workspace')
    weights = np.zeros((len(branches), 9, 3*n))
    jets, ranges = [], {model: [] for model in MATCHED_MODELS}
    for slot, ((index, _), window) in enumerate(zip(branches, supports, strict=True)):
        first, stop = window['first_index'], window['last_index']+1
        if stop-first > MAX_LOCAL_RECEIVER_EPOCHS:
            raise ValueError('alternative local receiver support exceeds declared limit')
        local_times = times[first:stop]
        operator = LocalPolynomial(local_times, targets[index], covariance(local_times, spec),
                                   degree=degree, maximum_gap_s=policy.maximum_gap_s)
        trajectory = operator.apply(
            _selected_coordinates(rows, first, stop-1, motion['ellipsoidal_height_m']))
        jet = np.concatenate([trajectory[key] for key in ('position', 'rate', 'acceleration')])
        radius = jet_error_bounds(operator.weights, local_times, targets[index],
            derivative_envelopes=envelopes,
            coordinate_error_bounds=errors[first:stop])['total_jet_error_bounds']
        box = np.column_stack((jet-radius, jet+radius))
        for model in MATCHED_MODELS:
            rate = background_rate_rads if model in FIELD_MODELS else 0.
            bounded = force_bounds(box, model=model, background_rate_bounds_rads=(rate, rate),
                gravity_bounds_mps2=gravity, disc_radius_m=disc_radius_m, include_matched_disc=True)
            ranges[model].append(bounded['magnitude_bounds_mps2'])
        jets.append(jet)
        weights[slot, :, 3*first:3*stop] = operator.weights
    result.update(project_candidate_forces(times, spec, np.asarray(jets), weights,
        background_rate_rads=background_rate_rads, gravity_mps2=float(gravity.mean()),
        disc_radius_m=disc_radius_m, include_matched_disc=True,
        return_receiver_weights=return_receiver_weights),
        magnitude_ranges_mps2={model: np.asarray(values) for model, values in ranges.items()})
    return result
