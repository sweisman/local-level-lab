# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from lll.esa_relative_clock_replay import (
    INPUTS, SCOPE, _anchors, _load, evaluate, interpolate_clock, relative_differences,
)


def test_clock_interpolation_preserves_knots_and_rejects_missing_samples():
    samples = {0: 20e-9, 30: 50e-9}
    assert interpolate_clock(samples, 0) == 20e-9
    assert interpolate_clock(samples, 15) == pytest.approx(35e-9)
    with pytest.raises(ValueError, match='clock sample'):
        interpolate_clock(samples, 35)


def test_clock_differences_ignore_common_epoch_shift_and_anchor_constant():
    def compare(reference_shift, fixed_satellite_offset):
        anchor = relative_differences({1: 4., 3: 6. + fixed_satellite_offset})
        later = relative_differences({1: 9. + reference_shift,
                                      3: 13. + reference_shift + fixed_satellite_offset})
        return {prn: later[prn] - anchor[prn] for prn in later}

    assert compare(0., 0.) == compare(65., -110.) == {1: 0., 3: 2.}


def test_one_epoch_replays_with_two_complete_runtime_reservations(tmp_path):
    root = Path(__file__).resolve().parents[2]
    paths = {key: root / path for key, path in INPUTS.items()}
    if not all(path.is_file() for path in paths.values()):
        pytest.skip('sealed recording 187 products are required for this check')
    records, baseline, navigation, _, clocks = _load(lambda key: paths[key].read_bytes())
    paths['anchors'] = tmp_path / 'anchors.json'
    paths['anchors'].write_text(json.dumps(_anchors(records, baseline, navigation, clocks)))

    charges, saved = [], {}

    def reserve(*, bound_calls, bound_steps):
        charges.append((bound_calls, bound_steps))

    context = SimpleNamespace(manifest={'scope': SCOPE}, input_path=paths.__getitem__, charge=reserve,
        save_bytes=lambda name, data: saved.update({name: data}))
    result = evaluate({'payload': dict(start=1040, end=1041)}, context)
    assert result == dict(passed=True, epochs=1, passing=1, scientific_decision='abstain')
    assert charges == [(1, 5), (1, 4)]
    row, = json.loads(saved['clock-epochs.json'])
    assert row['satellites'] == [
        prn for prn in baseline[-1]['dual_frequency']['used_satellites'] if prn != 17
    ]
