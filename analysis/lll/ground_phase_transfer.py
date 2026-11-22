# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check how a ground phase correction learned earlier transfers in time."""


def compare_transfer(aircraft, ground, *, training, withheld):
    import numpy as np

    air, station = np.asarray(aircraft, float), np.asarray(ground, float)
    if (air.ndim != 2 or station.shape != air.shape or not air.size
            or not np.isfinite(air).all() or not np.isfinite(station).all()):
        raise ValueError('finite matched phase residual arrays required')
    train, later = list(training), list(withheld)
    indices = train+later
    if (not train or not later or indices != sorted(set(indices)) or indices[0] < 0 or indices[-1] >= len(air)):
        raise ValueError('disjoint chronological training and withheld intervals required')
    early_ground = station[train].ravel()
    denominator = early_ground@early_ground
    if denominator <= 0:
        raise ValueError('earlier ground residual must have measurable variation')
    gain = float(air[train].ravel()@early_ground/denominator)

    def rms(values):
        return float(np.sqrt(np.mean(values**2)))

    def score(selected):
        a, g = air[selected], station[selected]
        return dict(no_ground_rms_m=rms(a), ground_rms_m=rms(g), unit_ground_rms_m=rms(a-g),
                    earlier_gain_rms_m=rms(a-gain*g))

    return dict(trained_gain=gain, training=score(train), withheld=score(later),
                per_interval=[score([index]) for index in range(len(air))])
