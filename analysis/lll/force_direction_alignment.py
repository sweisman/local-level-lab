# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fit a proper common-frame rotation on earlier unit force directions."""


def direction_pair_angles_deg(vectors):
    """Return separation angles for every unordered pair, in row order."""
    import numpy as np
    from .esa_gyro_force_direction import angles

    unit = unit_vectors(vectors)
    if len(unit) < 2:
        raise ValueError('at least two force directions required')
    first, second = np.triu_indices(len(unit), k=1)
    return np.rad2deg(angles(unit[first], unit[second]))


def aligned_direction_scores(reference, measured, *, training):
    import numpy as np
    from .esa_gyro_force_direction import angles

    target, actual = (np.asarray(v, dtype=float) for v in (reference, measured))
    if (target.ndim != 2 or target.shape != actual.shape or target.shape[1] != 3
            or type(training) is not int or not 2 <= training < len(target)
            or not np.isfinite([target, actual]).all()):
        raise ValueError('matched three-axis unit-direction training and forecast support required')
    target, actual = unit_vectors(target), unit_vectors(actual)
    result, rotation = fit_unit_rotation(target[:training], actual[:training])
    if rotation is None:
        return result
    errors = np.rad2deg(angles(target @ rotation.T, actual))
    return result | dict(angular_errors_deg=errors.tolist(),
        training_rms_deg=float(np.sqrt(np.mean(errors[:training]**2))),
        later_rms_deg=float(np.sqrt(np.mean(errors[training:]**2))))


def unit_vectors(vectors):
    import numpy as np

    vectors = np.asarray(vectors, float)
    if vectors.ndim != 2 or vectors.shape[1] != 3 or not len(vectors) or not np.isfinite(vectors).all():
        raise ValueError('finite three-axis force vectors required')
    norms = np.linalg.norm(vectors, axis=1)
    if np.any(norms <= 0) or not np.isfinite(norms).all():
        raise ValueError('force directions must be nonzero and normalizable')
    return vectors / norms[:, None]


def fit_unit_rotation(a, b):
    """Return the least-squares proper rotation on already normalized vectors."""
    import numpy as np

    ratios = []
    for vectors in (a, b):
        # A rotation about a common direction has zero information.
        gram = len(a)*np.eye(3) - vectors.T @ vectors
        information = np.linalg.eigvalsh(gram)
        ratios.append(max(0., float(information[0]/information[-1])))
    result = dict(reference_rotation_information_ratio=ratios[0], measured_rotation_information_ratio=ratios[1])
    if min(ratios) <= 1e-10:
        return result | dict(status='unresolved_alignment'), None
    u, singular, vt = np.linalg.svd(b.T @ a)
    signs = np.array([1., 1., np.linalg.det(u @ vt)])
    rotation = (u * signs) @ vt
    return result | dict(status='scored', rotation_reference_to_measured=rotation.tolist(),
                         alignment_singular_values=singular.tolist()), rotation
