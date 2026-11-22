import numpy as np
import pytest

from lll.ilvis0_matched_extension_force_witness import corrected_tracks, force_deficit


def test_force_witness_keeps_the_training_gain_in_the_gap():
    row = dict(measured_lower_mps2=11., required_upper_mps2=10.)
    assert force_deficit(row, .1) <= 0.
    assert force_deficit(row, 0.) == pytest.approx(1.)


def test_force_witness_uses_one_shared_local_shift_at_each_epoch():
    shift = np.array([[.1, -.2, .3], [.4, -.5, .6]])
    tracks = {'a': np.ones((2, 3)), 'b': np.arange(6, dtype=float).reshape(2, 3)}
    metrics = {'a': np.full((2, 3), 2.), 'b': np.full((2, 3), 3.)}
    adjusted = corrected_tracks(tracks, metrics, shift)
    for name, coords in tracks.items():
        np.testing.assert_allclose((adjusted[name]-coords)*metrics[name], shift, rtol=0., atol=2e-15)
