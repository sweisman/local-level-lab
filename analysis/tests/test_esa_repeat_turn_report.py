import pytest

from lll import esa_repeat_turn_execution as design
from lll.esa_repeat_turn_release import primary_starts


def test_repeat_turn_report_retains_every_case_and_compares_scores_within_each():
    from lll.esa_repeat_turn_report import render, summary

    outcomes = {task['identity']: {'converged': False} for task in design.tasks()}
    first, second, third = (task['identity'] for task in design.tasks()[:3])
    outcomes[first] = {'converged': True, 'cost': 1., 'forecast_sha256': 'a'*64}
    outcomes[second] = {'converged': True, 'cost': 2., 'forecast_sha256': 'b'*64}
    outcomes[third] = {'converged': True, 'cost': 1.}
    primary = primary_starts(outcomes)
    windows = {index: {'window': {'signed_course_change_deg': -5.}} for index in design.WINDOWS}
    scored = {first: dict(forecast_sha256='a'*64, law='increment', physical_rms_neu_m=[3., 4., 12.],
                          horizontal_rms_m=5., scores={
                              name: {'negative_log_score': score} for name, score in
                              zip(('native', 'steady', 'turn', 'both'), (-2., -1., -4., -3.), strict=True)
                          })}
    report = summary(outcomes=outcomes, primary=primary, scores=scored, windows=windows)
    assert len(report) == 8
    assert report[0]['rms_3d_m'] == 13.
    assert report[0]['nll_change'] == {'steady': 1., 'turn': -2., 'both': -1.}
    assert report[1]['state'] == 'primary_forecast_missing'
    assert report[2]['state'] == 'no_converged_start'
    table = [line for line in render(report, outcomes, 'c'*64, 'd'*64).splitlines()
             if line.startswith('| ')]
    assert len(table) == 10
    assert all(line.count('|') == 14 for line in table)
    assert 'Selected forecast unavailable' in table[3]
    assert 'Neither start converged' in table[4]
    with pytest.raises(ValueError, match='exactly the released'):
        summary(outcomes=outcomes, primary=primary, scores={**scored, second: scored[first]}, windows=windows)
