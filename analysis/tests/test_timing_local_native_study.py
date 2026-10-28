# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def fixture():
    from lll import timing_optimizer_local_study as local
    from lll.timing_optimizer_native_study import NUMERICAL
    sources={k:'a'*64 for k in NUMERICAL};environment={'same':True}
    report=dict(verified=True,analytical_qualified=True,complete=44,fit_passed=36,controls_correct=8,
        failures=[],pairs=[dict(agreement=True) for _ in range(9)],
        manifest_sha256=local.GATE_MANIFEST,summary_sha256=local.GATE_SUMMARY)
    return local,report,dict(sources=sources,environment=environment),sources,environment


def test_local_native_retains_original_cases_and_finite_caps():
    from lll import timing_optimizer_local_study as local,timing_optimizer_native_study as original
    assert local.tasks()==original.tasks() and len(local.tasks())==4
    a=local.configuration();b=original.configuration()
    assert {k:v for k,v in a.items() if k not in ('id','scope')}=={k:v for k,v in b.items() if k not in ('id','scope')}
    assert sum(t['limits']['native_calls'] for t in local.tasks())==239816
    assert sum(t['limits']['packet_visits'] for t in local.tasks())==1506051012


@pytest.mark.parametrize('change',[None,'count','pairs','source','environment','manifest','failed'])
def test_local_native_requires_new_complete_analytical_gate(change):
    local,r,b,s,e=fixture();r=copy.deepcopy(r);b=copy.deepcopy(b)
    if change=='count':r['complete']=40
    elif change=='pairs':r['pairs'].pop()
    elif change=='source':b['sources'][next(iter(s))]='b'*64
    elif change=='environment':b['environment']={}
    elif change=='manifest':r['manifest_sha256']='c'*64
    elif change=='failed':r['analytical_qualified']=False
    if change is None:local.verify_gate(r,b,s,e)
    else:
        with pytest.raises(ValueError,match='analytical qualification'):local.verify_gate(r,b,s,e)


def test_local_native_delegates_execution_to_shared_worker(monkeypatch):
    from lll import timing_optimizer_local_study as local,timing_optimizer_native_study as shared
    task={};context=object();seen=[]
    def run(t,c,*,definition):
        assert t is task and c is context
        seen.append(definition);return {'delegated':True}
    monkeypatch.setattr(shared,'run_task',run)
    assert local.evaluate(task,context)=={'delegated':True} and seen==[local]
