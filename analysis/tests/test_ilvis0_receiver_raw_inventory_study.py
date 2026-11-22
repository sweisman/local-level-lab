# SPDX-License-Identifier: AGPL-3.0-or-later
"""Broad inventory adapter keeps the receiver-only policy frozen."""

import json

from test_ilvis0_distance_inventory_study import fixture
from lll import ilvis0_receiver_raw_inventory_study as study


def test_adapter_selects_declared_receiver_raw_policy(tmp_path,monkeypatch):
    context,task=fixture(tmp_path)
    context.files['policy'].write_text(json.dumps(study.segments.RECEIVER_RAW_INVENTORY_POLICY))
    def scan(path,saved_context,*,policy):
        assert policy['selection_mode']=='receiver_raw_support'
        return dict(state='no_qualifying_segment',segments=[],rejections={},
                    frame_counts={'$GRP:4':1},receiver_speed_samples=1)
    monkeypatch.setattr(study.segments,'scan',scan)
    result=study.evaluate(task,context)
    assert result['passed'] and result['segment_count']==0
    assert context.saved['gyro_residuals_inspected'] is False
