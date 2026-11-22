# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.joint_score_abstention import ARMS, assess


def _scores(rotating, still, disc):
    return {key:dict.fromkeys(ARMS, value) for key,value in zip(
        ('sphere_rotating','sphere_still','flat_still'), (rotating,still,disc), strict=True)}


def test_underdispersion_can_withhold_support_but_cannot_exclude_a_competitor():
    assert assess(_scores(120., 500., 0.), epochs=40)['shape'] == 'abstain'
    assert assess(_scores(0., 500., 500.), epochs=40)['shape_reason'] == 'no_adequate_candidate'


def test_support_is_a_union_and_field_is_assessed_after_shape():
    rows = _scores(120., 500., 500.)
    assert assess(rows, epochs=40)['field'] == 'specified'
    rows['sphere_still'][ARMS[0]] = 120.
    answer = assess(rows, epochs=40)
    assert answer['shape'] == 'globe' and answer['field'] == 'abstain'
    rows['flat_still'][ARMS[-1]] = 120.
    assert assess(rows, epochs=40)['shape_reason'] == 'both_families_compatible'


def test_accuracy_veto_does_not_reclassify_other_model_as_adequate():
    rows = _scores(120., 500., 500.)
    physical = {key:dict.fromkeys(ARMS, key != 'sphere_rotating') for key in rows}
    result = assess(rows, epochs=40, physical=physical)
    assert result['shape'] == 'abstain'
    assert result['compatible_models'] == ['sphere_rotating']


def test_missing_scores_never_issue_a_decision():
    assert assess({}, epochs=40)['shape_reason'] == 'incomplete'
    rows = _scores(120., 500., 500.)
    rows['flat_still'][ARMS[0]] = -1.
    with pytest.raises(ValueError, match='nonnegative'):
        assess(rows, epochs=40)
