# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_conditioned_path_must_bind_exact_raw_path_clock_and_law():
    from lll.esa_matched_conditioning import matched_positions

    coordinates = [[0., 0., float(t)] for t in range(320)]
    raw = dict(times_s=list(range(320)), coordinates=coordinates, training_epochs=200,
               prediction_epochs=120, prediction_receiver_positions_used=False)
    saved = dict(law='increment', times_s=raw['times_s'], raw_coordinates=coordinates[200:],
                 conditional_receiver_mean=coordinates[200:], training_epochs=200,
                 prediction_epochs=120, later_receiver_values_used=False, optimization_performed=False)
    assert matched_positions(raw, saved, 200, 'increment') == (coordinates[200:], coordinates[200:])
    with pytest.raises(ValueError, match='same earlier'):
        matched_positions(raw, saved, 200, 'point')
    saved['times_s'] = list(range(1, 321))
    with pytest.raises(ValueError, match='same earlier'):
        matched_positions(raw, saved, 200, 'increment')
