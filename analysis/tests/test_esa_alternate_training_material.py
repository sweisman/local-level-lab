# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-coordinate transfer preserves the intended local displacement."""

import math

import pytest

from lll.esa_alternate_training_material import aligned_coordinates
from lll.esa_parallel_gnss import relative_neu


def test_aligned_coordinates_round_trip_in_local_chart():
    reference=dict(latitude_deg=64.,longitude_deg=-51.,height_m=1500.)
    latitude,longitude,height=aligned_coordinates(reference,[.1,-.2,.03])
    actual=relative_neu(reference,dict(latitude_deg=latitude,
                                       longitude_deg=longitude,height_m=height))
    assert actual==pytest.approx([.1,-.2,.03],abs=2e-8)


def test_invalid_displacement_rejected():
    reference=dict(latitude_deg=64.,longitude_deg=-51.,height_m=1500.)
    with pytest.raises(ValueError,match='finite'):
        aligned_coordinates(reference,[math.nan,0.,0.])
    with pytest.raises(ValueError,match='three-axis'):
        aligned_coordinates(reference,[0.,0.])
