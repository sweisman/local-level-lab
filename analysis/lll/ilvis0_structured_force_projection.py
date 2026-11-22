# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project a supplied receiver-error law without a dense epoch covariance.

The output is a conditional covariance of fixed linear summaries. It does not
estimate the error law, account for support selection or calibrate coverage.
"""

import numpy as np

from .ilvis0_error_model import Spec
from .ilvis0_force_magnitude_covariance import _gradient, _magnitude
from .ilvis0_receiver_force import FIELD_MODELS, MATCHED_MODELS, MODELS, evaluate


VERSION = 'ilvis0-structured-force-projection-v1'


def project_covariance(times, spec, weights, *, transforms=None):
    """Return ``W C W.T`` for the shared white/OU/offset/drift receiver law.

    ``weights`` has one row per summary and epoch-major three-coordinate
    columns. Optional per-epoch transforms map the Spec's three axes to those
    coordinates. Workspace grows with epochs times summary rows, without a
    dense covariance over all receiver epochs.
    """
    t = np.asarray(times, dtype=float)
    if (t.ndim != 1 or not len(t) or not np.all(np.isfinite(t)) or
            np.any(np.diff(t) <= 0.) or not isinstance(spec, Spec)):
        raise ValueError('finite ordered receiver epochs and declared Spec required')
    w = np.asarray(weights, dtype=float)
    n = len(t)
    if (w.ndim != 2 or not w.shape[0] or w.shape[1] != 3*n or
            not np.all(np.isfinite(w))):
        raise ValueError('finite summary weights on all receiver epochs required')
    if transforms is None:
        loading = w.reshape(w.shape[0], n, 3).transpose(1, 2, 0).copy()
    else:
        a = np.asarray(transforms, dtype=float)
        if (a.shape != (n, 3, 3) or not np.all(np.isfinite(a)) or
                np.any(np.linalg.slogdet(a)[0] == 0)):
            raise ValueError('finite invertible receiver transforms required')
        loading = np.einsum('kni,nij->njk', w.reshape(w.shape[0], n, 3), a)
    projected = covariance_action(t, spec, loading)
    factor_left = loading.reshape(3*n, w.shape[0])
    factor_right = projected.reshape(3*n, w.shape[0])
    result = factor_left.T @ factor_right
    result = (result+result.T)/2.
    if not np.all(np.isfinite(result)):
        raise ValueError('finite projected receiver covariance required')
    return result


def covariance_action(times, spec, loadings):
    """Apply the shared receiver law to epoch-major three-axis loadings."""
    t = np.asarray(times, float)
    loading = np.asarray(loadings, float)
    if (t.ndim != 1 or not t.size or not np.isfinite(t).all() or np.any(np.diff(t) <= 0.)
            or loading.ndim != 3 or loading.shape[:2] != (t.size, 3) or not loading.shape[2]
            or not np.isfinite(loading).all() or not isinstance(spec, Spec)):
        raise ValueError('finite receiver epochs and aligned three-axis loadings required')
    n = len(t)
    projected = np.einsum('ab,nbk->nak', spec.white, loading)
    total = loading.sum(axis=0)
    projected += (spec.offset @ total)[None, :, :]
    u = (t-spec.drift_origin_s)/spec.drift_span_s
    projected += u[:, None, None]*(spec.drift @
                                    np.einsum('n,nik->ik', u, loading))[None, :, :]
    for tau, component in spec.components:
        left = np.empty_like(loading)
        state = np.zeros_like(loading[0])
        for index in range(n):
            if index:
                state *= np.exp(-(t[index]-t[index-1])/tau)
            state += loading[index]
            left[index] = state
        state.fill(0.)
        for index in range(n-1, -1, -1):
            if index < n-1:
                state *= np.exp(-(t[index+1]-t[index])/tau)
            state += loading[index]
            projected[index] += component@(left[index]+state-loading[index])
    return projected


def project_candidate_forces(times, spec, jets, embedded_weights, *,
                             transforms=None, background_rate_rads,
                             gravity_mps2, disc_radius_m, include_matched_disc=False,
                             return_receiver_weights=False):
    """Project one common receiver law through all candidate force magnitudes.

    The caller must select shared target windows and provide their trajectory
    jets and derivative weights. This calculation does not select support,
    estimate calibration or make a model decision. The fourth candidate is
    an explicit opt-in for the matched-field study.
    """
    t = np.asarray(times, dtype=float)
    coordinates = np.asarray(jets, dtype=float)
    weights = np.asarray(embedded_weights, dtype=float)
    if (coordinates.ndim != 2 or coordinates.shape[1:] != (9,) or
            not len(coordinates) or not np.all(np.isfinite(coordinates)) or
            weights.shape != (len(coordinates), 9, 3*len(t)) or
            not np.all(np.isfinite(weights))):
        raise ValueError('finite shared trajectory jets and receiver weights required')
    magnitudes = {}
    vectors = {}
    sensitivities = []
    if type(include_matched_disc) is not bool:
        raise ValueError('explicit matched-disc option required')
    candidates = MATCHED_MODELS if include_matched_disc else MODELS
    for model in candidates:
        rate = background_rate_rads if model in FIELD_MODELS else 0.
        if include_matched_disc:
            vectors[model] = np.stack([
                evaluate(row[:3], row[3:6], row[6:], model=model,
                         background_rate_rads=rate, gravity_mps2=gravity_mps2,
                         disc_radius_m=disc_radius_m)['specific_force_ned_mps2']
                for row in coordinates])
            magnitudes[model] = np.linalg.norm(vectors[model], axis=1)
        else:
            magnitudes[model] = np.asarray([
                _magnitude(row, model=model, background_rate_rads=rate,
                           gravity_mps2=gravity_mps2, disc_radius_m=disc_radius_m)
                for row in coordinates])
        gradient = np.vstack([
            _gradient(row, model=model, background_rate_rads=rate,
                      gravity_mps2=gravity_mps2, disc_radius_m=disc_radius_m)
            for row in coordinates])
        sensitivities.append(np.einsum('mi,mij->mj', gradient, weights))
    weights = np.vstack(sensitivities)
    covariance = project_covariance(t, spec, weights, transforms=transforms)
    result = dict(version=VERSION, model_order=candidates,
                required_force_magnitude_mps2=magnitudes,
                joint_covariance_mps4=covariance,
                receiver_covariance_calibrated=False,
                support_selection_uncertainty_accounted=False,
                linearization_coverage_established=False,
                gyro_observations_used=False,
                fused_navigation_used=False,
                scientific_decision='abstain')
    if include_matched_disc:
        result['required_force_ned_mps2'] = vectors
    if return_receiver_weights:
        result['magnitude_receiver_weights'] = weights
    return result
