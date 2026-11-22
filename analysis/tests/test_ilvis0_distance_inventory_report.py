# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved candidate grouping never inflates overlapping recorder counts."""

import pytest

from lll.ilvis0_distance_inventory_report import build_rows


def candidate(segment_id):
    fix=dict(latitude_rad=.5,longitude_rad=-1.,height_m=900.)
    return dict(segment_id=segment_id,start_s=172800.,end_s=173420.,
        duration_s=620.,receiver_distance_m=51000.,
        minimum_receiver_ground_speed_kmh=180.,
        median_receiver_ground_speed_kmh=300.,
        receiver_fixes_count=621,first_receiver_fix=fix,last_receiver_fix=fix,
        imu_type=8,signature='mount')


def control():
    tasks={name:dict(source_sha256=sha,filename=name+'.013') for name,sha in
           [('a','a'*64),('b','a'*64),('c','c'*64)]}
    results={name:dict(identity=name,source_sha256=task['source_sha256'],
        filename=task['filename'],earth_model_fits=0,
        gyro_residuals_inspected=False,scientific_decision='abstain',
        passed=True,state='segments_available',
        segments=[candidate('first' if name!='c' else 'second')])
        for name,task in tasks.items()}
    contexts=dict(results=[dict(task_id=name,timing=dict(dates=['2009-04-14']))
                           for name in tasks])
    return tasks,results,contexts


def test_aliases_count_once_and_same_day_is_one_group():
    files,stretches=build_rows(*control())
    assert len(files)==3 and len(stretches)==2
    assert files[1]['canonical_task']=='a' and files[1]['candidate_stretches']==0
    assert {row['date_group'] for row in stretches}=={'2009-04-14'}
    assert all(row['receiver_distance_km']==51 for row in stretches)


def test_recording_crossing_midnight_connects_date_groups():
    tasks,results,contexts=control()
    contexts['results'][0]['timing']['dates']=['2009-04-14','2009-04-15']
    contexts['results'][2]['timing']['dates']=['2009-04-15']
    _,stretches=build_rows(tasks,results,contexts)
    assert {row['date_group'] for row in stretches}=={'2009-04-14'}


def test_changed_alias_or_gyro_outcome_is_rejected():
    tasks,results,contexts=control()
    results['b']['segments']=[candidate('different')]
    with pytest.raises(ValueError,match='aliases'):
        build_rows(tasks,results,contexts)
    results['b']['segments']=[candidate('first')]
    results['c']['gyro_residuals_inspected']=True
    with pytest.raises(ValueError,match='scientific scope'):
        build_rows(tasks,results,contexts)
