# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path

import pytest


def audit():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-final-two-audit-20261018/build_report.py'
    assert path.exists(), 'saved two-stretch audit is missing'
    spec=importlib.util.spec_from_file_location('final_two_audit',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def example():
    policy=dict(stationarity_tolerance=1e-4,relative_cost_tolerance=1e-8,
        position_rms_tolerance_m=.001,position_max_tolerance_m=.01)
    branch=dict(side='right',passed=False,reason='unchecked_neighbor_boundary',
        side_stationarity=[1e-6,2e-6],fresh_stationarity=.02,
        relative_cost_change=.001,position_rms=[.002,.003,.004],
        position_maximum=[.01,.02,.03],correction=[.25,.01],
        probe_continuity=dict(passed=True))
    return dict(identity='source',passed=False,reason='boundary_check_unresolved',
        boundary_check=dict(policy=policy,branches=[branch]))


def test_neighbor_reason_does_not_hide_cost_position_or_stationarity_failures():
    source=example();before=copy.deepcopy(source)
    result=audit().diagnose(source,['gravity_delta','time_offset'])
    assert source==before
    branch=result['branches'][0]
    assert branch['unchecked_neighbor'] and branch['endpoint_stationarity_passed']
    assert not branch['fresh_stationarity_passed']
    assert not branch['cost_passed'] and not branch['position_passed']
    assert branch['largest_corrections'][0]==['gravity_delta',.25]
    assert result['needs_neighbor_check'] and result['needs_correction_investigation']


def test_geometry_failure_is_not_a_failed_physical_position_check():
    result=audit().diagnose(dict(identity='source',passed=False,reason='side_geometry_unsupported'),['time_offset'])
    assert result['needs_geometry_check'] and result['branches']==[]
    assert not result['needs_correction_investigation']


@pytest.mark.parametrize('bad',['length','nan','negative','nonfinite_limit'])
def test_invalid_saved_numbers_fail_closed(bad):
    row=example();branch=row['boundary_check']['branches'][0]
    if bad=='length':branch['correction'].pop()
    if bad=='nan':branch['fresh_stationarity']=float('nan')
    if bad=='negative':branch['position_rms'][0]=-.1
    if bad=='nonfinite_limit':row['boundary_check']['policy']['relative_cost_tolerance']=float('inf')
    with pytest.raises(ValueError):audit().diagnose(row,['gravity_delta','time_offset'])


def test_all_scientific_checks_can_pass_while_neighbor_remains_unchecked():
    row=example();b=row['boundary_check']['branches'][0]
    b.update(fresh_stationarity=1e-6,relative_cost_change=1e-10,
        position_rms=[1e-5]*3,position_maximum=[1e-4]*3)
    result=audit().diagnose(row,['gravity_delta','time_offset'])
    assert result['needs_neighbor_check'] and not result['needs_correction_investigation']
    assert not result['original_passed']


def test_result_can_be_sealed_individually_or_inside_a_completed_summary():
    row=dict(identity='id',passed=False)
    assert audit().select_result('id',[dict(result=row)])[0]==row
    assert audit().select_result('id',[dict(state='complete',results=[row])])[0]==row
    assert audit().select_result('id',[dict(state='complete',results={'id':row})])[0]==row
    for records in ([],[dict(result=row),dict(state='complete',results=[row])]):
        with pytest.raises(ValueError):audit().select_result('id',records)
