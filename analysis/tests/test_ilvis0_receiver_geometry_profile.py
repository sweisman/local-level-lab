# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver geometry scores only preselected coordinate paths."""

import csv
import hashlib
import json
import math

import pytest

from lll.ilvis0_receiver_geometry_profile import geometry_from_fixes
from lll.ilvis0_receiver_candidate_study import bound_source


def track():
    return [dict(time_s=float(i),latitude_rad=math.radians(60.+i*.001),
                 longitude_rad=math.radians(10.+i*.0005))
            for i in range(121)]


def test_conditional_pairwise_geometry_uses_no_gyro_observation():
    result=geometry_from_fixes(track())
    assert result['supported_epochs']>80
    assert not result['gyro_observations_used']
    assert not result['aircraft_motion_independently_known']
    assert result['scientific_decision']=='abstain'
    comparisons=result['conditional_geometry']['comparisons']
    assert set(comparisons)=={
        'constant_bias','constant_and_linear_drift',
        'linear_drift_gain_mount_tangents'}
    for treatment in comparisons.values():
        assert len(treatment)==3
        for pair in treatment.values():
            assert 0<=pair['retained_fraction']<=1
            assert pair['retained_vector_rms_deg_hour']>=0


def test_gap_is_rejected_instead_of_filled():
    rows=track();rows[60]['time_s']+=3.
    with pytest.raises(ValueError,match='uninterrupted'):
        geometry_from_fixes(rows)


def test_candidate_source_binding_rejects_changed_segment(tmp_path):
    source=tmp_path/'data/ilvis0-ready/one.013.gz'
    source.parent.mkdir(parents=True);source.write_bytes(b'original')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    candidates=tmp_path/'candidates.csv'
    rows=[dict(task=f'task-{i:03d}',segment_id=f'segment-{i:03d}',
               source_sha256=digest,level_motion_screened='False')
          for i in range(29)]
    with candidates.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    parent=tmp_path/'parent.json'
    parent.write_text(json.dumps(dict(tasks=[dict(identity='task-000',
        source_sha256=digest,source_path='data/ilvis0-ready/one.013.gz')])))
    contexts=tmp_path/'contexts.json'
    contexts.write_text(json.dumps(dict(results=[dict(task_id='task-000',
        inspection=dict(source_sha256=digest))])))
    class Context:
        root=tmp_path/'data/study'
        def input_path(self,key):
            return dict(candidates=candidates,parent=parent,contexts=contexts)[key]
    task=dict(identity='task-000',segment_id='segment-000',source_sha256=digest,
              source_path='data/ilvis0-ready/one.013.gz',compressed_bytes=8)
    assert bound_source(task,Context())[0]==source
    task['segment_id']='changed'
    with pytest.raises(ValueError,match='sealed candidate'):
        bound_source(task,Context())
