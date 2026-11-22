# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
from types import SimpleNamespace

import pytest

from lll.esa_linked_floor_support import assess_box, certificate_terms


def test_slack_certificate_has_correct_signs_and_auxiliary_support():
    # On x + y <= 1, y in [-2, 3], earlier x <= 1/2 and score 2*x >= 3/2,
    # use floor weight 1/2 and disable the affine row to prove conflict.
    coefficient, offset = certificate_terms([(2, 2)], [(1, 1)], F(1, 2),
        F(3, 2), [[1, 1]], [1], [0], F(1, 2), [-2], [3])
    assert coefficient == [(0, 0)]
    assert offset == -F(1, 4)

    # With a unit weight on the affine row its y coefficient is -1,
    # so its support at y = -2 adds 2 to the original offset.
    coefficient, offset = certificate_terms([(2, 2)], [(1, 1)], F(1, 2),
        F(3, 2), [[1, 1]], [1], [1], F(1, 2), [-2], [3])
    assert coefficient == [(-1, -1)]
    assert offset == F(11, 4)


def test_certificate_rejects_negative_duals_and_preserves_intervals():
    with pytest.raises(ValueError, match='nonnegative'):
        certificate_terms([(1, 2)], [(3, 4)], 1, 2, [[1]], [1], [-1], 1, [], [])
    coeff, offset = certificate_terms([(1, 2)], [(3, 4)], 1, 2, [[1]], [1], [0], 1, [], [])
    assert coeff == [(-3, -1)]
    assert offset == -1


def test_subdivision_charges_complete_operations(monkeypatch):
    from lll import ilvis0_linked_directional

    monkeypatch.setattr(ilvis0_linked_directional, 'directional_bound',
        lambda model, lo, hi, weights: SimpleNamespace(hi=1 if hi[26]-lo[26] == 2 else -1))
    monkeypatch.setattr(ilvis0_linked_directional, '_linked_expression',
        lambda *args: SimpleNamespace(derivative=[SimpleNamespace(lo=0, hi=i) for i in range(27)]))
    charges = []

    def charge(**reservation):
        assert set(reservation) == {'bound_calls', 'bound_steps'}
        assert reservation['bound_calls'] == 1
        charges.append(reservation['bound_steps'])

    record = assess_box(SimpleNamespace(charge=charge), None,
        dict(lower=[-1.] * 27, upper=[1.] * 27), [(0, 0)] * 51, F(0))
    assert charges == [3, 2, 2, 2, 2]
    assert record['coverage']['children'] == 4
    assert record['excluded']
