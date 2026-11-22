"""Source-bound controls for the two-start generated method check."""

import math

import pytest

from lll.airquantumgrav_truth import A, DISC_RADIUS
from lll.ilvis0_start_equivalence_study import (
    assess_group, inspect, pair, prepare, qualification_sources,
    recipe, required_tests, tasks, world_coordinates)


def test_two_start_study_covers_all_models_and_profiles_with_finite_limits():
    settings = recipe()
    cases = tasks(settings)
    assert len(cases) == 12
    assert settings['starts'] == 2
    assert settings['workers']*settings['threads'] == 4
    assert settings['relative_cost_tolerance'] == 1e-8
    assert {row['payload']['model'] for row in cases} == {
        'sphere_rotating', 'sphere_still', 'flat_still'}
    assert {row['payload']['profile'] for row in cases} == {False, True}
    assert {row['payload']['start'] for row in cases} == {0, 1}
    assert len({row['identity'] for row in cases}) == 12
    assert all(row['limits']['native_calls'] == 402 for row in cases)
    assert sum(row['limits']['packet_visits'] for row in cases) == 9034872000


def test_forecast_conversion_uses_each_candidate_metric_in_metres():
    sphere = world_coordinates([[0., 0., 0.], [0., 0., 2.]], 'sphere_rotating')
    disc = world_coordinates([[0., 0., 0.]], 'flat_still')
    assert sphere[0] == pytest.approx([A, 0., 0.])
    assert math.dist(sphere[0], sphere[1]) == pytest.approx(2.)
    assert disc[0] == pytest.approx([DISC_RADIUS*math.pi/2, 0., 0.])
    with pytest.raises(ValueError, match='finite nonpolar'):
        world_coordinates([[math.pi/2, 0., 0.]], 'sphere_still')


def test_group_checks_cross_start_paths_without_later_receiver_positions():
    base = dict(input_binding={'training_sha256': 'a'*64}, times_s=[1., 2.],
                passed=True)
    small = [[0., 0., 0.], [0., 0., 0.]]
    moved = [[0., 0., 0.], [0., 0., .003]]
    group = {'wide': {0: dict(base, training_cost=10., forecast=small),
                      1: dict(base, training_cost=10.+1e-9, forecast=moved)},
             'hybrid': {0: dict(base, training_cost=10.+1e-9, forecast=small),
                        1: dict(base, training_cost=10., forecast=moved)}}
    report = assess_group(group, model='sphere_rotating', settings=recipe())
    assert report['equivalent']
    assert report['reference_primary'] == 0
    assert report['candidate_primary'] == 1
    assert report['cross_start_maximum_m'] == pytest.approx(.003)
    group['hybrid'][1]['times_s'] = [1., 3.]
    with pytest.raises(ValueError, match='binding'):
        assess_group(group, model='sphere_rotating', settings=recipe())


def test_preparation_requires_source_bound_qualification(tmp_path):
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None)
    assert not list(tmp_path.iterdir())


def test_second_start_pair_uses_existing_matched_fit_runner():
    settings = recipe()
    second = next(row['payload'] for row in tasks(settings)
                  if row['payload']['start'] == 1)
    seen = []
    def calculate(spec, settings, *, kernel_factory, reserve,
                  reserve_construction, save, check_continue):
        seen.append(spec['start'])
        save('input-binding.json', {'source': 'same'})
        save('scoring-observations.json', {'times': [1.]})
        save('scores.json', {'errors_neu_m': [[0., 0., 0.]]})
        return dict(spec, passed=True, converged=True,
                    all_columns_retained=True, training_cost=10.)
    report = pair(second, settings, calculate=calculate,
                  factories={'wide': lambda anchor: None,
                             'hybrid': lambda anchor: None},
                  reserve=lambda **work: None,
                  reserve_construction=lambda **work: None,
                  save=lambda name, value: None,
                  check_continue=lambda: None)
    assert seen == [1, 1]
    assert report['passed']


def test_source_binding_includes_new_method_and_recovery_checks():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    source = set(qualification_sources(root))
    assert {'analysis/lll/ilvis0_start_equivalence.py',
            'analysis/lll/ilvis0_start_equivalence_study.py',
            'analysis/tests/test_ilvis0_start_equivalence_study.py',
            'docs/mixed-tangent-hybrid/START_EQUIVALENCE_STUDY_PLAN.md'} <= source
    required = set(required_tests())
    assert 'test_reboot_resume_skips_sealed_and_preserves_charges' in required
    assert 'test_group_checks_cross_start_paths_without_later_receiver_positions' in required


def test_old_one_start_study_cannot_be_reinterpreted_as_two_start_release():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    with pytest.raises(ValueError, match='unchanged generated paired-fit scope'):
        inspect(root, 'data/model-declared-paired-fit-20261115-v2')
