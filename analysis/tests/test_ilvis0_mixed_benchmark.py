# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def test_long_mixed_benchmark_has_separate_finite_six_case_no_fit_allowance():
    from lll.ilvis0_mixed_benchmark import recipe,tasks
    r=recipe();matrix=tasks()
    assert len(matrix)==6 and (r['workers'],r['threads'],r['maximum_wall_s'])==(1,1,7200.)
    assert sum(t['limits']['native_calls'] for t in matrix)==12
    assert sum(t['limits']['packet_visits'] for t in matrix)==5184000000
    assert r['optimizer_starts']==r['original_reads']==r['protected_reads']==r['retries']==0


def test_long_mixed_report_rejects_open_before_numerical_imports(tmp_path):
    from lll.ilvis0_mixed_benchmark import inspect
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path)


def test_mixed_comparison_requires_bitwise_values_and_all_derivative_columns():
    import numpy as np
    from lll.ilvis0_mixed_benchmark import checks
    arrays=dict(reference_coordinates=np.zeros((3,3)),candidate_coordinates=np.zeros((3,3)),
        reference_difference=np.zeros((3,3)),candidate_difference=np.zeros((3,3)),
        reference_jacobian=np.ones((9,26)),candidate_jacobian=np.ones((9,26)),standard_deviation=np.ones(9))
    assert checks(arrays,boundaries=[0,0])['passed']
    changed=copy.deepcopy(arrays);changed['candidate_coordinates'][0,0]=1e-30
    assert not checks(changed,boundaries=[0,0])['passed']
    changed=copy.deepcopy(arrays);changed['candidate_jacobian'][8,25]+=1.
    assert not checks(changed,boundaries=[0,0])['passed']
    changed=copy.deepcopy(arrays);changed['candidate_difference'][0,0]=-0.
    assert not checks(changed,boundaries=[0,0])['passed']
    changed=copy.deepcopy(arrays);changed['reference_jacobian']=np.ones(9)
    with pytest.raises(ValueError):checks(changed,boundaries=[0,0])


def test_long_benchmark_native_bridge_counts_once_and_preserves_full_arrays(tmp_path):
    import hashlib
    from pathlib import Path
    from lll.ilvis0_mixed_benchmark import recipe,calculate
    from lll import ilvis0_wide_tangent as wide
    from lll.ilvis0_mixed_tangent import load
    r=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    def factory(anchor):
        a,am=wide.load(tmp_path,gravity_anchor_height_m=anchor)
        b,bm=load(tmp_path,gravity_anchor_height_m=anchor,
            expected_source_sha256=hashlib.sha256(Path('analysis/lll/ilvis0_tangent.cpp').read_bytes()).hexdigest(),
            expected_loader_sha256=hashlib.sha256(Path(wide.__file__).read_bytes()).hexdigest())
        return dict(reference=a,candidate=b),dict(reference=am,candidate=bm)
    saved={};calls=[];construction=[]
    result=calculate(dict(model='flat_still',latitude_deg=55.,profile=True,start=0),r,
        kernel_factory=factory,reserve=lambda **v:calls.append(v),reserve_construction=lambda **v:construction.append(v),
        save=lambda k,v:saved.__setitem__(k,v),save_bytes=lambda k,v:saved.__setitem__(k,v),check_continue=lambda:None)
    assert result['passed'] and len(calls)==2
    assert sum(v['packet_visits'] for v in calls)==10800
    assert sum(v.get('constructed_intervals',0) for v in construction)==600
    assert sum(v.get('generated_samples',0) for v in construction)==616
    assert result['raw_arrays_unchanged'] and result['active_columns']==27
    assert result['optimizer_starts']==result['original_reads']==result['protected_reads']==0
    assert saved['comparison.npz'] and result['checks']['values_bitwise_identical']
