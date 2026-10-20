# SPDX-License-Identifier: AGPL-3.0-or-later
"""Breaks caught: uncharged work, rounded feasibility and omitted error blocks."""
from fractions import Fraction as F
from types import SimpleNamespace
import math
import pytest
from lll import ilvis0_calibration_map_diagnostic as diagnosis


def test_standalone_frozen_adapter_keeps_qualified_helper_imports():
    import importlib.util
    import sys
    spec=importlib.util.spec_from_file_location('_calibration_map_frozen_fixture',diagnosis.__file__)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module)
        budget=module.Allowance(dict(lp=1,maps=1,checks=4),lambda _:None)
        region=module.CountedRegion([-1.],[1.],[],[],budget)
        assert module.propose(region,[1.],budget)['point']==[1.]
    finally:sys.modules.pop(spec.name,None)


def allowance(**limits):
    events=[]
    return diagnosis.Allowance(dict(lp=6,maps=7,checks=41000)|limits,events.append),events


def test_exact_repair_and_independent_verification_are_both_precharged():
    budget,events=allowance();region=diagnosis.CountedRegion([-1,-1],[1,1],[[1,1]],[F(1,4)],budget)
    witness=region.repair([1,1],[0,0])
    assert witness['point']==(F(1,8),F(1,8))
    assert diagnosis.independent_slacks(region,witness['point'],budget)==(F(0),F(-7,8),F(-7,8),F(-9,8),F(-9,8))
    assert budget.counts==dict(lp=0,maps=0,checks=20)
    assert [r['counts']['checks'] for r in events]==[5,10,15,20]
    tiny,_=allowance(checks=4)
    with pytest.raises(ValueError,match='allowance'):
        diagnosis.CountedRegion([-1,-1],[1,1],[[1,1]],[0],tiny).slacks([0,0])
    assert tiny.counts['checks']==0


def test_persistence_failure_prevents_charged_work_and_counter_change():
    def reject(_):raise OSError('cannot save reservation')
    budget=diagnosis.Allowance(dict(lp=1,maps=1,checks=1),reject)
    with pytest.raises(OSError):budget.reserve('maps',1)
    assert budget.counts==dict(lp=0,maps=0,checks=0)


def physical_reference(mapper):
    return SimpleNamespace(parent=SimpleNamespace(lower=[-1.]*27,upper=[1.]*27),
        normalized_values_at=mapper)


def test_binary_rounding_is_saved_before_map_and_never_clipped():
    budget,events=allowance();saved={}
    def mapper(point):
        assert 'physical-conversion.json' in saved
        assert events[-1]['counts']['maps']==1
        assert point[0]==float(F(1,3))
        return [point[0]**2]+[0.]*23
    point=[F(1,3)]+[F(0)]*77
    out=diagnosis.physical_map(physical_reference(mapper),point,budget,lambda k,v:saved.update({k:v}))
    assert out['supported'] and out['original_coordinates'][0]=='1/3'
    assert out['rounding_difference'][0]==str(F(float(F(1,3)))-F(1,3))
    assert out['physical'][0]==float(F(1,3)) and out['errors'][0]==float(F(1,3))**2
    assert budget.counts['maps']==1
    too_high=[F(1)+F(1,2**54)]+[F(0)]*77
    rejected=diagnosis.physical_map(physical_reference(lambda _:pytest.fail('outside exact domain')),
        too_high,budget,lambda k,v:None)
    assert not rejected['supported'] and budget.counts['maps']==1


def test_nonfinite_map_and_wrong_component_count_are_not_silently_accepted():
    for errors in ([math.nan]+[0.]*23,[0.]*23):
        budget,_=allowance()
        with pytest.raises(ValueError):
            diagnosis.physical_map(physical_reference(lambda _:errors),[F(0)]*78,budget,lambda k,v:None)


def test_complete_map_lifts_even_outside_the_relaxed_box_so_violations_remain_visible():
    # A diagonal matrix with one changed entry: exact products are hand known.
    matrix=[]
    for i in range(9):
        row=[0.]*51
        if i==0:row[42]=1.
        matrix.append(dict(constant=str(int(i in (0,4,8))),coefficients=row))
    cuts=dict(matrix_affine=matrix,gain_limits=[F(1,2),0,0])
    point=[F(0)]*51;point[18]=F(1,2);point[42]=F(1)
    lifted=diagnosis.lift_without_domain_repair(cuts,point)
    assert len(lifted)==78 and lifted[:51]==tuple(point)
    assert lifted[51:60]==(F(1,2),)+(F(0),)*8
    assert lifted[60:66]==(F(25,4),F(0),F(0),F(0),F(0),F(0))
    budget,_=allowance()
    region=diagnosis.CountedRegion([-1.]*78,[1.]*78,[],[],budget)
    assert max(diagnosis.independent_slacks(region,lifted,budget))==F(21,4)


def test_each_error_block_and_rounding_are_reported_without_ignoring_cancellation():
    zero=[0.]*27
    bound=dict(previous_coefficients=[[2.,0,0,3.,0,0]]*3,
        acceleration_coefficients=[[4.]+[0.]*8]*3,transform_coefficients=[[5.]+[0.]*8]*3)
    future=dict(jacobian=[[1.]+[0.]*26]*3,bound=bound)
    source=dict(coordinate_scale=[2.,1.,.5])
    before=[F(0)]*78;after=before.copy()
    for index,value in ((0,1),(27,1),(30,-1),(33,1),(42,-1)):after[index]=F(value)
    rows=diagnosis.changes(source,future,before,after)
    assert rows[0]['blocks']==dict(physical='2',velocity_clock='4',lever='-6',acceleration='8',force_matrix='-10')
    assert [r['total'] for r in rows]==['-2','-1','-1/2']
    assert rows[0]['absolute_block_sum']=='30'
    assert rows[0]['total']!=rows[0]['absolute_block_sum']


def test_reference_identity_mismatch_is_rejected_before_oracle_work():
    ref=SimpleNamespace(report=lambda:dict(binding='fresh',parent=dict(binding='parent')))
    diagnosis.require_reference(ref,dict(binding='fresh',parent=dict(binding='parent')))
    with pytest.raises(ValueError,match='source'):
        diagnosis.require_reference(ref,dict(binding='different',parent=dict(binding='parent')))


def test_lp_reservation_is_saved_before_proposal_and_no_retry_occurs():
    budget,events=allowance(lp=1)
    region=diagnosis.CountedRegion([-1.],[1.],[],[],budget)
    answer=diagnosis.propose(region,[1.],budget)
    assert answer['success'] and answer['point']==[1.]
    assert events[0]['counts']['lp']==1
    with pytest.raises(ValueError,match='allowance'):diagnosis.propose(region,[1.],budget)


def test_boundary_collapse_remains_an_anchor_witness():
    budget,_=allowance();region=diagnosis.CountedRegion([-1.],[1.],[[1.]],[0.],budget)
    witness=region.repair([1.],[0.])
    assert witness['mixing_fraction']==1 and witness['point']==(F(0),)


def test_reservation_audit_rejects_missing_or_changed_cumulative_charges():
    limits=dict(lp=1,maps=1,checks=100);budget,events=allowance(**limits)
    budget.reserve('maps',1);budget.reserve('checks',24)
    assert diagnosis.reconcile(events,budget.counts,limits)==dict(lp=0,maps=1,checks=24)
    with pytest.raises(ValueError):diagnosis.reconcile(events[:-1],budget.counts,limits)
    events[1]['counts']['checks']=23
    with pytest.raises(ValueError):diagnosis.reconcile(events,budget.counts,limits)


def test_portable_full_adapter_preserves_every_column_and_precharges_all_map_work(tmp_path,monkeypatch):
    import json
    from pathlib import Path
    from saved_prediction_fixtures import generated_context
    from lll import ilvis0_product_prediction as prediction,ilvis0_rotation_products as products
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_sharded_native import read
    root=Path(__file__).resolve().parents[2]
    task,context,saved=generated_context(root/'docs/ilvis0-column-orientation-prediction',tmp_path,monkeypatch)
    bundle=read(context.input_path());case=read(context.input_path('case'))
    box=sector(bundle['result']['task']['sector']);case['truth']=box['center'].tolist()
    ref=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center'])
    future=bundle['future'];parent=ref.parent
    cuts=products.build(ref.transform.report(),initial_r=parent.initial_r.tolist(),limits=parent.limits.tolist(),
        physical_center=parent.center.tolist(),lower=future['lower'],upper=future['upper'],
        reference_binding=parent.binding,source_id=parent.source_id,numerical_allowance=1e-8)
    bundle['training']['region']=prediction.extend(bundle['training'],future,cuts)
    future.update(parameter_count=78,lower=cuts['lower'],upper=cuts['upper'])
    bundle.update(cuts=cuts);bundle['result'].update(parameter_count=78,truth_in_sector=True)
    case_path=tmp_path/'case.json';case_path.write_text(json.dumps(case))
    path=tmp_path/'adapter.json';path.write_text(json.dumps(bundle))
    context.input_path=lambda key=None:case_path if key else path
    task['payload']=dict(case_key='case',work_limits=dict(lp=6,maps=7,checks=41000))
    from lll import ilvis0_transform_native as native
    monkeypatch.setattr(native,'enclose',lambda *_a,**_k:pytest.fail('no native work'))
    result=diagnosis.evaluate(task,context)
    assert result['passed'] and result['supported_witnesses']==6 and result['mapped_witnesses']==6
    assert result['work']==dict(lp=6,maps=7,checks=9677)
    assert result['native_evaluations']==result['bound_evaluations']==0
    assert len(saved['witness-01-exact.json']['point'])==78
    assert len(saved['witness-01-physical-map.json']['errors'])==24
    assert diagnosis.reconcile([v for k,v in saved.items() if k.startswith('reservation-')],
        result['work'],task['payload']['work_limits'])==result['work']
