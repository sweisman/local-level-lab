"""Fixed primary-receiver motion profiles do not use fitted outcomes."""

import math
import csv
import hashlib
import json

import pytest

from lll import ilvis0_receiver_motion_profile as study
from lll.ilvis0_receiver_motion_profile import profile_fixes
from lll.models import WGS84_A


def fixes(*,climb=0.,turn_deg_s=0.,gap=False):
    rows=[];lat=math.radians(65.);lon=0.;height=3000.
    for index in range(601):
        t=float(index+(3 if gap and index>=300 else 0))
        if index:
            angle=math.radians(turn_deg_s*(index-.5))
            lat+=200*math.cos(angle)/WGS84_A
            lon+=200*math.sin(angle)/(WGS84_A*math.cos(lat))
            height+=climb
        rows.append(dict(time_s=t,latitude_rad=lat,
                         longitude_rad=lon,height_m=height))
    return rows


def test_straight_level_receiver_track_has_near_zero_turn_and_climb():
    result=profile_fixes(fixes())
    assert result['receiver_fixes']==601
    assert result['supported_course_rate_epochs']>500
    assert result['median_speed_kmh']==pytest.approx(720,rel=.01)
    assert result['p95_abs_climb_mps']<1e-9
    assert result['p95_abs_course_rate_deg_s']<.001
    assert result['gyro_used'] is False
    assert result['scientific_decision']=='abstain'


def test_known_climb_and_turn_are_reported_with_correct_signless_scale():
    result=profile_fixes(fixes(climb=1.,turn_deg_s=.02))
    assert result['p95_abs_climb_mps']==pytest.approx(1.,abs=.01)
    assert result['p95_abs_course_rate_deg_s']==pytest.approx(.02,abs=.002)
    assert result['course_span_deg']>8.


def test_receiver_gap_does_not_get_interpolated():
    with pytest.raises(ValueError,match='uninterrupted'):
        profile_fixes(fixes(gap=True))


def test_adapter_reproduces_exact_parent_candidate_before_profiling(tmp_path,monkeypatch):
    source=tmp_path/'data/ilvis0-ready/one.013.gz'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'known original')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    candidate=tmp_path/'candidates.csv'
    rows=[dict(task=f'task-{i:03d}',segment_id=f'segment-{i:03d}',
               source_sha256=digest,level_motion_screened='False') for i in range(29)]
    with candidate.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    parent=tmp_path/'parent.json'
    parent.write_text(json.dumps(dict(tasks=[dict(identity='task-000',
        source_path='data/ilvis0-ready/one.013.gz',source_sha256=digest)])))
    contexts=tmp_path/'contexts.json'
    contexts.write_text(json.dumps(dict(results=[dict(task_id='task-000',
        inspection=dict(source_sha256=digest))])))
    policy=tmp_path/'policy.json';policy.write_text(json.dumps(study.POLICY))
    class Context:
        root=tmp_path/'data/study'
        def input_path(self,key):
            return dict(candidates=candidate,parent=parent,contexts=contexts,policy=policy)[key]
        def save(self,name,value):
            assert name=='motion.json'
            self.saved=value
            return 'artifacts/one/motion.json'
    context=Context()
    task=dict(identity='task-000',segment_id='segment-000',
              source_path='data/ilvis0-ready/one.013.gz',source_sha256=digest,
              compressed_bytes=len(source.read_bytes()),filename='one.013',
              candidate_duration_s=600.)
    monkeypatch.setattr(study.segments,'scan',lambda *args,**kwargs:dict(
        source_sha256=digest,segments=[dict(segment_id='segment-000',
        duration_s=600.,receiver_fixes=fixes())]))
    result=study.evaluate(task,context)
    assert result['passed'] and context.saved['profile']['gyro_used'] is False
    task['segment_id']='different'
    with pytest.raises(ValueError,match='bindings'):
        study.evaluate(task,context)
