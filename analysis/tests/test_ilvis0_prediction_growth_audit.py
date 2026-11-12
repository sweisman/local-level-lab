"""Earlier-only primary selection and RMS growth must remain distinct."""

import pytest


def _result(cost, *, converged=True):
    return dict(segment_id='s', clock='header_elapsed', profile=False,
                model='sphere_rotating', training_cost=cost,
                converged=converged, passed=converged)


def test_primary_selection_uses_training_cost_and_ignores_failed_start():
    from lll.ilvis0_prediction_growth_audit import primary_results

    selected = primary_results([('failed', _result(0., converged=False)),
                                ('higher', _result(2.)),
                                ('lower', _result(1.))])
    assert len(selected) == 1
    assert selected[0][1] == 'lower'


def test_growth_ratio_rejects_zero_training_scale():
    from lll.ilvis0_prediction_growth_audit import AXES, ratios

    scores = dict(training={name: 2. for name in AXES},
                  prediction={name: 6. for name in AXES})
    assert set(ratios(scores).values()) == {3.}
    scores['training']['north_rms_m'] = 0.
    with pytest.raises(ValueError, match='earlier RMS'):
        ratios(scores)


def test_horizon_quarters_use_only_saved_withheld_epochs():
    from lll.ilvis0_prediction_growth_audit import horizon_quarters

    rows = [dict(epoch=0, time_s=0., role='training',
                 north_direct_error_m=900., east_direct_error_m=900.,
                 up_direct_error_m=900.)]
    for index, value in enumerate((1., 1., 2., 2., 3., 3., 4., 4.), 1):
        rows.append(dict(epoch=index, time_s=float(index), role='prediction',
                         north_direct_error_m=value,
                         east_direct_error_m=-value,
                         up_direct_error_m=0.))
    assert horizon_quarters(rows) == [
        dict(epochs=2, north_rms_m=1., east_rms_m=1., up_rms_m=0.),
        dict(epochs=2, north_rms_m=2., east_rms_m=2., up_rms_m=0.),
        dict(epochs=2, north_rms_m=3., east_rms_m=3., up_rms_m=0.),
        dict(epochs=2, north_rms_m=4., east_rms_m=4., up_rms_m=0.)]


def test_horizon_quarters_rejects_gaps_and_reordered_roles():
    from lll.ilvis0_prediction_growth_audit import horizon_quarters

    rows = [dict(epoch=index, time_s=float(index), role='prediction',
                 north_direct_error_m=1., east_direct_error_m=1.,
                 up_direct_error_m=1.) for index in range(8)]
    rows[3]['epoch'] = 5
    with pytest.raises(ValueError, match='consecutive'):
        horizon_quarters(rows)
    rows[3]['epoch'] = 3
    rows[4]['role'] = 'training'
    with pytest.raises(ValueError, match='training prefix'):
        horizon_quarters(rows)
