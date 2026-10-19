# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
from pathlib import Path
import pytest


def module():
    assert Path(__file__).parents[1].joinpath('lll/ilvis0_multistart.py').exists(), 'multi-start policy missing'
    return importlib.import_module('lll.ilvis0_multistart')


def row(identity,cost,passed=True):
    return dict(identity=identity,fit=dict(converged=passed,residual_sum_squares=cost,normalized_parameters=[0.,0.]))


def test_best_selection_does_not_hide_a_better_failed_start():
    m=module();rows=[row('a',2.),row('b',1.,False)]
    report=m.select(rows,expected_ids=['a','b'])
    assert report['selected_identity']=='b' and not report['passed']
    assert report['global_optimum_established'] is False


def test_selection_preserves_every_start_and_breaks_ties_deterministically():
    m=module();rows=[row('z',1.),row('a',1.)]
    report=m.select(rows,expected_ids=['z','a'])
    assert report['passed'] and report['selected_identity']=='a'
    assert report['attempted_identities']==['z','a']
    assert rows==[row('z',1.),row('a',1.)]


@pytest.mark.parametrize('rows,ids',[( [row('a',1.)],['a','b']),([row('a',1.),row('a',2.)],['a','b']),([row('a',float('nan'))],['a'])])
def test_missing_duplicate_or_nonfinite_results_cannot_pass(rows,ids):
    with pytest.raises(ValueError):module().select(rows,expected_ids=ids)


def test_grid_changes_only_timing_and_keeps_every_column():
    m=module();seed=[.1,-.2,.3];starts=m.starts(seed,['bias','time_offset','null'],[-.8,-.6,-.4])
    assert starts==[[.1,-.8,.3],[.1,-.6,.3],[.1,-.4,.3]]
    assert seed==[.1,-.2,.3]
    with pytest.raises(ValueError):m.starts(seed,['bias','time_offset','null'],[-1.1])
    with pytest.raises(ValueError):m.starts(seed,['bias','time_offset','null'],[-.6,-.6])
