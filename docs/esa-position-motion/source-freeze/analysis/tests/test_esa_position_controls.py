# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import esa_position_controls as controls


def test_independent_quadratic_path_recovers_supplied_equatorial_velocity_and_turn():
    path=controls.path(latitude=0.,heading=90.,turn=-.06,climb=2.,nonuniform=True)
    # At the equator the northward acceleration is +v*|turn|; metric derivatives vanish.
    assert path['truth_jet'][3]==pytest.approx(0.,abs=1e-19)
    assert path['truth_jet'][4]==pytest.approx(60./6379137.,rel=1e-14)
    assert path['truth_jet'][6]>0.
    from lll.airquantumgrav_position_motion import assess
    result=assess(path['times'],path['coordinates'],np.tile(np.eye(3)*.01,(21,1,1)),center_s=0.,
        degree=3,maximum_gap_s=.75,rounding_m=[0.]*3)
    assert result['point_speed_mps']==pytest.approx(60.,abs=2e-7)
    assert result['point_course_rate_deg_s']==pytest.approx(-.06,abs=1e-8)


def test_generated_realizations_have_distinct_immutable_streams_and_preserve_true_samples():
    first=controls.generated(.05,.8,3);same=controls.generated(.05,.8,3)
    other=controls.generated(.05,.8,4)
    np.testing.assert_array_equal(first['observed'],same['observed'])
    np.testing.assert_array_equal(first['coordinates'],same['coordinates'])
    assert first['seed']!=other['seed'] and not np.array_equal(first['observed'],other['observed'])
    assert not np.array_equal(first['observed'],first['coordinates'])
    assert first['true_course_rate_deg_s']==-.06
    assert first['time_constant_s']>0. and first['observed'].shape==(21,3)


def test_coverage_gate_includes_misses_and_has_an_exact_binomial_requirement():
    assert controls.coverage(256,256)['passed']
    assert not controls.coverage(256,240)['passed']
    with pytest.raises(ValueError):controls.coverage(0,0)
    with pytest.raises(ValueError):controls.generated(.1,.8,0)


def test_assessment_is_reserved_before_evaluation_and_rejects_scope_expansion():
    saved={}
    def save(name,value):saved[name]=value
    def call():
        assert saved['assessment-001-reservation.json']['assessments']==1
        return dict(answer=3)
    reserve=controls.Assessments(1,save,lambda:None)
    assert reserve.run(call)==dict(answer=3)
    with pytest.raises(ValueError):reserve.run(lambda:pytest.fail('over budget'))


def test_analytic_adapter_seals_all_paths_and_reconciles_precharged_assessments(tmp_path,monkeypatch):
    import json,gzip
    from types import SimpleNamespace
    from lll import ilvis0_control_shards as runner
    path=tmp_path/'definition.json';path.write_text(json.dumps(dict(seed=controls.SEED,realizations_per_family=256)))
    saved={};noted=[]
    context=SimpleNamespace(root=tmp_path,manifest={},directory=tmp_path/'artifacts',input_path=lambda:path,
        save=lambda k,v:saved.update({k:v}),note_file=lambda p:noted.append(p))
    monkeypatch.setattr(runner,'_check_continue',lambda *_:None)
    result=controls.evaluate(dict(identity='analytic',payload=dict(kind='analytic',maximum_assessments=24)),context)
    assert result['passed'] and result['assessments_reserved']==24
    assert len([k for k in saved if k.endswith('-reservation.json')])==24
    records=json.loads(gzip.decompress(noted[0].read_bytes()))
    assert len(records)==24 and all(r['passed'] for r in records)
    assert result['receiver_reads']==result['raw_imu_reads']==result['native_evaluations']==0
