"""Known-answer checks for the saved matched-field pitch comparison."""

import pytest

from lll.ilvis0_gyro_group_replay import GRID, MODELS, REMOVALS, differences, summarize


def test_matched_field_uses_the_disc_projection():
    pose = (0., 0., 0.)
    base_rates = dict(zip(MODELS, (5., 8., 0.), strict=True))
    field = dict(zip(MODELS, (-3., -3., -6.), strict=True))
    rates = {(pose, removal, model): base_rates[model]-removal*field[model]
             for model in MODELS for removal in REMOVALS}
    assert differences(rates, pose, 0., 5.) == (2., 11., 3.)
    assert differences(rates, pose, .5, 5.) == (-2.5, 6.5, 3.)
    rates[(pose, .5, 'flat_still')] += 1.
    with pytest.raises(ValueError, match='not affine'):
        differences(rates, pose, .5, 5.)


def test_group_specific_choices_can_reverse_a_shared_assumptions_result():
    scores = {'a': [-3., 6.] * 40 + [6.],
              'b': [6., -3.] * 40 + [-3.],
              'c': [1.] * len(GRID)}
    report = summarize(scores)
    assert report['same_assumptions_range_dph'] == [1., 1.]
    assert report['group_specific_assumptions_range_dph'] == [-3., 6.]
    assert report['positive_in_all_settings'] == 1
