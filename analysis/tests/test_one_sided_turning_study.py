# SPDX-License-Identifier: AGPL-3.0-or-later
"""The candidate rule gets a separate finite generated study identity."""

import pytest

from lll.one_sided_turning_study import ID,recipe,tasks,validate_task


def test_two_unchanged_turning_inputs_get_one_finite_start_each():
    r=recipe()
    rows=tasks(r)
    assert [x['identity'] for x in rows]==['turning-level','turning-climb']
    assert r['maximum_evaluations']==200
    assert r['verification_evaluations']==9
    assert r['workers']*r['threads']==2
    assert all(x['payload']['start']==0 for x in rows)


def test_changed_turning_study_task_is_rejected():
    row=tasks()[0]
    validate_task(row)
    with pytest.raises(ValueError,match='unchanged one-sided task'):
        validate_task(dict(row,payload=dict(row['payload'],start=1)))


def test_study_id_is_accepted_by_shared_generated_reconstruction(tmp_path):
    from lll.generated_turning_problem import project_root
    path=tmp_path/'data'/ID
    path.mkdir(parents=True)
    assert project_root(path,ID)==tmp_path
