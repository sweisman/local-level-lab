# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from audit_roll_proxy import compare, knot_bank_jumps
from lll.inference_policy import digest
from lll.trajectory import TRACK_VERSION, TrackReplay


def trajectory(longitudes):
    rows = [dict(t_s=t, latitude_deg=40+.002*t, longitude_deg=lon,
                 reported_altitude_m=11000, is_provider_estimate=False)
            for t, lon in zip([0., 30., 60., 90.], longitudes)]
    content = dict(version=TRACK_VERSION, mode='simulated_high_rate', rows=rows,
                   start_s=0., end_s=90., max_interval_s=90.)
    return TrackReplay({**content, 'trajectory_hash': digest(content)})


def test_linear_position_has_no_artificial_bank_jump():
    entries = knot_bank_jumps(trajectory([-75., -74.99, -74.98, -74.97]))
    assert len(entries) == 2
    assert max(abs(e['jump_deg']) for e in entries) < 1e-5


def test_c1_position_curve_can_imply_discontinuous_coordinated_bank():
    entries = knot_bank_jumps(trajectory([-75., -74.995, -74.98, -74.975]))
    assert len(entries) == 2
    assert max(abs(e['jump_deg']) for e in entries) > 1.


def test_scalar_comparison_is_an_explicit_diagnostic_not_a_science_decision():
    x = np.array([1., 2., 3., np.nan])
    result = compare(x, 2*x, np.ones(4, bool))
    assert result['samples'] == 3
    assert result['gain'] == 2
    assert result['explained_fraction'] == 1
    assert 'accepted_for_science' not in result
