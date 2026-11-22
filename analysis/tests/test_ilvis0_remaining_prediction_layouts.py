# SPDX-License-Identifier: AGPL-3.0-or-later
"""Twenty-group receiver-cut inventory controls."""

import pytest

from lll.ilvis0_remaining_prediction_layouts import validate


def _layout(i):
    return dict(segment_id=f'segment-{i}',group_id=f'group-{i}',
                receiver_epochs=30,training_epochs=20,prediction_epochs=10)


def test_exact_twenty_unique_groups_and_cuts():
    rows=[_layout(i) for i in range(20)]
    selection=[dict(segment_id=row['segment_id']) for row in rows]
    assert validate(rows,selection)==rows
    with pytest.raises(ValueError,match='twenty unique'):
        validate(rows[:-1],selection)
    rows[1]['group_id']=rows[0]['group_id']
    with pytest.raises(ValueError,match='twenty unique'):
        validate(rows,selection)


def test_changed_receiver_cut_rejected():
    rows=[_layout(i) for i in range(20)]
    selection=[dict(segment_id=row['segment_id']) for row in rows]
    rows[0]['training_epochs']=19
    with pytest.raises(ValueError,match='receiver cut'):
        validate(rows,selection)
