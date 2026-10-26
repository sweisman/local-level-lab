# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def report():
    from lll.prediction_calibration_study import recipe
    r=recipe('calibration')
    return dict(verified=True,role='calibration',total=7176,returned_outcomes=7176,
        population_sha256='a'*64,manifest_sha256='b'*64,summary_sha256='c'*64,
        validation_policy=recipe('validation'),draws=[dict(seed=seed,role='calibration',
            population_sha256='a'*64,maximum_score=float(i)) for i,seed in enumerate(r['seeds'])])


def test_calibration_report_requires_closed_evidence_before_numerics(tmp_path):
    import sys
    from lll.prediction_calibration_report import inspect
    before='numpy' in sys.modules
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path,'data/missing')
    from lll.prediction_calibration_report import publish
    with pytest.raises(ValueError):publish(tmp_path,'data/missing',qualification=None)
    assert not (tmp_path/'docs').exists()
    assert ('numpy' in sys.modules)==before


def test_handoff_binds_finite_threshold_and_frozen_validation_policy():
    from lll.prediction_calibration_report import build_handoff,check_handoff
    h=build_handoff(report())
    assert h['calibration']['threshold']==298. and h['calibration']['coverage']==.99
    assert h['validation_policy']['coverage']==.95 and h['validation_policy']['allowed_failures']==4
    assert check_handoff(h,population_sha256='a'*64)==h


def test_handoff_rejects_changed_threshold_population_policy_or_seed():
    from lll.prediction_calibration_report import build_handoff,check_handoff
    original=build_handoff(report())
    for kind in ('threshold','population','policy','seed'):
        h=copy.deepcopy(original)
        if kind=='threshold':h['calibration']['threshold']+=1
        if kind=='population':h['population_sha256']='d'*64
        if kind=='policy':h['validation_policy']['allowed_failures']=5
        if kind=='seed':h['calibration']['records'][0]['seed']=26102610
        with pytest.raises(ValueError):check_handoff(h,population_sha256='a'*64)


def test_handoff_rejects_unexecuted_calibration_draws(tmp_path,monkeypatch):
    from lll.prediction_calibration_study import population,recipe,tasks,REQUIRED_SOURCES,SCOPE
    from lll.prediction_calibration_report import inspect,build_handoff
    from lll import structured_noisy_publication
    from lll.studies import closed
    from lll.studies.artifacts import digest
    raw=b'frozen fixture';sources={n:digest(raw) for n in REQUIRED_SOURCES};env={'fixture':'one-thread'}
    pop=population(sources,env);matrix={t['identity']:t for t in tasks('calibration',pop['sha256'])}
    identity=next(iter(matrix))
    class FakeClosed:
        all_returned=False
        def __init__(self,*a):
            self.manifest=dict(scope=SCOPE,sources=sources);self.tasks=matrix
            self.rows={k:{} for k in matrix} if self.all_returned else {identity:{}}
            self.summary=dict(completed=len(self.rows),elapsed_s=1.,charged={})
            self.completion=dict(manifest_sha256='b'*64,summary_sha256='c'*64)
        def input(self,key):return {'recipe':recipe('calibration'),'population':pop,
            'qualification-environment':env,'validation-policy':recipe('validation')}[key]
        def read(self,*a,**kw):return raw
        def envelope(self,key):return dict(result=dict(passed=False,reason='fixed unavailable outcome',
            error_type='BudgetStopped' if self.all_returned else 'FixtureError'),artifacts={})
        def close(self):pass
    monkeypatch.setattr(closed,'ClosedStudy',FakeClosed)
    from lll import airquantumgrav_inventory
    monkeypatch.setattr(airquantumgrav_inventory,'environment',lambda:env)
    monkeypatch.setattr(structured_noisy_publication,'native_bindings',lambda s:{})
    monkeypatch.setattr(structured_noisy_publication,'inspect_case',lambda *a,**kw:None)
    r=inspect(tmp_path,'data/closed-partial')
    assert r['total']==7176 and r['returned_outcomes']==1 and r['returned_seed_families']==1
    assert len(r['draws'])==299 and r['calibration'] is None
    from lll.prediction_calibration_report import render,result_csv
    assert '1/7176' in render(r) and 'not computed' in render(r).lower()
    assert len(result_csv(r).splitlines())==7177
    with pytest.raises(ValueError):build_handoff(r)
    FakeClosed.all_returned=True
    stopped=inspect(tmp_path,'data/closed-stopped')
    assert stopped['returned_outcomes']==7176 and stopped['calibration'] is None
    with pytest.raises(ValueError):build_handoff(stopped)
