# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed feasible steps and physical tangent remainder for a generated pilot."""


STEPS = (.05, .10, .20)


def points(fitted, weak, *, steps=STEPS):
    """Choose a sign using only the fixed normalized calibration box."""
    import numpy as np

    origin = np.asarray(fitted, dtype=float)
    direction = np.asarray(weak, dtype=float)
    if (steps != STEPS or origin.ndim != 1 or direction.shape != origin.shape
            or not 1 <= len(origin) <= 27
            or not np.all(np.isfinite(origin))
            or not np.all(np.isfinite(direction))
            or np.any(np.abs(origin) > 1)
            or not np.isclose(np.linalg.norm(direction), 1., rtol=0, atol=1e-9)):
        raise ValueError('fixed steps, unit direction and in-box fit required')
    for sign in (-1, 1):
        trial = np.stack([origin] + [origin + sign*step*direction
                                     for step in steps])
        if np.all(np.abs(trial) <= 1 + 1e-12):
            return dict(sign=sign, steps=(0.,) + steps, points=trial)
    raise ValueError('fixed steps do not fit either box direction')


def compare(base, shifted, jacobian, delta, *, training_epochs):
    """Compare nonlinear coordinate change with a native baseline tangent."""
    import numpy as np
    from .airquantumgrav_truth import A, E2

    origin = np.asarray(base, dtype=float)
    candidate = np.asarray(shifted, dtype=float)
    derivative = np.asarray(jacobian, dtype=float)
    displacement = np.asarray(delta, dtype=float)
    if (origin.ndim != 2 or origin.shape[1] != 3 or
            candidate.shape != origin.shape or
            derivative.shape != (origin.size, len(displacement)) or
            displacement.ndim != 1 or not len(displacement) or
            type(training_epochs) is not int or
            not 1 <= training_epochs < len(origin) or
            any(not np.all(np.isfinite(item)) for item in
                (origin, candidate, derivative, displacement)) or
            np.any(abs(origin[:, 0]) >= np.pi/2)):
        raise ValueError('complete matched path, tangent and training split required')
    difference = candidate - origin
    difference[:, 1] = (difference[:, 1] + np.pi) % (2*np.pi) - np.pi
    linear = (derivative @ displacement).reshape(origin.shape)
    linear[:, 1] = (linear[:, 1] + np.pi) % (2*np.pi) - np.pi
    phi = origin[:, 0]
    height = origin[:, 2]
    q = 1 - E2*np.sin(phi)**2
    metric = np.column_stack((A*(1-E2)/q**1.5 + height,
                              (A/np.sqrt(q)+height)*np.cos(phi),
                              np.ones(len(origin))))
    actual_neu = difference*metric
    remainder_neu = (difference-linear)*metric

    def rms(values):
        return float(np.sqrt(np.mean(np.sum(values[:, :2]**2, axis=1))))

    return dict(training_change_horizontal_rms_m=rms(
                    actual_neu[:training_epochs]),
                later_change_horizontal_rms_m=rms(
                    actual_neu[training_epochs:]),
                training_remainder_horizontal_rms_m=rms(
                    remainder_neu[:training_epochs]),
                later_remainder_horizontal_rms_m=rms(
                    remainder_neu[training_epochs:]),
                training_change_neu_rms_m=np.sqrt(np.mean(
                    actual_neu[:training_epochs]**2, axis=0)).tolist(),
                later_change_neu_rms_m=np.sqrt(np.mean(
                    actual_neu[training_epochs:]**2, axis=0)).tolist(),
                later_remainder_neu_rms_m=np.sqrt(np.mean(
                    remainder_neu[training_epochs:]**2, axis=0)).tolist())
