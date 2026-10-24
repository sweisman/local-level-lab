# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-data report controls; standard library only, no trajectories run."""
import copy
import importlib
import math

import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_observation_report') is not None, 'saved-only observation auditor is missing'
    return importlib.import_module('lll.airquantumgrav_observation_report')


def fixture():
    metrics=dict(rms_neu_m=[.1,.2,.3],horizontal_rms_m=math.sqrt(.05),vertical_rms_m=.3,
        maximum_3d_m=math.sqrt(.14),total_rms_m=math.sqrt(.14))
    checks=dict(horizontal_rms_m=True,vertical_rms_m=True,maximum_3d_m=True,value_agreement=True,
        all_columns_retained=True,mixed_derivative=True)
    r=dict(queries=3,accuracy=dict(horizontal_rms_m=1.,vertical_rms_m=1.,maximum_3d_m=5.),
        value_agreement_m=.0001,difference_step=.000001,derivative_absolute_m=.5,derivative_relative=.002)
    names=[n+'_'+a for n in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever') for a in 'xyz']
    names+=['gravity_delta','time_offset','earth_removal']
    correction=dict(active_parameters=names,known_corrections_supplied_not_estimated=True)
    forecast=dict(coordinates=[[0.,0.,0.]]*3,errors_neu_m=[[.1,.2,.3]]*3,corrected=metrics,
        uncorrected_errors_neu_m=[[.1,.2,.3]]*3,uncorrected=metrics)
    comparison=dict(value_coordinates=[[0.,0.,0.]]*3,
        shifted_coordinates=[[1e-6/6378137.,2e-6/6378137.,3e-6]]*3,
        analytic_direction_scaled_m=[[1.,2.,3.]]*3,step=1e-6,direction=[.25]*27,
        value_disagreement_m=0.,derivative_disagreement_m=0.,derivative_size_m=3.,checks=checks)
    result=dict(passed=True,corrected=metrics,uncorrected=metrics,checks=checks,
        all_columns_retained=True,value_disagreement_m=0.,derivative_disagreement_m=0.)
    return result,forecast,comparison,correction,r


def test_saved_observation_audit_checks_error_series_and_directional_difference():
    result=library().case_gate(*fixture())
    assert result['passed'] and result['corrected']['maximum_3d_m']==pytest.approx(math.sqrt(.14))


@pytest.mark.parametrize('fault',['error_series','direction','gate','columns','step'])
def test_saved_observation_audit_rejects_changed_measurements_or_gate_labels(fault):
    values=copy.deepcopy(fixture());result,forecast,comparison,correction,r=values
    if fault=='error_series':forecast['errors_neu_m'][0][0]=2.
    elif fault=='direction':comparison['analytic_direction_scaled_m'][0][0]=30.
    elif fault=='gate':result['passed']=False
    elif fault=='columns':correction['active_parameters'].pop()
    else:comparison['step']=1e-5
    with pytest.raises(ValueError):library().case_gate(*values)


def test_saved_native_accounting_keeps_value_and_tangent_counts_distinct(tmp_path):
    from lll.studies.journal import IndexedLedger
    ledger=IndexedLedger(tmp_path,'freeze',['case'],fit_limit=4,diagnostic_limit=1);ledger.start('case')
    for kind in ('tangent','value','value','value'):
        ledger.append('sweeps',dict(identity='case',phase='fit',kind=kind,packet_visits=7))
    counts=library().native_accounting(ledger.journal.path.read_bytes(),'freeze',{'case'})
    assert counts=={'case':dict(value=3,tangent=1,packet_visits=28)}
    with pytest.raises(ValueError):library().native_accounting(ledger.journal.path.read_bytes(),'freeze',{'other'})
