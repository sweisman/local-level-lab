# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.airquantumgrav_withheld_receiver import generate_full_report
from lll.airquantumgrav_error_policy import build
from lll.airquantumgrav_weighted_controls import fixture_rows
from lll.measurement_noise import receiver_errors


def _fixture():
    times = np.arange(1., 9.)
    coordinates = np.column_stack((np.full(8, np.radians(55.)),
                                   np.radians(-40.)+times*1e-5,
                                   np.full(8, 2000.)))
    clean = fixture_rows(coordinates, times)
    prefix = build(clean[:4], policy_id='reported-short-v1')
    error = receiver_errors(prefix.times, prefix.spec, seed=33,
                            maximum_epochs=4, transforms=prefix.transforms)
    training = [dict(row, latitude_deg=row['latitude_deg']+np.degrees(e[0]),
                     longitude_deg=row['longitude_deg']+np.degrees(e[1]),
                     height_m=row['height_m']+e[2])
                for row,e in zip(clean[:4], error, strict=True)]
    return coordinates,times,training


def test_later_receiver_generation_reproduces_exact_earlier_stream():
    coordinates,times,training = _fixture()
    result = generate_full_report(coordinates, times, training,
                                  policy_id='reported-short-v1', seed=33)
    assert result['training_prefix_exact'] is True
    assert result['later_observations_used_for_training'] is False
    assert result['rows'][:4] == training
    assert len(result['rows']) == 8
    changed = coordinates.copy(); changed[4:, 2] += 50.
    second = generate_full_report(changed, times, training,
                                  policy_id='reported-short-v1', seed=33)
    assert second['rows'][:4] == training
    assert second['rows'][4:] != result['rows'][4:]


def test_changed_training_receiver_is_rejected():
    coordinates,times,training = _fixture()
    training[0]['height_m'] += .01
    with pytest.raises(ValueError, match='prefix'):
        generate_full_report(coordinates,times,training,
                             policy_id='reported-short-v1',seed=33)


def test_full_receiver_draw_charges_declared_variates_before_generation():
    coordinates,times,training = _fixture()
    charged = []
    result = generate_full_report(
        coordinates,times,training,policy_id='reported-short-v1',seed=33,
        reserve=lambda **work: charged.append(work))
    assert charged == [dict(noise_normal_variates=6*len(times)+6)]
    assert result['rows'][:4] == training
