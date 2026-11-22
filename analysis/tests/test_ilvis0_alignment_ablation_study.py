# SPDX-License-Identifier: AGPL-3.0-or-later
"""The ablation changes one screen and keeps its source set fixed."""

import csv
import json

import pytest

from lll import ilvis0_alignment_ablation_study as study
from test_ilvis0_distance_inventory_study import fixture


def test_adapter_checks_sealed_broad_candidate_and_alignment_policy(tmp_path,monkeypatch):
    context,task=fixture(tmp_path)
    candidate=tmp_path/'candidates.csv'
    rows=[dict(task=f'task-{i:03d}',segment_id=f'segment-{i:03d}',
               source_sha256=task['source_sha256'],level_motion_screened='False')
          for i in range(29)]
    with candidate.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    parent=tmp_path/'parent.json'
    parent.write_text(json.dumps(dict(tasks=[dict(identity=task['identity'],
        source_sha256=task['source_sha256'],source_path=task['source_path'])])))
    context.files.update(candidates=candidate,parent=parent)
    task['broad_segment_id']='segment-000'
    def evaluate_task(chosen,ctx,policy):
        assert chosen is task and ctx is context
        assert policy['require_alignment_status'] is False
        assert policy['maximum_roll_deg']==study.segments.DISTANCE_INVENTORY_POLICY['maximum_roll_deg']
        return dict(passed=True)
    monkeypatch.setattr(study,'evaluate_task',evaluate_task)
    assert study.evaluate(task,context)['passed']
    task['broad_segment_id']='wrong'
    with pytest.raises(ValueError,match='sealed broad'):
        study.evaluate(task,context)
