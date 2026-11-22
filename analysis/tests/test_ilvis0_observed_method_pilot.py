"""Finite recorded-data comparison of two bounded optimizer families."""

import csv
from pathlib import Path
from types import SimpleNamespace

import pytest

from lll import ilvis0_observed_method_pilot as study


def test_selected_recordings_span_frozen_hemisphere_year_and_duration():
    with Path(study.SELECTION).open(newline='') as stream:
        rows={row['segment_id']:row for row in csv.DictReader(stream)}
    chosen=[rows[segment] for segment in study.SEGMENTS]
    assert [row['start_utc'][:4] for row in chosen]==['2010','2011','2015']
    assert [float(row['mean_latitude_deg'])>0 for row in chosen]==[True,False,False]
    assert [round(float(row['duration_s'])) for row in chosen]==[244,442,554]


def _layouts():
    return [dict(segment_id=segment,receiver_epochs=243+index*100,
                 training_epochs=2*(243+index*100)//3,
                 native_packets=49000+index*20000)
            for index,segment in enumerate(study.SEGMENTS)]


def test_frozen_three_recording_eight_fit_grid_per_recording():
    rows=study.tasks(_layouts())
    assert len(rows)==len({row['identity'] for row in rows})==24
    assert {row['payload']['solver'] for row in rows}=={'trust_v2','scipy_trf'}
    assert {row['payload']['origin'] for row in rows}=={'inner','outer'}
    assert {row['payload']['start'] for row in rows}=={0,1}
    assert all(row['limits']['native_calls']==201 for row in rows)
    assert all(row['limits']['packet_visits']>0 for row in rows)


def test_observed_preflight_is_separate_scipy_task():
    short=study.tasks(_layouts(),preflight=True)
    assert len(short)==1
    assert short[0]['payload']['solver']=='scipy_trf'
    assert short[0]['limits']['native_calls']<201


def test_observed_method_freeze_includes_sealed_input_recovery_and_solvers():
    names=study.sources(Path('.'))
    assert 'analysis/lll/independent_bounded_solver.py' in names
    assert 'analysis/lll/ilvis0_observed_method_eval.py' in names
    assert 'analysis/lll/ilvis0_tangent.cpp' in names
    assert 'test_reboot_resume_skips_sealed_and_preserves_charges' in study.required_tests()


def test_changed_observed_task_rejected_before_input_access():
    task=study.tasks(_layouts())[0].copy()
    task['payload']=dict(task['payload'],model='flat_still')
    with pytest.raises(ValueError,match='unchanged observed optimizer task'):
        study.evaluate(task,SimpleNamespace(manifest=dict(scope=study.SCOPE),
                                           input_path=lambda *args:None))
