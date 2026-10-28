# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import numpy as np
import pytest


def fixture(center=0.):
    from lll.studies.artifacts import digest
    active=['time_offset']+['p'+str(i) for i in range(26)];scale=.01
    dt=np.diff(np.arange(601)/300).astype('<f8')
    record=dict(identity='saved-point',saved_converged=False,timing_scale=scale,
        fit=dict(active_parameters=active,residual_sum_squares=5.),artifact_sha256={'fit.json':'a'*64},
        artifacts={'input-binding.json':dict(native_packets=600,full_array_sha256=dict(dt=digest(dt.tobytes()))),
                   'training-observations.json':dict(times_s=[.5,1.5])})
    branches=[]
    for h in (1e-5,1e-6,1e-7):
        for side in (-1,1):
            anchor=np.zeros(27);anchor[0]=center+side*h/scale
            feasible=bool(-1<=anchor[0]-h/scale/4 and anchor[0]+h/scale/4<=1)
            branches.append(dict(side=side,spacing_s=h,feasible=feasible,point=anchor.tolist(),
                residual=[1.,2.],jacobian=[[1.]+[0.]*26,[0.,1.]+[0.]*25]))
    diagnostic=dict(active_parameters=active,columns=27,source_fit_sha256='a'*64,
        labels_changed=False,nonlinear_fit_starts=0,center=dict(normalized_time_offset=center),branches=branches)
    return record,diagnostic


@pytest.mark.parametrize('center,count',[(0.,6),(-1.,3)])
def test_cell_matrices_keep_every_feasible_spacing_and_all_physical_columns(center,count):
    from lll.timing_cell_study import matrices
    record,d=fixture(center);rows=matrices(record,d,diagnostic_sha256='b'*64)
    assert len(rows)==count
    for row in rows:
        assert len(row['active'])==len(row['lower'])==len(row['upper'])==27
        assert all(-1<=a<b<=1 for a,b in zip(row['lower'],row['upper']))
        assert all(a<=x<=b for x,a,b in zip(row['point'],row['lower'],row['upper']))
        assert row['source_fit_sha256']=='a'*64 and row['source_diagnostic_sha256']=='b'*64
    if center==0.:
        assert {r['side'] for r in rows}=={-1,1}
        assert rows[0]['upper'][0]==0. and rows[1]['lower'][0]==0.


@pytest.mark.parametrize('change',['hash','alignment','columns','feasibility'])
def test_cell_matrix_selection_rejects_changed_clock_or_omitted_information(change):
    from lll.timing_cell_study import matrices
    record,d=fixture()
    if change=='hash':record['artifacts']['input-binding.json']['full_array_sha256']['dt']='0'*64
    elif change=='alignment':record['artifacts']['training-observations.json']['times_s'][0]+=.0001
    elif change=='columns':d['active_parameters']=d['active_parameters'][:-1]
    else:d['branches'][0]['feasible']=False
    with pytest.raises(ValueError):matrices(record,d,diagnostic_sha256='b'*64)


def test_cell_review_freezes_one_task_eighteen_solves_and_zero_native_calls():
    from lll.timing_cell_study import configuration,task
    r=configuration();t=task('a'*64)
    assert r['maximum_linear_solves']==18 and r['workers']==r['threads']==1
    assert r['maximum_wall_s']==600 and r['maximum_iterations']==100
    assert t['limits']==dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)


def test_cell_review_requires_qualification_before_data_reads(tmp_path):
    from lll.timing_cell_study import prepare
    with pytest.raises(ValueError,match='qualification'):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()
