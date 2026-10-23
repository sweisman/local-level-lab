# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from lll.ilvis0_saved_budget_audit import budget_row


def test_evaluator_loads_under_shared_workers_standalone_module_name():
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'lll/ilvis0_saved_budget_audit.py'
    spec=importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.budget_row(material())['prior_useful'] is False


def material():
    return dict(identity='case',result=dict(model=0,profile=False,useful=False,
        numerical_checks_passed=True,future_width_m=[100,200,300]),
        certificate=dict(time_s=438,position_unshared_remainder=[9,18,27],
            lever_unshared_remainder=[1,2,3],unshared_remainder=[10,20,30]),
        result_sha256='a'*64,bound_sha256='b'*64)


def test_saved_budget_share_does_not_relabel_failed_prediction():
    row=budget_row(material())
    assert row['position_share']==[0.9,0.9,0.9]
    assert row['prior_useful'] is False
    assert row['future_width_m']==[100,200,300]


def test_components_must_reconstruct_saved_total():
    value=material();value['certificate']['unshared_remainder'][0]=12
    with pytest.raises(ValueError,match='components'):budget_row(value)


@pytest.mark.parametrize('bad',[float('nan'),-1])
def test_invalid_allowance_is_rejected(bad):
    value=material();value['certificate']['position_unshared_remainder'][0]=bad
    with pytest.raises(ValueError):budget_row(value)


def calibration_material():
    value=material();value['certificate'].update(source_id='source',
        shared_binding='previous-shared-coordinates',reference_binding='reference',
        conditioned_acceleration_change=1.7)
    design=[[0.]*51,[0.]*51];design[0][0]=1.;design[1][0]=-1.
    value['training_region']=dict(parameter_count=51,physical_parameter_count=27,
        lower=[-1.]*51,upper=[1.]*51,center=[0.]*51,inequality_design=design,
        inequality_upper=[.25,.25],future_truth_used=False,source_id='source',binding='reference')
    return value


def test_calibration_projection_is_diagnostic_and_keeps_all_columns():
    from lll.ilvis0_saved_budget_audit import calibration_row
    charges=[];row=calibration_row(calibration_material(),reserve=lambda *x:charges.append(x))
    assert row['projection']['parameter_count']==51
    assert row['projection']['coordinates'][0]['width_ratio']==.25
    assert len(row['projection']['coordinates'])==27 and len(charges)==54
    assert row['prior_useful'] is False and row['new_prediction_bound'] is False


@pytest.mark.parametrize('key,value',[('future_truth_used',True),('source_id','wrong'),
    ('parameter_count',27),('binding','wrong')])
def test_calibration_projection_rejects_wrong_training_binding_before_work(key,value):
    from lll.ilvis0_saved_budget_audit import calibration_row
    material=calibration_material();material['training_region'][key]=value;charges=[]
    with pytest.raises(ValueError):calibration_row(material,reserve=lambda *x:charges.append(x))
    assert not charges


def saved_parent(root):
    from lll.studies.artifacts import encoded,digest
    prefix='data/parent';directory=root/prefix;directory.mkdir(parents=True)
    def write(name,value):
        path=directory/name;path.parent.mkdir(parents=True,exist_ok=True);raw=encoded(value)
        path.write_bytes(raw);return digest(raw)
    inputs={};tasks=[];cases=[]
    for model in range(3):
        for profile in (False,True):
            identity=f'{model}-{int(profile)}';key='case-'+identity
            case=dict(configuration=dict(model=model,profile=profile,gravity=9.81,
                initial_r=[[1,0,0],[0,1,0],[0,0,1]],limits=[.01]*27),
                dv=[[0,0,-.04905],[1,2,3]],dt=[.005,.005])
            path='inputs/'+identity+'.json';sha=write(path,case)
            inputs[key]=dict(path=path,sha256=sha)
            tasks.append(dict(identity=identity,payload=dict(case_key=key)))
            value=calibration_material();value['identity']=identity
            value['result'].update(identity=identity,model=model,profile=profile,
                original_reads=0,optimizer_starts=0)
            value['certificate'].update(lower=[-1.]*27,upper=[1.]*27,normalized_center=[0.]*27)
            reference=dict(binding='reference',parent=dict(source_id='source'))
            artifacts={}
            for name,data in [('future-bound.json',value['certificate']),
                ('reference.json',reference),('stage-02-region.json',value['training_region'])]:
                path='artifacts/'+identity+'/'+name;artifacts[path]=write(path,data)
            cases.append((identity,value['result'],artifacts))
    manifest_sha=write('manifest.json',dict(inputs=inputs,tasks=tasks));results=[]
    for identity,result,artifacts in cases:
        envelope=dict(identity=identity,manifest_sha256=manifest_sha,result=result,
            result_sha256=digest(encoded(result)),artifacts=artifacts)
        path='results/'+identity+'.json'
        results.append(dict(identity=identity,artifact=path,artifact_sha256=write(path,envelope)))
    summary_sha=write('summary.json',dict(passed=False,completed=6,results=results))
    write('completion.json',dict(manifest_sha256=manifest_sha,summary_sha256=summary_sha))
    return prefix


def test_compact_static_inputs_keep_verified_start_and_source_chain(tmp_path):
    from lll.ilvis0_saved_budget_audit import static_materials
    prefix=saved_parent(tmp_path);rows=static_materials(tmp_path,prefix)
    assert len(rows)==6
    for row in rows:
        assert row['first_delta_v']==[0,0,-.04905] and row['first_dt']==.005
        assert row['training_region']['parameter_count']==51
        assert row['prior_acceleration_change']==1.7
        assert len(row['provenance']['case_sha256'])==64
        assert 'dv' not in row and 'dt' not in row


def test_compact_static_inputs_reject_changed_parent_case(tmp_path):
    from lll.ilvis0_saved_budget_audit import static_materials
    prefix=saved_parent(tmp_path);path=tmp_path/prefix/'inputs/0-0.json'
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='hash mismatch'):static_materials(tmp_path,prefix)


def test_static_reference_worker_charges_before_restoring(tmp_path,monkeypatch):
    import json,sqlite3
    from types import SimpleNamespace
    from test_ilvis0_coupled_map import reference
    from lll import ilvis0_coupled_map as coupled
    from lll.ilvis0_saved_budget_audit import evaluate
    ref=reference();r=ref.parent
    value=dict(identity='case',configuration=dict(initial_r=r.initial_r.tolist(),limits=r.limits.tolist(),
        gravity=ref.acceleration.gravity,model=0,profile=True),first_delta_v=ref.acceleration.raw_delta_v.tolist(),
        first_dt=ref.acceleration.period,lower=r.lower.tolist(),upper=r.upper.tolist(),
        center=r.center.tolist(),reference_report=ref.report(),provenance={'case_sha256':'a'*64})
    path=tmp_path/'input.json';path.write_text(json.dumps(value))
    (tmp_path/'manifest.json').write_text('{}');saved={};noted=[]
    context=SimpleNamespace(root=tmp_path,directory=tmp_path/'artifacts',input_path=lambda:path,
        save=lambda n,v:saved.update({n:v}),note_file=lambda p:noted.append(p))
    original=coupled.restore_static_reference
    def restore(*args,**kwargs):
        with sqlite3.connect(context.directory/'allowance.sqlite') as db:
            assert db.execute('SELECT total FROM counts WHERE resource=?',('reference_restorations',)).fetchone()==(1,)
        return original(*args,**kwargs)
    monkeypatch.setattr(coupled,'restore_static_reference',restore)
    task=dict(identity='case',payload=dict(analysis='static_reference',maximum_restorations=1))
    result=evaluate(task,context)
    assert result['passed'] and result['reference_binding']==ref.binding
    assert result['scientific_decision']=='abstain' and result['native_evaluations']==0
    assert noted and saved['reference-check.json']['reference_unchanged'] is True


def width_material():
    value=material();value['result']['future_width_m']=[9.5,18.5,10.5]
    value['certificate'].update(source_id='source',reference_binding='reference',
        position_unshared_remainder=[1.,2.,3.],lever_unshared_remainder=[.5]*3,
        unshared_remainder=[1.5,2.5,3.5])
    value['training_region']=dict(parameter_count=51,binding='reference',source_id='source',
        coordinate_scale=[2.,3.,1.],arithmetic_allowance=.25,future_truth_used=False)
    value['future']=dict(parameter_count=51,shared_binding='reference',source_id='source',
        future_truth_used=False,lower=[-4.75,-9.25,-5.25],upper=[4.75,9.25,5.25],
        certificates=[dict(upper='2',negated_lower='1') for _ in range(3)])
    return value


def test_width_budget_converts_native_coordinates_to_metres_and_keeps_all_terms():
    from lll.ilvis0_saved_budget_audit import width_budget
    result=width_budget(width_material())
    assert [r['affine_width_m'] for r in result['axes']]==[3.,3.,3.]
    assert [r['position_width_m'] for r in result['axes']]==[4.,12.,6.]
    assert [r['unshared_width_m'] for r in result['axes']]==[6.,15.,7.]
    assert all(r['arithmetic_width_m']==.5 and r['endpoint_rounding_width_m']==0 for r in result['axes'])
    assert result['axes'][0]['unshared_fraction']==6/9.5
    assert not result['new_prediction_bound'] and result['scientific_decision']=='abstain'


def test_width_budget_preserves_the_parents_outward_rounded_width():
    import math
    from fractions import Fraction as F
    from lll.ilvis0_saved_prediction_audit import endpoint
    from lll.ilvis0_saved_budget_audit import width_budget
    value=width_material();value['future']['upper'][0]=math.nextafter(4.75,math.inf)
    exact=F(value['future']['upper'][0])-F(value['future']['lower'][0])
    value['result']['future_width_m'][0]=endpoint(exact,True)
    assert float(exact)!=value['result']['future_width_m'][0]
    row=width_budget(value)['axes'][0]
    assert row['width_m']==value['result']['future_width_m'][0]
    assert row['reported_rounding_width_m']>0


@pytest.mark.parametrize('change',['source','scale','future','width','certificate'])
def test_width_budget_rejects_mixed_units_source_or_changed_envelope(change):
    from lll.ilvis0_saved_budget_audit import width_budget
    value=width_material()
    if change=='source':value['future']['source_id']='elsewhere'
    elif change=='scale':value['training_region']['coordinate_scale'][0]=0.
    elif change=='future':value['future']['future_truth_used']=True
    elif change=='width':value['result']['future_width_m'][0]+=1.
    else:value['future']['certificates'][0]['upper']='200'
    with pytest.raises(ValueError):width_budget(value)
