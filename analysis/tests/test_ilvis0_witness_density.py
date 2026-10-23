# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


def test_density_recipe_is_finite_and_ends_before_unused_prediction():
    from lll.ilvis0_witness_density import recipe,validate_recipe
    value=recipe();validate_recipe(value)
    assert value['times_s']==list(map(float,range(2,291)))+[438.]
    assert value['identities']==18 and value['maximum_native_batches']==18
    assert value['maximum_packet_visits']==501120000
    assert value['times_s'][-2]==290. and value['future_observations_used'] is False
    with pytest.raises(ValueError):validate_recipe(dict(value,maximum_native_batches=19))


def test_overlap_reports_ambiguity_without_inventing_observations():
    from lll.ilvis0_witness_density import interval_overlap
    values=[[[0.,0.,0.]],[[.5,-.25,0.]],[[1.,.25,0.]]]
    result=interval_overlap(values,[2.],[1.,1.,1.],allowance_m=1.,guard_m=.00001)
    assert result['could_share_all'] and result['guaranteed_overlap_all']
    assert F(result['axes'][0]['minimum_guaranteed_width_exact'])>0
    assert result['observations_created']==0 and result['outer_bound_qualified'] is False


def test_overlap_handles_guard_band_and_axis_specific_gaps():
    from lll.ilvis0_witness_density import interval_overlap
    values=[[[0.,0.,0.]],[[2.00001,0.,0.]],[[0.,3.,0.]]]
    result=interval_overlap(values,[10.],[1.,1.,1.],allowance_m=1.,guard_m=.00001)
    assert result['axes'][0]['could_share_all'] and not result['axes'][0]['guaranteed_overlap_all']
    assert not result['could_share_all'] and result['axes'][1]['first_disjoint_s']==10.
    with pytest.raises(ValueError):interval_overlap(values,[10.],[1.,1.,-1.],allowance_m=1.,guard_m=0.)


def test_fixed_predictions_require_bitwise_original_epoch_values():
    from lll.ilvis0_witness_density import check_reference
    source=dict(times_s=[2.,10.,438.],prediction=[[0.,0.,0.],[1.,1.,1.],[2.,2.,2.]])
    output=dict(prediction=[[0.,0.,0.],[5.,5.,5.],[1.,1.,1.],[2.,2.,2.]])
    check_reference(source,output,[2.,3.,10.,438.])
    output['prediction'][-1][0]=2.0000000001
    with pytest.raises(ValueError,match='original'):check_reference(source,output,[2.,3.,10.,438.])


def test_missing_density_point_blocks_complete_comparison():
    from lll.ilvis0_witness_density import assess
    rows=[dict(model=m,profile=p,role=role,passed=True) for m in range(3)
        for p in (False,True) for role in ('origin','low','high')]
    assert assess(rows)['complete']
    assert not assess(rows[:-1])['complete']
    with pytest.raises(ValueError):assess(rows+[rows[0]])


@pytest.mark.parametrize('failure',[None,'binding','epoch'])
def test_fixed_worker_charges_before_call_and_preserves_failed_output(tmp_path,monkeypatch,failure):
    import hashlib
    import numpy as np
    from test_ilvis0_witness_search import _material
    from lll import ilvis0_witness_density as density,ilvis0_control_shards as runner
    from lll import ilvis0_shape,ilvis0_density_native_probes
    from lll.ilvis0_receipt_journal import encoded
    bundle,case,spec=_material();spec.update(bundle_key='bundle',point_key='point',role='low')
    paths={};paths['case']=tmp_path/'case.json';paths['case'].write_bytes(encoded(case))
    sha=hashlib.sha256(paths['case'].read_bytes()).hexdigest()
    bundle['problem']['binding']['case_sha256']='d'*64 if failure=='binding' else sha
    source=dict(binding=bundle['problem']['binding'],times_s=bundle['problem']['training_s']+[438.],
        point=bundle['initial'],prediction=[[0.,0.,0.]]*6,status=0)
    for key,value in (('recipe',density.recipe()),('bundle',bundle),('point',dict(record=source))):
        paths[key]=tmp_path/(key+'.json');paths[key].write_bytes(encoded(value))
    class Context:
        root=tmp_path/'study';shard=0
        manifest=dict(sources={'analysis/lll/ilvis0_tangent.cpp':'b'*64},inputs={'case':dict(sha256=sha)})
        def __init__(self):self.saved={};self.charges=[]
        def input_path(self,key=None):return paths[key or 'recipe']
        def save(self,name,value):self.saved[name]=value
        def charge(self,**value):self.charges.append(value)
    context=Context();monkeypatch.setattr(runner,'_check_continue',lambda *args:None)
    monkeypatch.setattr(ilvis0_shape,'load_tangent',lambda directory:(None,dict(compiler='test compiler',source_sha256='b'*64)))
    def query(kernel,config,theta,dv,dt,times,point,reserve,save):
        assert context.charges and context.saved['point-before-native.json']['saved_before_native']
        reserve(len(times),len(times)*len(dt));prediction=np.zeros((len(times),3))
        if failure=='epoch':prediction[-1,0]=1e-9
        raw=dict(status=0,point=np.asarray(point),prediction=prediction,jacobian=np.zeros((len(times),3,27)),
            classification=dict(counter_verified=True));save(raw);return raw
    monkeypatch.setattr(ilvis0_density_native_probes,'query',query)
    if failure:
        with pytest.raises(ValueError):density.evaluate(dict(identity='test',payload=spec),context)
        assert bool(context.charges)==(failure=='epoch')
        if failure=='epoch':assert 'native-output.json' in context.saved
    else:
        result=density.evaluate(dict(identity='test',payload=spec),context)
        assert result['passed'] and result['optimizer_starts']==0
        assert context.charges==[dict(native_calls=1,packet_visits=27840000)]
