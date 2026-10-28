# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
from types import SimpleNamespace
import numpy as np
import pytest


def fixture():
    from lll.timing_cell_native_study import identities
    from lll.studies.artifacts import digest,encoded
    points=[];matrices=[];proposals=[]
    for i,identity in enumerate(identities()):
        points.append(dict(identity=identity,selection_sha256=str(i)*64,
            fit=dict(active_parameters=['time_offset']+['p'+str(k) for k in range(26)]),
            artifact_sha256={'fit.json':str(i)*64}))
        for branch in range(3 if i<2 else 6):
            m=dict(identity=identity,source_fit_sha256=str(i)*64,active=points[-1]['fit']['active_parameters'],
                point=[0.]*27,lower=[-1.]*27,upper=[1.]*27,residual=[1.],jacobian=np.zeros((1,27)).tolist(),
                branch_index=branch,side=1 if branch%2 else -1,spacing_s=1e-5)
            index=len(matrices);matrices.append(m)
            proposals.append(dict(index=index,matrix_sha256=digest(encoded(m)),
                proposal=dict(linear_success=True,point=[0.]*27,predicted_cost=1.,predicted_residual=[1.])))
    return points,dict(rows=matrices,sha256=digest(encoded(matrices))),proposals


def test_native_cell_selection_includes_all_eighteen_without_best_spacing_selection():
    from lll.timing_cell_native_study import bind_proposals
    points,selected,proposals=fixture();original=copy.deepcopy(points)
    result=bind_proposals(points,selected,proposals)
    assert points==original and [len(r['proposals']) for r in result]==[3,3,6,6]
    assert [p['index'] for r in result for p in r['proposals']]==list(range(18))
    assert all(len(p['active'])==27 for r in result for p in r['proposals'])


@pytest.mark.parametrize('change',['missing','duplicate','matrix','source_fit','columns','physical_box'])
def test_native_cell_selection_rejects_changed_or_incomplete_proposals(change):
    from lll.timing_cell_native_study import bind_proposals
    from lll.studies.artifacts import digest,encoded
    points,selected,proposals=fixture()
    if change=='missing':proposals.pop()
    elif change=='duplicate':proposals[-1]=copy.deepcopy(proposals[0])
    elif change=='matrix':proposals[0]['matrix_sha256']='0'*64
    elif change=='source_fit':points[0]['artifact_sha256']['fit.json']='a'*64
    elif change=='columns':points[0]['fit']['active_parameters']=list(reversed(points[0]['fit']['active_parameters']))
    else:
        selected['rows'][0]['lower'][0]=-2.
        selected['sha256']=digest(encoded(selected['rows']))
        proposals[0]['matrix_sha256']=digest(encoded(selected['rows'][0]))
    with pytest.raises(ValueError):bind_proposals(points,selected,proposals)


def test_native_cell_freezes_four_workers_and_eight_sweeps_per_original_point():
    from lll.timing_cell_native_study import configuration,work_allowance
    c=configuration();assert (c['workers'],c['threads'],c['maximum_evaluations'])==(4,1,8)
    assert c['maximum_wall_s']==3600 and c['nonlinear_fit_starts']==0
    assert work_allowance(281474977010693)==dict(native_calls=23642,packet_visits=14910394,bound_calls=0,bound_steps=0)
    with pytest.raises(ValueError):work_allowance(281474977010694)


def test_native_cell_requires_qualification_and_scope_before_data_or_native_access(tmp_path):
    from lll.timing_cell_native_study import prepare,evaluate
    with pytest.raises(ValueError,match='qualification'):prepare(tmp_path,qualification=None)
    with pytest.raises(ValueError,match='scope'):evaluate({},SimpleNamespace(manifest={'scope':'unapproved'}))
    assert not (tmp_path/'data').exists()


def test_native_cell_source_changes_allow_only_documented_adapter_changes():
    from lll.timing_cell_native_study import parent_changes
    parent={'physics.py':'a','analysis/lll/stopping_consistency_study.py':'b'}
    current=dict(parent);current['analysis/lll/stopping_consistency_study.py']='c'
    assert list(parent_changes(parent,current))==['analysis/lll/stopping_consistency_study.py']
    current['physics.py']='d'
    with pytest.raises(ValueError):parent_changes(parent,current)
