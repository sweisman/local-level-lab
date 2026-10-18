# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def module():
    from lll import ilvis0_stopping_audit
    return ilvis0_stopping_audit


def test_true_cusp_minimum_can_fail_original_gate_despite_small_gradient():
    rows=module().known_controls()
    cusps=[r for r in rows if r['case'].startswith('cusp')]
    assert len(cusps)==2
    for r in cusps:
        assert r['known_global_minimum'] and r['stationarity_passed']
        assert not r['original_gate']['passed']
        assert r['signed_actual_cost_change']>0
        assert max(r['original_gate']['position_rms_neu_m'])>.001
    assert all(r['expectation_met'] for r in rows)


def test_smooth_and_constrained_minima_pass_but_nonminimum_fails():
    rows={r['case']:r for r in module().known_controls()}
    assert rows['smooth_minimum']['original_gate']['passed']
    assert rows['constrained_minimum']['original_gate']['passed']
    assert not rows['smooth_nonminimum']['original_gate']['passed']


def test_saved_packet_screen_uses_elapsed_accumulation_not_rounded_nominal_phase():
    ends=np.cumsum(np.full(10000,.005));times=ends[[100,300,500]]-2e-8
    r=module().packet_screen(times,10000,0.,.15)
    assert r['epochs_within_100ns']==3
    assert r['minimum_packet_distance_ns']==pytest.approx(20.,abs=.01)
    assert r['changed_packet_epochs_plus_100ns']==3
    assert r['changed_packet_epochs_minus_100ns']==0


def test_affine_slices_are_diagnostics_and_keep_time_feasibility():
    r=module().affine_slices(np.zeros(2),np.array([1.,2.,1.]),np.array([[1.,2.],[2.,1.],[0.,0.]]),1,-1e-5,1e-5)
    assert len(r)==3
    assert r[2]['method']=='fixed_time' and r[2]['normalized_time_step']==0.
    assert abs(r[1]['normalized_time_step'])<=1e-5+1e-15
    assert all(row['native_predictions']==0 and row['observed_fit_starts']==0 for row in r)


def test_signed_saved_probe_requires_reproduced_center():
    fit=dict(residual_sum_squares=10.,stability_probe={'reason':'fresh_position_probe_not_stable'},
             evaluation_trace=[dict(cost=10.,fresh=True),dict(cost=10.1,fresh=True)])
    assert module().signed_saved_probe(fit)==pytest.approx(.1)
    fit['evaluation_trace'][0]['cost']=9.
    with pytest.raises(ValueError):module().signed_saved_probe(fit)
