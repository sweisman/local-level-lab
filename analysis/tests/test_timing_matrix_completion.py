# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import pytest


def policy():return importlib.import_module('lll.timing_matrix_completion')


def fixture():
    from lll import timing_feasible_matrix_study as m
    rows=m.tasks();return dict(verified=True,selected=48,complete=44,native_qualified=False,
        manifest_sha256='625e8b32523807a3ca6f6dcb28665dbc6818e7e3435366fd36e6f4d60fa3b5cc',
        summary_sha256='690b3db8286b54c6ae4358f08969a1424586497b9f4e49f4f4f6e85f6cff0dff',
        failures=[dict(identity=t['identity'],reason='charged work interrupted; not retried') for t in rows[:4]],
        rows=[dict(identity=t['identity'],passed=True) for t in rows[4:]],
        pairs=[dict(passed=i>=2) for i in range(24)],verification_failures=[])


def test_matrix_completion_is_four_new_starts_without_reopening_closed_matrix():
    from lll import timing_feasible_matrix_study as m
    p=policy();rows=p.tasks();c=p.configuration()
    assert rows==m.tasks()[:4] and p.IDENTITY!=m.IDENTITY
    assert c['maximum_fits']==4 and c['maximum_wall_s']==3600.
    assert c['workers']==4 and c['threads']==1 and c['maximum_evaluations']==200
    assert c['linear_solves_per_fit']==620 and c['retries']==0
    assert sum(t['limits']['native_calls'] for t in rows)==239816
    assert sum(t['limits']['packet_visits'] for t in rows)==1506051012
    assert p.expected_point_count==1 and p.require_original_match is False
    assert p.allowed_source_updates==()


@pytest.mark.parametrize('change',[None,'reason','missing','fit','extra','pairs','summary','manifest','cells'])
def test_matrix_completion_only_accepts_exact_four_runtime_interruptions(change):
    p=policy();r=fixture()
    if change=='reason':r['failures'][0]['reason']='numerical failure'
    elif change=='missing':r['failures'].pop()
    elif change=='fit':r['rows'][0]['passed']=False
    elif change=='extra':r['rows'][0]['identity']=r['failures'][0]['identity']
    elif change=='pairs':r['pairs'][2]['passed']=False
    elif change=='summary':r['summary_sha256']='0'*64
    elif change=='manifest':r['manifest_sha256']='0'*64
    elif change=='cells':r['verification_failures']=[{'failed':True}]
    if change is None:p.verify_interrupted_matrix(r)
    else:
        with pytest.raises(ValueError):p.verify_interrupted_matrix(r)


def test_matrix_completion_uses_same_shared_execution_and_gate(monkeypatch):
    from lll import timing_optimizer_native_study as shared,timing_feasible_matrix_study as m
    p=policy();task={};context=object();seen=[]
    def run(t,c,*,definition):
        assert t is task and c is context;seen.append(definition);return {'delegated':True}
    monkeypatch.setattr(shared,'run_task',run)
    assert p.evaluate(task,context)=={'delegated':True} and seen==[p]
    assert p.GATE==m.GATE and p.GATE_MANIFEST==m.GATE_MANIFEST and p.GATE_SUMMARY==m.GATE_SUMMARY
    assert p.verify_gate is m.verify_gate and p.computational_payload is m.computational_payload


def test_matrix_completion_reference_is_only_the_original_binding_in_missing_slice():
    from lll.timing_optimizer_matrix_study import ORIGINAL_POPULATION
    p=policy();work=p.tasks();points=[dict(identity=str(i),payload=dict(t['payload'],
        role='calibration',population_sha256=ORIGINAL_POPULATION)) for i,t in enumerate(work)]
    points.append(dict(identity='elsewhere',payload=dict(draw_seed=281474976810726,case={},
        role='calibration',population_sha256=ORIGINAL_POPULATION)))
    assert p.select_reference(points[:1]+points[4:])==points[:1]
    with pytest.raises(ValueError):p.select_reference(points)
    with pytest.raises(ValueError):p.select_reference(points[4:])
