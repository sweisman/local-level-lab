# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from lll import esa_girafe_force_contrast as contrast
from lll.esa_girafe_force_contrast import earlier_offset_difference


def test_offset_uses_only_earlier_differences():
    observed = [10., 12., 24., 29.]
    predicted = [8., 8., 20., 20.]
    offset, later = earlier_offset_difference(observed, predicted, earlier=2)
    assert offset == 3.
    assert later.tolist() == pytest.approx([1., 6.])


@pytest.mark.parametrize('left, right', [
    ([1., 2., 3.], [1., 2.]),
    ([1., 2., float('nan')], [1., 2., 3.]),
    ([1., 2.], [1., 2.]),
])
def test_offset_requires_finite_matched_training_and_later_values(left, right):
    with pytest.raises(ValueError):
        earlier_offset_difference(left, right, earlier=2)


def test_each_matched_support_is_charged_before_evaluation(monkeypatch):
    receipts = []
    evaluated = []

    def charge(**operation):
        assert operation == {'bound_calls': 1, 'bound_steps': 8*40}
        receipts.append(operation)

    def force(*args):
        assert len(receipts) == len(evaluated)//8+1
        evaluated.append(args)
        return 9.81

    monkeypatch.setattr(contrast, 'predicted_force_batch', force)
    rows = [dict(latitude_deg=64., longitude_deg=-20., height_m=2000.,
                 north_mps=20., east_mps=30., up_mps=0.) for _ in range(400)]
    results = contrast._source_predictions(rows, range(400), 11, charge)
    assert len(receipts) == 16 and len(evaluated) == 128
    assert all(len(values) == 16 for models in results.values() for values in models.values())
