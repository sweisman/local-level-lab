# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def report():
    rows=[]
    for i,converged in enumerate((True,False)):
        rows.append(dict(identity=f'case-{i}',law='increment' if i==0 else 'point',model='sphere_rotating',
            profile=bool(i),start=0,complete=True,converged=converged,accurate=True,
            prediction=dict(horizontal_rms_m=1.8+i*.2,vertical_rms_m=.2),
            conditional_prediction=dict(horizontal_rms_m=1.81+i*.2,vertical_rms_m=.21,accuracy=dict(passed=True)),
            linear_calibration_status='active_bounds_unsupported',normalized_parameters={'gyro_gain_x':1.}))
    return dict(verified=True,total=2,complete=2,numerically_converged=1,raw_accuracy=2,conditional_accuracy=2,
        rows=rows,qualified=False,elapsed_s=120.,attempted_native_calls=10,
        prepaid=dict(native_calls=20,packet_visits=100),confidence_calibrated=False)


def test_render_separates_accuracy_numerical_failure_and_calibration_limits():
    from lll.structured_noisy_publication import render
    text=render(report())
    assert '2/2' in text and '1/2' in text
    assert 'case-0' in text and 'case-1' in text
    assert 'boundary' in text and 'not qualified' in text
    assert 'not Earth-model votes' in text


def test_render_refuses_an_unverified_result():
    from lll.structured_noisy_publication import render
    data=report();data['verified']=False
    with pytest.raises(ValueError):render(data)


def test_result_csv_preserves_both_starts_and_the_failed_case():
    import csv,io
    from lll.structured_noisy_publication import result_csv
    rows=list(csv.DictReader(io.StringIO(result_csv(report()))))
    assert len(rows)==2 and [r['identity'] for r in rows]==['case-0','case-1']
    assert rows[0]['numerical_pass']=='True' and rows[1]['numerical_pass']=='False'
    assert rows[1]['linear_calibration_status']=='active_bounds_unsupported'


def test_render_rejects_inconsistent_summary_counts():
    from lll.structured_noisy_publication import render
    data=report();data['numerically_converged']=2
    with pytest.raises(ValueError):render(data)


def saved_case_fixture(monkeypatch):
    from types import SimpleNamespace
    from lll import structured_noisy_report,airquantumgrav_geographic_report
    from lll.structured_noisy_training import recipe
    hashes={name:value*64 for name,value in [('analysis/lll/ilvis0_tangent.cpp','1'),
        ('analysis/lll/ilvis0_noise_bridge.cpp','2'),('analysis/lll/ilvis0_wide_tangent.py','3')]}
    tm=dict(source_sha256='4'*64,original_source_sha256='1'*64,compiler='c++',gravity_anchor_height_m=2200.,
        internal_mantissa_bits=64,binary_sha256='6'*64)
    nm=dict(source_sha256='5'*64,original_source_sha256='1'*64,bridge_source_sha256='2'*64,
        wide_loader_source_sha256='3'*64,compiler='c++',internal_mantissa_bits=64,binary_file='noise.so',binary_sha256='7'*64)
    saved={'compilation.json':dict(tangent=tm,noise_bridge=nm),'input-binding.json':dict(gravity_anchor_height_m=2200.),
        'native-operation-summary.json':dict(native_calls=5,packet_visits=9),
        'native-prepayment.json':dict(state='complete',prepaid=dict(native_calls=20,packet_visits=100),
            attempted=dict(native_calls=5,packet_visits=9)),'construction.sqlite':b'construction','worker-build-journal.sqlite':b'builds'}
    payload=dict(law='increment',model='sphere_rotating',latitude_deg=55.,profile=False,start=0,policy_id='reported-short-v1')
    envelope=dict(result=dict(converged=False),artifacts={},charged=dict(native_calls=20,packet_visits=100))
    seen=[]
    def check(spec,result,values,*,r):
        seen.append(spec);return dict(native_calls=5,converged=False,accurate=True)
    monkeypatch.setattr(structured_noisy_report,'check_case',check)
    monkeypatch.setattr(airquantumgrav_geographic_report,'construction_counts',lambda *a,**kw:None)
    study=SimpleNamespace(manifest={'sources':hashes},tasks={'case':dict(shard=0,payload=payload)},
        completion={'manifest_sha256':'f'*64},envelope=lambda identity:envelope,
        artifact=lambda identity,name,**kw:saved.get(name,{}),read=lambda *a,**kw:b'checked-by-closed-reader')
    bindings=dict(wide_sha256='4'*64,bridge_sha256='5'*64,compiler='c++')
    return study,payload,recipe(),bindings,saved,seen


def test_shared_saved_case_auditor_retains_numerical_failure(monkeypatch):
    from lll.structured_noisy_publication import inspect_case
    study,payload,r,bindings,saved,seen=saved_case_fixture(monkeypatch)
    checked=inspect_case(study,'case',payload=payload,r=r,bindings=bindings)
    assert checked['converged'] is False and checked['native_calls']==5
    assert seen==[payload]


@pytest.mark.parametrize('change',['compiler','source','prepayment'])
def test_shared_saved_case_auditor_rejects_changed_bindings(monkeypatch,change):
    from lll.structured_noisy_publication import inspect_case
    study,payload,r,bindings,saved,seen=saved_case_fixture(monkeypatch)
    if change=='compiler':saved['compilation.json']['tangent']['compiler']='other'
    elif change=='source':saved['compilation.json']['noise_bridge']['source_sha256']='0'*64
    else:saved['native-prepayment.json']['attempted']['native_calls']=6
    with pytest.raises(ValueError):inspect_case(study,'case',payload=payload,r=r,bindings=bindings)


def cache_fixture():
    from types import SimpleNamespace
    from lll.studies.artifacts import encoded
    tm=dict(source_sha256='1'*64,binary_sha256='2'*64)
    nm=dict(source_file='noise.cpp',binary_file='noise.so',source_sha256='3'*64,binary_sha256='4'*64,
        compiler='c++',compiler_executable='/usr/bin/c++',flags=['-O2'],cache_sha256='5'*64)
    raw=encoded(nm)
    study=SimpleNamespace(tasks={'a':{'shard':0},'b':{'shard':0}},rows={'a':{},'b':{}},
        envelope=lambda identity:{'result':{'converged':False}},
        artifact=lambda identity,name:dict(tangent=tm,noise_bridge=nm),
        read=lambda name,**kw:raw if name.endswith('.json') else b'build-counts')
    return study,nm


def test_shared_native_cache_entries_deduplicate_explicit_worker_assets():
    from lll.structured_noisy_publication import native_cache_entries
    study,nm=cache_fixture();entries=native_cache_entries(study)
    assert len(entries)==6 and set(entries)<={
        'shards/000/kernels/wide-tangent-'+'1'*64+'.cpp',
        'shards/000/kernels/wide-tangent-'+'1'*64+'.so',
        'shards/000/kernels/noise.cpp','shards/000/kernels/noise.so',
        'shards/000/kernels/noise.json','shards/000/kernels/builds.sqlite'}


def test_shared_native_cache_entries_reject_changed_cache_binding():
    from lll.structured_noisy_publication import native_cache_entries
    study,nm=cache_fixture();nm['compiler']='other'
    with pytest.raises(ValueError):native_cache_entries(study)
