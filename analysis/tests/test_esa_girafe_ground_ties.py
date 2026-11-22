# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from lll.esa_girafe import ForceSample
from lll.esa_girafe_ground_ties import force_summary, height_adjusted_reference


def test_reference_height_adjustment_uses_sensor_height():
    assert height_adjusted_reference(982000.0, 107.6, 100.0, 1.6) == pytest.approx(9.819981484)


def test_mean_vector_magnitude_differs_from_mean_magnitude_when_orientation_changes():
    samples = [ForceSample(0., (1., 0., 0.), .02, 20.), ForceSample(1., (0., 1., 0.), .02, 20.)]
    summary = force_summary(samples, stop_start=0.)
    assert summary['mean_vector_magnitude_mps2'] == pytest.approx(2**-.5)
    assert summary['mean_sample_magnitude_mps2'] == pytest.approx(1.)
    assert summary['mean_atom_axis_mps2'] == pytest.approx(0.)
