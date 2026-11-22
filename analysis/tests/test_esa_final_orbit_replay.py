# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
from types import SimpleNamespace

import pytest

from lll.esa_final_orbit_replay import (
    _NAV, _OBS, BASELINE, ORBIT, SCOPE, evaluate, interpolate_orbit,
)


def test_interpolation_matches_a_known_degree_seven_polynomial():
    def position(t):
        u = t / 900
        return (2.0 + u**7 / 100, 4.0 - u**4, -5.0 + u**3)

    knots = {i * 900: position(i * 900) for i in range(-3, 5)}
    assert interpolate_orbit(knots, 387.3) == pytest.approx(position(387.3), abs=1e-11)
    assert interpolate_orbit(knots, 0.) == knots[0]
    del knots[1800]
    with pytest.raises(ValueError, match='missing'):
        interpolate_orbit(knots, 387.3)


def test_one_epoch_meets_runtime_accounting_and_result_contract():
    root = Path(__file__).resolve().parents[2]
    paths = dict(observations=_OBS, navigation=_NAV, baseline=BASELINE, orbit=ORBIT)
    if not all((root / path).is_file() for path in paths.values()):
        pytest.skip('sealed recording 187 products are required for this check')

    charged = []
    saved = {}

    def reserve(*, bound_calls, bound_steps):
        charged.append((bound_calls, bound_steps))

    context = SimpleNamespace(
        manifest={'scope': SCOPE}, input_path=lambda key: root / paths[key], charge=reserve,
        save_bytes=lambda name, data: saved.update({name: data}),
    )
    result = evaluate({'payload': dict(start=1040, end=1041)}, context)
    assert charged == [(1, 5)]
    assert result == dict(passed=True, epochs=1, passing=1, scientific_decision='abstain')
    assert b'final_minus_broadcast_neu_m' in saved['orbit-epochs.json']
