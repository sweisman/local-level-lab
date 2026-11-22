# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.shape_remainder_witness import declared_probes


def test_exact_replay_uses_only_the_declared_support_steps():
    rows = [dict(assumed_earlier_remainder=delta,
                 support={'sphere_still': dict(point=[0.03]*27, achieved=0.25)})
            for delta in (0., .001, .01, .1, 1.)]
    probes = declared_probes(rows, 'sphere_still')
    assert [(probe['delta'], probe['fraction']) for probe in probes] == [(0., 1.), (0., .98), (.1, 1.), (1., 1.)]
    assert probes[1]['point'] == pytest.approx([.03*.98]*27)
    assert probes[1]['affine_projection'] == pytest.approx(.25*.98)
