# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace
import pytest
from lll import ilvis0_coupled_prediction as prediction
from lll.ilvis0_interval_calibration import Jet
from test_ilvis0_product_prediction import fixture as product_fixture


def fixture():
    _,_,_,region=product_fixture();saved=product_fixture()[1]
    saved.update(parameter_count=78,lower=region['lower'],upper=region['upper'])
    saved['envelope'].update(parameter_count=78,original_parameter_count=51,
        rotation_product_binding=region['rotation_product_binding'])
    report=dict(binding='map',reference_binding=region['binding'],source_id=region['source_id'])
    model=SimpleNamespace(report=lambda:report,bound=lambda _a,_b:[Jet.constant(0.)]*24)
    cuts=prediction.build(model,saved['lower'][:27],saved['upper'][:27],reserve=lambda:None)
    return dict(region=region),saved,cuts,report


def test_independent_export_audit_checks_every_coefficient_and_exact_upper_bound():
    training,saved,cuts,report=fixture()
    check=prediction.audit_cuts(cuts,report,saved['lower'][:27],saved['upper'][:27])
    assert check['rows']==48 and check['passed']
    region=prediction.extend(training,saved,cuts)
    assert len(region['inequality_design'])==len(training['region']['inequality_design'])+48
    assert all(len(row)==78 for row in region['inequality_design'])
    assert region['center']==training['region']['center']
    assert region['inequality_design'][-48:]==[row+[0.]*27 for row in cuts['design']]


@pytest.mark.parametrize('change',['gradient','row','bound','source','box'])
def test_changed_cut_proof_is_rejected_before_contraction_or_support(change):
    _,saved,cuts,report=fixture();cuts=deepcopy(cuts)
    if change=='gradient':cuts['proof']['derivatives'][0][0][1]=1.
    elif change=='row':cuts['design'][0][0]=1.
    elif change=='bound':cuts['upper'][0]=1.
    elif change=='source':cuts['source_id']='elsewhere'
    else:cuts['physical_lower'][0]=-.5
    with pytest.raises(ValueError):prediction.audit_cuts(cuts,report,saved['lower'][:27],saved['upper'][:27])


def test_future_audit_preserves_every_original_error_term_and_checks_new_duals():
    from lll.ilvis0_product_prediction import rebuild
    training,saved,cuts,report=fixture();region=prediction.extend(training,saved,cuts)
    future=rebuild(region,saved,region['lower'],region['upper'],reserve=lambda _:None)
    future['envelope']['coupled_map_binding']=cuts['binding']
    receipt=prediction.audit_cuts(cuts,report,saved['lower'][:27],saved['upper'][:27])
    result=prediction.audit_future(training,saved,region,future,cuts,cut_audit=receipt)
    assert result['exact_supports_checked']==6 and result['parameter_count']==78
    future['bound']['unshared_remainder'][0]=0.
    with pytest.raises(ValueError):prediction.audit_future(training,saved,region,future,cuts,cut_audit=receipt)


def test_actual_support_work_is_reserved_before_every_proposal_and_independent_audit(monkeypatch):
    from lll import ilvis0_affine_support as affine,ilvis0_saved_prediction_audit as exact
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_product_prediction import rebuild
    training,saved,cuts,report=fixture();region=prediction.extend(training,saved,cuts)
    calls=[];events=[];original_upper=affine.upper;original_support=exact.support
    def upper(*args):calls.append('upper');return original_upper(*args)
    def support(*args):calls.append('audit');return original_support(*args)
    monkeypatch.setattr(affine,'upper',upper);monkeypatch.setattr(exact,'support',support)
    budget=Allowance(dict(proposals=6,supports=24),events.append)
    future=rebuild(region,saved,region['lower'],region['upper'],
        reserve=lambda _:budget.reserve(dict(proposals=1,supports=3)))
    future['envelope']['coupled_map_binding']=cuts['binding']
    receipt=prediction.audit_cuts(cuts,report,saved['lower'][:27],saved['upper'][:27])
    budget.reserve(dict(supports=6));prediction.audit_future(training,saved,region,future,cuts,cut_audit=receipt)
    assert len(calls)==24 and calls.count('audit')==6
    assert events[-1]['counts']==dict(proposals=6,supports=24)


def test_portable_adapter_uses_saved_packets_without_native_predictions(tmp_path,monkeypatch):
    import json
    from pathlib import Path
    from saved_prediction_fixtures import generated_context
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_transform_native import make_reference
    from lll import ilvis0_product_prediction as old_prediction,ilvis0_rotation_products as products
    root=Path(__file__).resolve().parents[2]
    task,context,saved_artifacts=generated_context(root/'docs/ilvis0-column-orientation-prediction',tmp_path,monkeypatch)
    bundle=read(context.input_path());case=read(context.input_path('case'));box=sector(bundle['result']['task']['sector'])
    reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center']);r=reference.parent
    future=bundle['future']
    product_cuts=products.build(reference.transform.report(),initial_r=r.initial_r.tolist(),limits=r.limits.tolist(),
        physical_center=r.center.tolist(),lower=future['lower'],upper=future['upper'],
        reference_binding=r.binding,source_id=r.source_id,numerical_allowance=1e-8)
    region=old_prediction.extend(bundle['training'],future,product_cuts)
    future=old_prediction.rebuild(region,future,region['lower'],region['upper'],reserve=lambda _:None)
    bundle.update(training=dict(region=region),future=future,product_cuts=product_cuts)
    bundle['result'].update(parameter_count=78,truth_in_sector=True)
    case['truth']=box['center'].tolist()
    path=tmp_path/'product.json';path.write_text(json.dumps(bundle));case_path=tmp_path/'generated.json';case_path.write_text(json.dumps(case))
    context.input_path=lambda key=None:case_path if key else path
    task['payload']=dict(case_key='case',limits=dict(setups=1,intervals=2,coupling_audits=1,
        contractions=1,proposals=6,supports=24,truth_audits=1))
    from lll import ilvis0_transform_native as native
    monkeypatch.setattr(native,'enclose',lambda *_a,**_k:pytest.fail('no native prediction bounds'))
    result=prediction.evaluate(task,context)
    assert result['passed'] and not result['excluded']
    assert result['work']==task['payload']['limits']
    assert result['known_truth_retained'] and result['coupling_rows_checked']==48
    assert result['native_evaluations']==result['bound_evaluations']==0
    assert list(saved_artifacts).index('future.json')<list(saved_artifacts).index('independent-audit.json')
