# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path
import numpy as np
import pytest
from lll import ilvis0_coupled_subdivision as subdivision


def parent_fixture(tmp_path,monkeypatch):
    from saved_prediction_fixtures import generated_context
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_transform_native import make_reference
    from lll import ilvis0_product_prediction as product,ilvis0_rotation_products as products
    from lll.ilvis0_physical_partition import split
    root=Path(__file__).resolve().parents[2]
    task,context,artifacts=generated_context(root/'docs/ilvis0-column-orientation-prediction',tmp_path,monkeypatch)
    bundle=read(context.input_path());case=read(context.input_path('case'));box=sector(bundle['result']['task']['sector'])
    reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center']);r=reference.parent
    old=bundle['future']
    cuts=products.build(reference.transform.report(),initial_r=r.initial_r.tolist(),limits=r.limits.tolist(),
        physical_center=r.center.tolist(),lower=old['lower'],upper=old['upper'],
        reference_binding=r.binding,source_id=r.source_id,numerical_allowance=1e-8)
    region=product.extend(bundle['training'],old,cuts)
    future=product.rebuild(region,old,region['lower'],region['upper'],reserve=lambda _:None)
    case['truth']=box['center'].tolist();case['truth'][0]=.25;case['truth'][1]=-.25
    bundle.update(training=dict(region=region),future=future,product_cuts=cuts,
        partition=split(future['lower'][:27],future['upper'][:27],axes=(0,1)))
    bundle['result'].update(parameter_count=78,truth_in_sector=True,
        known_shared_error=reference.normalized_values_at(case['truth']).tolist())
    path=tmp_path/'parent.json';path.write_text(json.dumps(bundle));case_path=tmp_path/'case.json';case_path.write_text(json.dumps(case))
    context.input_path=lambda key=None:case_path if key else path
    return task,context,artifacts,bundle,reference


@pytest.mark.parametrize('child_index,contains_truth',[(0,False),(2,True)])
def test_all_children_are_processed_without_using_truth_to_choose_their_boxes(tmp_path,monkeypatch,child_index,contains_truth):
    task,context,artifacts,bundle,reference=parent_fixture(tmp_path,monkeypatch)
    parent=task['identity'];task['identity']=parent+f'-xy-{child_index}'
    task['payload']=dict(parent_identity=parent,case_key='case',child_index=child_index,parent_children=4,
        limits=dict(partition_audits=1,setups=1,intervals=2,coupling_audits=1,contractions=1,proposals=6,supports=24,truth_audits=1))
    from lll import ilvis0_transform_native as native
    monkeypatch.setattr(native,'enclose',lambda *_a,**_k:pytest.fail('no native work'))
    result=subdivision.evaluate(task,context)
    assert result['passed'] and not result['excluded']
    assert result['truth_in_child'] is contains_truth and result['known_truth_retained']
    assert result['work']==task['payload']['limits']
    assert artifacts['source-map.json']['reference_binding']==reference.binding
    assert artifacts['coupling.json']['physical_lower']==bundle['partition']['children'][child_index]['lower']
    assert artifacts['partition-audit.json']['children']==4
    assert 'future.json' in artifacts and 'truth-audit.json' in artifacts
    assert list(artifacts).index('future.json')<list(artifacts).index('truth-audit.json')
    assert result['native_evaluations']==result['original_reads']==0
