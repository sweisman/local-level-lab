# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def module():
    import ilvis0_gyro_companion_worker
    return ilvis0_gyro_companion_worker


def test_control_and_scenario_scope_is_finite():
    w=module()
    assert len(w.CONTROLS)==48 and len(w.SCENARIOS)==243
    assert w.LIMITS['maximum_observed_summaries']==53
    assert w.LIMITS['maximum_scenarios']==12879
    assert w.LIMITS['original_reads']==w.LIMITS['native_evaluations']==w.LIMITS['optimizer_starts']==0


@pytest.mark.parametrize('index',range(48))
def test_analytic_rotating_basis_and_physical_axis_reference_agrees(index):
    w=module();result=w.control(w.CONTROLS[index])
    assert result['passed'],result
    assert result['absolute_error_rads']<1e-12


def test_failed_or_missing_control_blocks_observed_stage():
    w=module()
    with pytest.raises(ValueError):w.require_controls([])
    results=[dict(identity=t['identity'],passed=True) for t in w.CONTROLS]
    assert w.require_controls(results) is None
    results[0]['passed']=False
    with pytest.raises(ValueError):w.require_controls(results)


def recording():
    fixes=[dict(time_s=float(i),latitude_rad=-.8+1e-5*i,longitude_rad=2.+2e-5*i,height_m=9000.) for i in range(5)]
    seconds={str(i):dict(duration_s=1.,raw_aircraft=[0.,-1e-4,0.],fused_context_corrected=[1e20]*3) for i in range(4)}
    return dict(segment_id='test',source_sha256='a'*64,filename='example.013',imu_type='8',group_id='group',
        shared_leg_id='leg',mounting_epoch='recorded',duration_s='4',start_utc='start',end_utc='end'),dict(receiver_fixes=fixes),dict(
            seconds=seconds,summary=dict(recorded_mount_available=True),provenance=dict(source_sha256='a'*64))


def test_recording_keeps_all_scenarios_and_same_raw_support_without_fused_input():
    w=module();meta,selected,saved=recording();result=w.observed(meta,selected,saved)
    assert result['supported'] and result['scenarios_evaluated']==243
    assert len(result['baseline'])==3 and len(result['scenario_results'])==243
    assert result['baseline'][0]['observed_nose_down_dph']==pytest.approx(1e-4*180./np.pi*3600.)
    for b in saved['seconds'].values():b['fused_context_corrected']=[-1e30]*3
    again=w.observed(meta,selected,saved)
    assert again['baseline']==result['baseline']
    assert result['scientific_decision']=='abstain'


def test_source_or_mount_failure_is_reported_without_fallback():
    w=module();meta,selected,saved=recording();saved['provenance']['source_sha256']='b'*64
    with pytest.raises(ValueError):w.observed(meta,selected,saved)
    saved['provenance']['source_sha256']='a'*64;saved['summary']['recorded_mount_available']=False
    result=w.observed(meta,selected,saved)
    assert result['supported'] is False and result['reason']=='recorded_mount_unavailable'


def test_charged_gyro_companion_never_restarts(tmp_path,monkeypatch):
    w=module();monkeypatch.setattr(w,'DATA',tmp_path);(tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='restart'):w.run()
