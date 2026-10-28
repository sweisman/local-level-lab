# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite matrix policy: computational cases unchanged, corrected native gate."""
import copy
import importlib

import pytest


def policy():return importlib.import_module('lll.timing_feasible_matrix_study')


def test_feasible_matrix_keeps_48_original_cases_and_closed_allowances():
    from lll import timing_optimizer_matrix_study as old
    m=policy();rows=m.tasks();cfg=m.configuration()
    assert rows==old.tasks() and len(rows)==48
    assert len({m.pair_key(t) for t in rows})==24
    assert {m.column_count(t['payload']['case']) for t in rows}=={26,27}
    assert (cfg['workers'],cfg['threads'],cfg['maximum_fits'],cfg['maximum_wall_s'])==(4,1,48,7200.)
    assert cfg['maximum_evaluations']==200 and cfg['linear_solves_per_fit']==620 and cfg['retries']==0
    assert sum(t['limits']['native_calls'] for t in rows)==2877792
    assert sum(t['limits']['packet_visits'] for t in rows)==18072612144
    assert m.IDENTITY!=old.IDENTITY and m.GATE=='docs/timing-feasible-native-regression'
    assert m.require_original_match is False and m.expected_point_count==4
    assert set(m.allowed_source_updates)=={'analysis/lll/timing_optimizer_native_report.py',
        'analysis/tests/test_timing_feasible_native_study.py'}


@pytest.mark.parametrize('change',[None,'count','rows','pairs','source','environment','manifest','failed','replays','summary'])
def test_feasible_matrix_requires_all_six_corrected_native_regressions(change):
    from lll.timing_optimizer_native_study import NUMERICAL
    m=policy();sources={k:'a'*64 for k in NUMERICAL};env={'same':True}
    binding=dict(sources=copy.deepcopy(sources),environment=env)
    report=dict(verified=True,native_qualified=True,selected=6,complete=6,failures=[],
        original_binding_replays_exact=True,rows=[dict(passed=True) for _ in range(6)],
        pairs=[dict(passed=True) for _ in range(3)],
        manifest_sha256=m.GATE_MANIFEST,summary_sha256=m.GATE_SUMMARY)
    if change=='count':report['complete']=4
    elif change=='rows':report['rows'].pop()
    elif change=='pairs':report['pairs'].pop()
    elif change=='source':binding['sources'][NUMERICAL[0]]='b'*64
    elif change=='environment':binding['environment']={}
    elif change=='manifest':report['manifest_sha256']='c'*64
    elif change=='summary':report['summary_sha256']='d'*64
    elif change=='failed':report['rows'][0]['passed']=False
    elif change=='replays':report['original_binding_replays_exact']=False
    if change is None:m.verify_gate(report,binding,sources,env)
    else:
        with pytest.raises(ValueError,match='native qualification'):m.verify_gate(report,binding,sources,env)


def test_feasible_matrix_uses_shared_worker_and_six_case_auditor(monkeypatch):
    from lll import timing_optimizer_native_study as shared,timing_optimizer_native_report as auditor
    from lll import timing_feasible_native_study as gate
    m=policy();task={};context=object();seen=[]
    def run(t,c,*,definition):
        assert t is task and c is context;seen.append(definition);return {'delegated':True}
    monkeypatch.setattr(shared,'run_task',run)
    assert m.evaluate(task,context)=={'delegated':True} and seen==[m]
    monkeypatch.setattr(auditor,'inspect',lambda root,path,*,definition:(path,definition))
    assert m.gate_report('.')==(m.GATE,gate)


def test_feasible_matrix_keeps_four_old_references_but_binds_new_native_sources(monkeypatch):
    from lll import timing_optimizer_matrix_study as old
    from lll.studies import closed
    m=policy();points=[{'identity':str(i)} for i in range(4)];sources={'unit':'a'*64};seen=[]
    monkeypatch.setattr(old,'selection',lambda root:(points,{'old':'b'*64}))
    class Saved:
        completion=dict(manifest_sha256=m.GATE_MANIFEST,summary_sha256=m.GATE_SUMMARY)
        manifest=dict(sources=sources)
        def close(self):seen.append('closed')
    monkeypatch.setattr(closed,'ClosedStudy',lambda root,path:Saved())
    assert m.selection('.')==(points,sources) and seen==['closed']
    Saved.completion=dict(Saved.completion,manifest_sha256='0'*64)
    with pytest.raises(ValueError):m.selection('.')
    assert seen==['closed','closed']
