# SPDX-License-Identifier: AGPL-3.0-or-later
"""One proper alignment for several predictions of the same force directions."""

from .force_direction_alignment import fit_unit_rotation, unit_vectors


def unit_references(paths):
    import numpy as np

    return np.asarray([unit_vectors(path) for path in paths])


def pooled_alignment(reference, measured):
    import numpy as np

    if (reference.ndim != 3 or reference.shape[1:] != measured.shape
            or not len(reference) or measured.ndim != 2 or measured.shape[1] != 3):
        raise ValueError('ordered references must share one force support')
    target = reference.reshape(-1, 3)
    actual = np.tile(measured, (len(reference), 1))
    _, rotation = fit_unit_rotation(target, actual)
    if rotation is None:
        raise ValueError('earlier pooled rotation numerically unidentified')
    prediction = target @ rotation.T
    return rotation, actual-prediction, prediction


def pooled_tangent(reference, measured, derivative):
    import numpy as np

    _, residual, aligned = pooled_alignment(reference, measured)
    return residual, np.tile(derivative, (len(reference), 1, 1)), aligned


def source_scores(references, measured, *, included, training):
    import numpy as np
    from .esa_gyro_force_direction import angles

    earlier = measured[:training]
    rotation, residual, _ = pooled_alignment(unit_references(references[k][:training] for k in included), earlier)
    earlier_loss = float(np.sum(residual**2)/len(residual))
    scores = {}
    for key, values in references.items():
        reference = unit_vectors(values) @ rotation.T
        results = np.rad2deg(angles(reference[training:], measured[training:]))
        scores[key] = dict(earlier_mean_squared_chord=float(np.mean(np.sum((reference[:training]-earlier)**2, axis=1))),
                           later_rms_deg=float(np.sqrt(np.mean(results**2))), later_errors_deg=results.tolist())
    return earlier_loss, scores
