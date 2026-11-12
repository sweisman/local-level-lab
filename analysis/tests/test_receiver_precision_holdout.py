# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact same-receiver timing and descriptive normalized-error controls."""

import math

import pytest


def _rows():
    origin = 100000.
    epochs = []
    positions = []
    training = []
    for index in range(6):
        role = 'training' if index < 2 else 'prediction'
        epochs.append(dict(epoch=index, role=role, time_s=float(index),
                           north_direct_error_m=float(index),
                           east_direct_error_m=0.,
                           up_direct_error_m=-float(index)))
        latitude = 42. + index * .001
        longitude = -120. + index * .001
        height = 1000. + index
        positions.append(dict(gps_week='1800',
                              gps_milliseconds=str(round((origin + index + 15) * 1000)),
                              latitude_deg=str(latitude),
                              longitude_deg=str(longitude),
                              ellipsoid_height_m=str(height),
                              reported_sigma_north_m='2',
                              reported_sigma_east_m='3',
                              reported_sigma_up_m='4'))
        if index < 2:
            training.append([math.radians(latitude),
                             math.radians(longitude), height])
    return origin, epochs, positions, training


def test_exact_receiver_join_checks_earlier_coordinates_and_later_support():
    from lll.receiver_precision_holdout import join_epochs, summarize

    origin, epochs, positions, training = _rows()
    joined = join_epochs(epochs, positions,
                         origin_utc_week_s=origin,
                         expected_gps_week=1800,
                         training_coordinates=training)
    assert len(joined) == 6
    assert joined[0]['gps_milliseconds'] == 100015000
    assert joined[-1]['role'] == 'prediction'
    report = summarize(joined)
    assert report['training_epochs'] == 2
    assert report['prediction_epochs'] == 4
    assert report['north']['normalized_rms'] == math.sqrt(
        (2**2 + 3**2 + 4**2 + 5**2) / 4) / 2
    assert report['height']['reported_sigma_median_m'] == 4
    assert report['scientific_decision'] == 'abstain'


def test_receiver_join_rejects_missing_epoch_and_wrong_earlier_position():
    from lll.receiver_precision_holdout import join_epochs

    origin, epochs, positions, training = _rows()
    with pytest.raises(ValueError, match='complete exact receiver support'):
        join_epochs(epochs, positions[:-1], origin_utc_week_s=origin,
                    expected_gps_week=1800,
                    training_coordinates=training)
    training[0][0] += 1e-5
    with pytest.raises(ValueError, match='same-receiver coordinate'):
        join_epochs(epochs, positions, origin_utc_week_s=origin,
                    expected_gps_week=1800,
                    training_coordinates=training)
