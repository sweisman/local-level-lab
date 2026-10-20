# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import hashlib
import pytest


def module():
    from lll import ilvis0_evidence_dataset
    return ilvis0_evidence_dataset


def inputs():
    models=('sphere_rotating','sphere_still','flat_still');cases=('bias1_unsubtracted','bias1_profiled_removal')
    current=[];groups=[];eligible=[];gyro=[];history=[];files=[]
    for i in range(2):
        sid=str(i);source=str(i)*64
        row=dict(segment_id=sid,filename=sid+'.013',source_sha256=source,imu_type='21',mounting_epoch='mount',
            selection_sha256='f'*64,selection_version='frozen',start_utc='start',end_utc='end',duration_s='240',
            minimum_ground_speed_kmh='750',shape_preference='globe',scientific_decision='abstain',all_required_repeat_checks_passed='True')
        for case in cases:
            for model in models:
                prefix=case+'__'+model+'__'
                row.update({prefix+'converged':'True',prefix+'cost':'1.25',prefix+'result_origin':'saved'})
        current.append(row);eligible.append({k:row[k] for k in ('segment_id','source_sha256','mounting_epoch','selection_sha256','selection_version')})
        groups.append(dict(record_id='ilvis0:'+sid,archive='ilvis0',group_id='shared-group',source_sha256=source,
            physical_instrument_id='',installation_id='',shared_leg_id='candidate-leg',mounting_configuration='mount'))
        for model in models:
            gyro.append(dict(segment_id=sid,source_sha256=source,model=model,imu_type='21',removal='0',crab_deg='0',roll_deg='0',pitch_deg='0',
                observed_nose_down_dph='4.0',predicted_nose_down_dph='3.5',observed_minus_scenario_dph='.5',scientific_decision='abstain'))
        history.extend([dict(segment_id=sid,identity='',converged='False',error='budget exhausted',operation='fit'),
                        dict(segment_id=sid,identity='later',converged='True',error='',operation='fit')])
        files.append(dict(filename=sid+'.013',source_sha256=source,state='selected',selected_stretches='1'))
    return dict(current=current,groups=groups,eligible=eligible,gyro=gyro,history=history,files=files)


def test_assembly_preserves_failures_groups_and_all_required_comparisons():
    source=inputs();before=copy.deepcopy(source);result=module().assemble(**source)
    assert source==before
    assert len(result['stretches'])==2 and len(result['primary_comparisons'])==12
    assert len(result['numerical_history'])==4
    assert sum(r['converged']=='False' for r in result['numerical_history'])==2
    assert len({r['history_row_id'] for r in result['numerical_history']})==4
    assert result['summary']['conservative_split_groups']==1
    assert result['summary']['verified_independent_flights'] is None
    for row in result['stretches']:
        assert row['shape_preference']=='globe'
        assert row['scientific_decision']=='abstain'
        assert row['calibrated_detection'] is False
        assert row['qualified_withheld_prediction'] is False
        assert row['physical_instrument_id']==''


@pytest.mark.parametrize('bad',['source','selection','group_missing','duplicate','gyro_missing','latest_failed','repeat_failed','promoted'])
def test_inconsistent_or_incomplete_sources_are_rejected(bad):
    source=inputs()
    if bad=='source':source['groups'][0]['source_sha256']='x'*64
    elif bad=='selection':source['eligible'][0]['selection_sha256']='e'*64
    elif bad=='group_missing':source['groups']=source['groups'][1:]
    elif bad=='duplicate':source['current'].append(source['current'][0])
    elif bad=='gyro_missing':source['gyro']=source['gyro'][1:]
    elif bad=='latest_failed':source['current'][0]['bias1_unsubtracted__flat_still__converged']='False'
    elif bad=='repeat_failed':source['current'][0]['all_required_repeat_checks_passed']='False'
    else:source['current'][0]['scientific_decision']='detected'
    with pytest.raises(ValueError):module().assemble(**source)


def test_artifact_check_detects_changes_and_refuses_path_escape(tmp_path):
    g=module();path=tmp_path/'known.csv';path.write_text('original')
    hashes={'known.csv':hashlib.sha256(path.read_bytes()).hexdigest()}
    g.verify_artifacts(tmp_path,hashes);path.write_text('altered')
    with pytest.raises(ValueError):g.verify_artifacts(tmp_path,hashes)
    with pytest.raises(ValueError):g.verify_artifacts(tmp_path,{'../outside':'0'*64})


def test_csv_keeps_blank_unknown_values_and_source_record_identity():
    g=module();data=g.encode_csv([dict(identity='',unknown='',count=0),dict(identity='x',unknown='',count=1)])
    assert b'identity,unknown,count' in data and b',,0' in data
