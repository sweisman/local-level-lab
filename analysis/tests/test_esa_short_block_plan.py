"""Outcome-independent selection of three existing ESA development windows."""

from copy import deepcopy
import json
from pathlib import Path

import pytest


def _parent():
    root=Path(__file__).resolve().parents[2]
    return json.loads((root/'docs/esa-broader-development/windows.json').read_bytes())


def test_short_block_selects_all_three_without_outcomes():
    from lll.esa_short_block_plan import select
    parent=_parent();original=deepcopy(parent)
    result=select(parent)
    assert parent==original
    assert result['window_count']==3
    assert result['conservative_groups']==1
    assert [row['original_first_index'] for row in result['windows']]==[
        42470,49554,58525]
    assert all(row['training_reports']==800 and row['future_reports']==120
               and row['unused_parent_queries']==280 and
               row['future_first_index']==row['training_last_index']+2
               and row['future_last_index']<row['original_last_index']
               for row in result['windows'])
    assert not any('gyro' in key or 'model' in key or 'score' in key
                   for row in result['windows'] for key in row)
    assert result['preparation_authorized'] is False
    assert result['fit_authorized'] is False
    assert result['confirmation_authorized'] is False


def test_short_block_rejects_changed_parent():
    from lll.esa_short_block_plan import select
    changed=_parent();changed['plan']['additional_windows']=2
    with pytest.raises(ValueError,match='unchanged frozen'):
        select(changed)
    changed=_parent();changed['plan']['windows'][1]['query_stride']=1
    with pytest.raises(ValueError,match='complete fixed'):
        select(changed)


def test_short_block_publish_requires_qualification(tmp_path):
    from lll.esa_short_block_plan import publish
    with pytest.raises(ValueError,match='qualification'):
        publish(tmp_path)
    assert not (tmp_path/'docs').exists()
