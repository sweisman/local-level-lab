# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from lll import ilvis0_recovery_plan as plan


def fixture():
    records = []
    for sid, complete in [('a', False), ('b', False), ('c', False), ('control', True)]:
        records.append(dict(segment_id=sid, cases=[dict(case_id=case, fits=[
            dict(model=model, converged=complete, normalized_parameters=[0., .5],
                 active_parameters=['x', 'y'], elapsed_s=40., evaluations=20)
            for model in ('sphere_rotating', 'sphere_still', 'flat_still')])
            for case in ('bias1_unsubtracted', 'bias1_profiled_removal')]))
    return records, ['a', 'b', 'c', 'control']


def test_tasks_keep_completed_references_and_finite_repeatability_allowance():
    rows, selected = fixture()
    rows[0]['cases'][0]['fits'][0]['converged'] = True
    result = plan.build(rows, selected)
    assert len(result['tasks']) == 26  # 17 unfinished + six control + three repeats
    assert result['maximum_native_sweeps'] == 26 * 602
    assert len(set(result['identities'])) == 26
    assert not any(t['role'] == 'recovery' and t['segment_id'] == 'a'
                   and t['model'] == 'sphere_rotating' and t['case_id'] == 'bias1_unsubtracted'
                   for t in result['tasks'])
    assert result['scientific_decision'] == 'abstain'
    assert result['observed_allowance_authorized'] is False


def test_repeats_are_selected_without_costs_or_preferences():
    rows, selected = fixture()
    one = plan.build(rows, selected)
    for r in rows:
        for c in r['cases']:
            for f in c['fits']:
                f['residual_sum_squares'] = -12345.
    two = plan.build(rows, selected)
    assert one == two


def test_noncompleted_control_is_rejected():
    rows, selected = fixture()
    rows[-1]['cases'][0]['fits'][0]['converged'] = False
    with pytest.raises(ValueError):
        plan.build(rows, selected)


def test_missing_saved_feasible_point_is_rejected():
    rows, selected = fixture()
    rows[0]['cases'][0]['fits'][0]['normalized_parameters'] = [2., 0.]
    with pytest.raises(ValueError):
        plan.build(rows, selected)


@pytest.mark.parametrize('selected', [['a', 'a', 'c', 'control'], ['a', 'b', 'control']])
def test_selection_scope_is_exact(selected):
    rows, _ = fixture()
    with pytest.raises(ValueError):
        plan.build(rows, selected)
