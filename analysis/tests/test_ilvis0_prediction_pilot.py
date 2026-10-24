# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata selection is independent of model costs and gyro summaries."""
import importlib.util

import pytest


def selection():
    name='lll.ilvis0_prediction_pilot'
    assert importlib.util.find_spec(name) is not None, 'metadata-only pilot selector missing'
    return __import__(name,fromlist=['select'])


def rows():
    def row(identity,kind,latitude,duration,group):
        source=identity.rjust(64,'0');filename=identity+'.013'
        return (dict(segment_id=identity,filename=filename,source_sha256=source,imu_type=str(kind),
            mean_latitude_deg=str(latitude),mean_course_deg='130',duration_s=str(duration),
            minimum_ground_speed_kmh='710',median_ground_speed_kmh='730',start_utc='a',end_utc='b'),
            dict(record_id='ilvis0:'+identity,archive='ilvis0',filename=filename,source_sha256=source,
                 group_id=group,role='retrospective_development'))
    pairs=[row('a',8,-60,300,'shared'),row('b',8,-60,500,'long'),
           row('c',21,70,400,'north'),row('d',21,-60,600,'long'),row('e',21,-60,450,'other')]
    return [p[0] for p in pairs],[p[1] for p in pairs]


def test_rare_cells_then_duration_and_distinct_groups_with_fixed_ties():
    cohort,provenance=rows();chosen=selection().select(cohort,provenance)
    assert [r['segment_id'] for r in chosen]==['c','b','e']
    assert len({r['group_id'] for r in chosen})==3
    # Changing diagnostic fields must not change this metadata selection.
    for row in cohort:row.update(training_cost='-9999',globe_preference='no',gyro_pitch='999')
    assert selection().select(list(reversed(cohort)),list(reversed(provenance)))==chosen


@pytest.mark.parametrize('fault',['hash','protected','missing_group','duplicate'])
def test_selection_rejects_unverified_membership(fault):
    cohort,provenance=rows()
    if fault=='hash':provenance[0]['source_sha256']='f'*64
    elif fault=='protected':provenance[0]['role']='reserved_confirmation'
    elif fault=='missing_group':provenance[0]['group_id']=''
    else:cohort.append(dict(cohort[0]))
    with pytest.raises(ValueError):selection().select(cohort,provenance)


def test_exact_split_uses_receiver_times_without_model_or_gyro_outcomes():
    chosen=dict(segment_id='abc',filename='sample.013',source_sha256='a'*64,
        group_id='flight-group',imu_type='8')
    source=dict(filename='sample.013',task='task',source_path='/not/opened/sample.013.gz',
        segment=dict(segment_id='abc',imu_type=8,receiver_fixes=[dict(time_s=100.+i) for i in range(12)]))
    context=dict(task_id='task',inspection=dict(source_sha256='a'*64),timing=dict(accepted=True))
    layout=__import__("lll.ilvis0_prediction_layout",fromlist=["prediction_layout"]).prediction_layout(chosen,source,context)
    assert layout['training_epochs']==8 and layout['prediction_epochs']==4
    assert layout['last_training_utc_week_s']==107.
    assert layout['first_prediction_utc_week_s']==108.
    assert layout['receiver_positions_used_for_selection'] is False
    assert layout['original_reads']==layout['observed_starts']==0


@pytest.mark.parametrize('fault',['source','configuration','time','short','timing'])
def test_split_rejects_mismatched_or_unsupported_metadata(fault):
    chosen=dict(segment_id='abc',filename='sample.013',source_sha256='a'*64,
        group_id='flight-group',imu_type='8')
    source=dict(filename='sample.013',task='task',source_path='unused',
        segment=dict(segment_id='abc',imu_type=8,receiver_fixes=[dict(time_s=100.+i) for i in range(12)]))
    context=dict(task_id='task',inspection=dict(source_sha256='a'*64),timing=dict(accepted=True))
    if fault=='source':context['inspection']['source_sha256']='b'*64
    elif fault=='configuration':source['segment']['imu_type']=21
    elif fault=='time':source['segment']['receiver_fixes'][4]['time_s']=103.
    elif fault=='short':source['segment']['receiver_fixes']=source['segment']['receiver_fixes'][:8]
    else:context['timing']['accepted']=False
    with pytest.raises(ValueError):__import__("lll.ilvis0_prediction_layout",fromlist=["prediction_layout"]).prediction_layout(chosen,source,context)
