# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def audit():
    path=Path(__file__).parents[2]/'docs/ilvis0-long-staged-feasibility-v2/audit_first_pair.py'
    spec=importlib.util.spec_from_file_location('_long_pair_audit_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def row():
    return dict(numerical_checks_passed=True,known_truth_retained=True,future_truth_contained=True,
        future_width_m=[10.,20.,30.],width_target_m=[20.,20.,50.],passed=True,useful=True)


def test_audit_keeps_coordinate_units_and_additive_remainder_separate():
    result=audit().metrics(row(),[1.,1.,1.],[2.,3.,4.],.1)
    assert result['unshared_half_width_m']==pytest.approx([2.1,3.1,4.1])
    assert result['unshared_width_fraction']==pytest.approx([.42,.31,8.2/30.])
    assert result['outcome']=='Pass'


def test_large_valid_range_is_too_wide_without_becoming_a_numerical_failure():
    value=row();value.update(future_width_m=[200.,200.,300.],passed=False,useful=False)
    result=audit().metrics(value,[10.,10.,10.],[1.,1.,1.],0.)
    assert result['outcome']=='Too wide' and result['numerical_checks_passed']


def test_inconsistent_labels_and_impossible_widths_are_rejected():
    for change in (dict(passed=False),dict(future_width_m=[0.,1.,2.]),dict(known_truth_retained=False)):
        with pytest.raises(ValueError):audit().metrics(dict(row(),**change),[.1]*3,[1.]*3,0.)
