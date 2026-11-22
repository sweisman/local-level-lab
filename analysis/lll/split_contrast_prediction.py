# SPDX-License-Identifier: AGPL-3.0-or-later
"""Split-window directional prediction under a fixed affine Gaussian law."""

import numpy as np
from scipy.stats import f

from .state_space_covariance import LinearInnovations


def _adjust(values, uncertainty):
    """Apply inverse square root of identity plus the calibration covariance."""
    vectors, singular = uncertainty
    coordinates = vectors.T @ values
    factors = 1.0 - 1.0 / np.hypot(1.0, singular)
    return values - vectors @ (factors[:, None] * coordinates)


def prepare(operator, design, directions, *, choice_epochs, training_epochs, rank_rtol=1e-10):
    """Freeze directions chosen using only the first window.

    Directions are differences in conditional future observation coordinates.
    The common design and covariance law must be fixed before all observations.
    The later part of the earlier window estimates all calibration parameters
    and the shared variance scale from its innovations only.
    """
    if (not isinstance(operator, LinearInnovations) or type(choice_epochs) is not int
            or type(training_epochs) is not int or not 0 < choice_epochs < training_epochs < operator.epoch_count
            or not 0.0 < rank_rtol < 1.0):
        raise ValueError('fixed operator and three ordered nonempty windows required')
    d = operator.observation_dimension
    n, cut, first = operator.epoch_count * d, training_epochs * d, choice_epochs * d
    design, directions = np.asarray(design, float), np.asarray(directions, float)
    if (design.ndim != 2 or design.shape[0] != n or not 1 <= design.shape[1] <= 27
            or directions.ndim != 2 or directions.shape[0] != n - cut
            or not 1 <= directions.shape[1] <= 2 or not np.isfinite(design).all()
            or not np.isfinite(directions).all()):
        raise ValueError('finite full calibration design and future contrast directions required')
    transformed = operator.whiten(design)
    calibration = transformed[first:cut]
    future = transformed[cut:]
    u, s, v = np.linalg.svd(calibration, full_matrices=False)
    rank = int(np.count_nonzero(s > s[0] * rank_rtol))
    retained = v[:rank].T
    missed = future - (future @ retained) @ retained.T
    result = dict(status='unidentifiable', choice_epochs=choice_epochs, training_epochs=training_epochs,
                  later_observations_used=False, calibration_rank=rank)
    if np.linalg.norm(missed) > rank_rtol * np.linalg.norm(future):
        return result
    dof = len(calibration) - rank
    if dof <= 0:
        result['status'] = 'unavailable_training_scale'
        return result
    uncertainty = np.linalg.svd((future @ retained) / s[:rank], full_matrices=False)[:2]
    _, state = operator.apply_block(np.zeros((cut, directions.shape[1])), first_epoch=0)
    whitened, _ = operator.apply_block(directions, first_epoch=training_epochs, state=state)
    basis, singular, _ = np.linalg.svd(_adjust(whitened, uncertainty), full_matrices=False)
    contrast_rank = int(np.count_nonzero(singular > singular[0] * rank_rtol))
    if contrast_rank == len(directions):
        raise ValueError('a nonempty complementary prediction space is required')
    result.update(status='ready', operator=operator, first=first, cut=cut, calibration=calibration,
                  future_design=future, training_basis=u[:, :rank],
                  estimation=retained / s[:rank], training_dof=dof, uncertainty=uncertainty,
                  contrast_basis=basis[:, :contrast_rank])
    return result


def predict(setup, earlier):
    """Estimate from the second window and advance covariance to the cut."""
    if setup['status'] != 'ready':
        return dict(status=setup['status'], scientific_decision='abstain')
    values = np.asarray(earlier, float)
    if values.shape != (setup['cut'],):
        raise ValueError('complete earlier observations only required')
    whitened, checkpoint = setup['operator'].apply_block(values, first_epoch=0)
    calibration = whitened[setup['first']:]
    estimate = setup['estimation'] @ (setup['training_basis'].T @ calibration)
    error = calibration - setup['calibration'] @ estimate
    variance = float(error @ error) / setup['training_dof']
    if not np.isfinite(variance) or variance <= 0.0:
        return dict(status='unavailable_training_scale', scientific_decision='abstain')
    return dict(status='ready', setup=setup, parameter_estimate=estimate,
                conditional_innovation_mean=setup['future_design'] @ estimate,
                checkpoint=checkpoint, training_variance_scale=variance, later_observations_used=False)


def score(forecast, later):
    if forecast['status'] != 'ready':
        return dict(status=forecast['status'], scientific_decision='abstain')
    setup = forecast['setup']
    mean = forecast['conditional_innovation_mean']
    values = np.asarray(later, float)
    if values.shape != mean.shape:
        raise ValueError('complete later observation coordinates required')
    whitened, _ = setup['operator'].apply_block(values, first_epoch=setup['training_epochs'],
                                                state=forecast['checkpoint'])
    residual = _adjust((whitened - mean)[:, None], setup['uncertainty'])[:, 0]
    basis = setup['contrast_basis']
    direction_coords = basis.T @ residual
    remainder = residual - basis @ direction_coords
    contrast = float(direction_coords @ direction_coords)
    orthogonal = float(remainder @ remainder)
    rank = basis.shape[1]
    parts = len(residual) - rank, setup['training_dof']
    variance = forecast['training_variance_scale']
    return dict(status='scored', contrast_coordinates=rank, orthogonal_coordinates=parts[0],
                training_dof=parts[1], training_variance_scale=variance,
                contrast_squared_error=contrast, orthogonal_squared_error=orthogonal,
                contrast_f=contrast / (rank * variance) if rank else None,
                orthogonal_f=orthogonal / (parts[0] * variance),
                contrast_reference=f.ppf([.025, .975], rank, parts[1]).tolist() if rank else None,
                orthogonal_reference=f.ppf([.025, .975], *parts).tolist(),
                scientific_decision='abstain', aircraft_coverage_established=False)
