# SPDX-License-Identifier: AGPL-3.0-or-later
from types import SimpleNamespace
import json
from lll import ilvis0_relaxed_width as diagnostic
from test_ilvis0_transform_audit import fixture


def context(tmp_path,monkeypatch,anchor=None):
    from lll import ilvis0_control_shards
    monkeypatch.setattr(ilvis0_control_shards,'_check_continue',lambda *_:None)
    result,training,future=fixture()
    bundle=dict(result=result,training=training,future=future,
        anchor=[0.]*51 if anchor is None else anchor,target_width_m=[.1]*3)
    path=tmp_path/'case.json';path.write_text(json.dumps(bundle));saved={}
    ctx=SimpleNamespace(root=tmp_path,manifest={},input_path=lambda:path,
        save=lambda name,value:saved.update({name:value}))
    task=dict(identity='fixture',payload=dict(maximum_proposals=6))
    return task,ctx,saved


def test_exact_feasible_witnesses_reconcile_with_old_supports(tmp_path,monkeypatch):
    task,ctx,saved=context(tmp_path,monkeypatch)
    row=diagnostic.evaluate(task,ctx)
    assert row['passed'] and row['supported'] and row['lp_proposals']==6
    assert row['exact_baseline_supports']==6 and len(row['axes'])==3
    assert all(a['affine_lower_width']=='0' and a['relaxed_lower_width']=='5/16' for a in row['axes'])
    assert all(a['lower_exceeds_target'] for a in row['axes'])
    assert len(saved['witnesses.json']['proposals'])==6
    assert row['physical_realizability_established'] is False


def test_invalid_anchor_is_recorded_without_any_lp_proposal(tmp_path,monkeypatch):
    task,ctx,saved=context(tmp_path,monkeypatch,anchor=[2.]*51)
    row=diagnostic.evaluate(task,ctx)
    assert row['passed'] and not row['supported'] and row['lp_proposals']==0
    assert row['reason']=='saved anchor is not exactly feasible'
    assert 'witnesses.json' not in saved


def test_unsuccessful_lp_is_not_treated_as_an_optimum(tmp_path,monkeypatch):
    import scipy.optimize
    monkeypatch.setattr(scipy.optimize,'linprog',lambda *_args,**_kwargs:SimpleNamespace(success=False,status=1,message='finite stop',x=None))
    task,ctx,_=context(tmp_path,monkeypatch)
    row=diagnostic.evaluate(task,ctx)
    assert row['passed'] and not row['supported'] and row['lp_proposals']==6
    assert row['axes']==[] and row['unsupported_proposals']==6


def test_positive_and_negative_coefficients_recover_known_widths(tmp_path,monkeypatch):
    task,ctx,_=context(tmp_path,monkeypatch)
    path=ctx.input_path();bundle=json.loads(path.read_text())
    for axis,index,coefficient,width in ((0,0,1.,1.),(1,18,-2.,2.)):
        future=bundle['future'];future['jacobian'][axis][index]=coefficient
        cert=future['envelope']['certificates'][axis]
        cert['upper']=str(int(width));cert['negated_lower']=str(int(width))
        future['envelope']['lower'][axis]=-width-.15625
        future['envelope']['upper'][axis]=width+.15625
    bundle['result']['future_lower_m']=future['envelope']['lower']
    bundle['result']['future_upper_m']=future['envelope']['upper']
    path.write_text(json.dumps(bundle))
    row=diagnostic.evaluate(task,ctx)
    assert row['supported']
    assert [a['affine_lower_width'] for a in row['axes']]==['2','4','0']
    assert all(a['affine_gap']=='0' for a in row['axes'])
