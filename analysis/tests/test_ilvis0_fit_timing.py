"""Timing must describe complete generated fits without changing their result."""

import pytest


def _ticks(*points):
    values = iter(points)
    return lambda: next(values)


def test_timer_excludes_kernel_compilation_and_forecast_from_fit_cpu():
    from lll.ilvis0_fit_timing import measure_variant

    saved = []

    def calculate(spec, recipe, *, kernel_factory, save, **_):
        kernel_factory(0.)
        save('fit.json', {'converged': True})
        save('forecast.json', {'epochs': 3})
        return {'result': 7}

    result, timing = measure_variant(
        calculate, {}, {}, kernel_factory=lambda _: ('kernel', 'tangent', {}),
        reserve=lambda **_: None, reserve_construction=lambda **_: None,
        save=lambda name, value: saved.append((name, value)),
        check_continue=lambda: None,
        tick=_ticks((10, 20), (20, 30), (30, 50), (45, 70)))
    assert result == {'result': 7}
    assert saved == [('fit.json', {'converged': True}),
                     ('forecast.json', {'epochs': 3})]
    assert timing == {'complete_cpu_ns': 35, 'complete_wall_ns': 50,
                      'fit_cpu_ns': 10, 'fit_wall_ns': 20}


@pytest.mark.parametrize('failure', ['missing_fit', 'duplicate_fit', 'fit_before_kernel'])
def test_timer_rejects_incomplete_or_misordered_fit_markers(failure):
    from lll.ilvis0_fit_timing import measure_variant

    def calculate(spec, recipe, *, kernel_factory, save, **_):
        if failure == 'fit_before_kernel':
            save('fit.json', {})
        kernel_factory(0.)
        if failure != 'missing_fit':
            save('fit.json', {})
        if failure == 'duplicate_fit':
            save('fit.json', {})
        return {}

    with pytest.raises(ValueError, match='fit timing'):
        measure_variant(
            calculate, {}, {}, kernel_factory=lambda _: None,
            reserve=lambda **_: None, reserve_construction=lambda **_: None,
            save=lambda *_: None, check_continue=lambda: None,
            tick=_ticks((10, 20), (20, 30), (30, 50), (45, 70)))


def test_timer_rejects_nonpositive_elapsed_time():
    from lll.ilvis0_fit_timing import measure_variant

    def calculate(spec, recipe, *, kernel_factory, save, **_):
        kernel_factory(0.)
        save('fit.json', {})
        return {}

    with pytest.raises(ValueError, match='positive'):
        measure_variant(
            calculate, {}, {}, kernel_factory=lambda _: None,
            reserve=lambda **_: None, reserve_construction=lambda **_: None,
            save=lambda *_: None, check_continue=lambda: None,
            tick=_ticks((10, 20), (20, 30), (20, 50), (45, 70)))


def test_timed_pair_preserves_matched_result_and_records_two_variants():
    from lll.ilvis0_fit_timing import timed_pair
    from lll.ilvis0_hybrid_long_fit_study import recipe, tasks

    r = recipe()
    spec = tasks(r)[0]['payload']
    saved = {}

    def calculate(spec, recipe, *, kernel_factory, save, **_):
        kernel_factory(0.)
        save('fit.json', {'converged': True})
        save('input-binding.json', {'same': True})
        save('scoring-observations.json', {'same': True})
        save('scores.json', {'errors_neu_m': [[0., 0., 0.]]})
        return dict(spec, converged=True, passed=True,
                    all_columns_retained=True, training_cost=1., native_calls=1)

    result = timed_pair(
        spec, r, calculate=calculate,
        factories={'wide': lambda _: None, 'hybrid': lambda _: None},
        reserve=lambda **_: None, reserve_construction=lambda **_: None,
        save=lambda name, value: saved.__setitem__(name, value),
        check_continue=lambda: None)
    assert result['passed'] is True
    assert result['comparison']['maximum_prediction_difference_m'] == 0.
    assert result['timing'] == saved['whole-fit-timing.json']
    assert set(result['timing']) == {'wide', 'hybrid'}
    assert all(all(value > 0 for value in times.values())
               for times in result['timing'].values())
