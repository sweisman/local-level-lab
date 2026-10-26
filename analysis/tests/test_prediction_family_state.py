# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from types import SimpleNamespace
import pytest


def fixture(tmp_path,role='calibration',seeds=1,models=1):
    from lll.prediction_calibration_study import recipe
    policy=recipe(role);tasks=[]
    for seed in policy['seeds'][:seeds]:
        for model in ('sphere_rotating','sphere_still')[:models]:
            for start in (0,1):
                case=dict(law='increment',model=model,profile=False,start=start)
                tasks.append(dict(identity=f'{seed}-{model}-{start}',payload=dict(draw_seed=seed,role=role,
                    population_sha256='a'*64,case=case)))
    manifest={'tasks':tasks};(tmp_path/'manifest.json').write_text(json.dumps(manifest))
    def context(task):
        directory=tmp_path/'artifacts'/task['identity'];directory.mkdir(parents=True,exist_ok=True)
        def save(name,value):(directory/name).write_text(json.dumps(value))
        return SimpleNamespace(root=tmp_path,manifest=manifest,directory=directory,save=save)
    def outcome(task,converged=True,score=2.):
        from lll.prediction_family_state import record
        c=context(task);c.save('fit.json',dict(residual_sum_squares=1.+task['payload']['case']['start']))
        record(c,task,dict(converged=converged,maximum_standardized_error=score))
        return c
    return policy,tasks,context,outcome


def test_futility_does_not_stop_after_one_failed_start(tmp_path):
    from lll.prediction_family_state import check
    p,t,_,outcome=fixture(tmp_path);c=outcome(t[0],False)
    assert check(c,t[0],policy=p) is None
    assert not (tmp_path/'stop-request.json').exists()


def test_futility_stops_cooperatively_after_both_starts_fail(tmp_path):
    from lll.prediction_family_state import check
    p,t,_,outcome=fixture(tmp_path);outcome(t[0],False);c=outcome(t[1],False)
    proof=check(c,t[1],policy=p)
    request=json.loads((tmp_path/'stop-request.json').read_bytes())
    assert proof['reason']=='unavailable_calibration_family' and proof['seed']==p['seeds'][0]
    assert request['manifest_sha256']==proof['manifest_sha256']


def test_futility_preserves_available_start_despite_other_failure(tmp_path):
    from lll.prediction_family_state import check
    p,t,_,outcome=fixture(tmp_path);outcome(t[0],False);c=outcome(t[1],True,score=100.)
    assert check(c,t[1],policy=p) is None
    assert not (tmp_path/'stop-request.json').exists()


def test_futility_rejects_marker_with_changed_manifest(tmp_path):
    from lll.prediction_family_state import check
    p,t,_,outcome=fixture(tmp_path);c=outcome(t[0],False)
    path=c.directory/'family-outcome.json';m=json.loads(path.read_bytes());m['manifest_sha256']='b'*64
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError):check(c,t[0],policy=p)
    assert not (tmp_path/'stop-request.json').exists()


def test_futility_rejects_marker_from_another_draw_role(tmp_path):
    from lll.prediction_family_state import check
    p,t,_,outcome=fixture(tmp_path);c=outcome(t[0],False)
    path=c.directory/'family-outcome.json';m=json.loads(path.read_bytes());m['role']='validation'
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError):check(c,t[0],policy=p)


def test_validation_futility_stops_at_fifth_distinct_family_not_four(tmp_path):
    from lll.prediction_family_state import check
    p,t,_,outcome=fixture(tmp_path,'validation',seeds=5)
    for i in range(4):
        outcome(t[2*i],score=9.);c=outcome(t[2*i+1],score=1.)
        assert check(c,t[2*i+1],policy=p,threshold=5.) is None
    assert not (tmp_path/'stop-request.json').exists()
    outcome(t[8],score=9.);c=outcome(t[9],score=1.)
    proof=check(c,t[9],policy=p,threshold=5.)
    assert proof['reason']=='validation_failure_budget_exceeded' and proof['failed_families']==5


def test_validation_futility_counts_one_seed_once_across_settings(tmp_path):
    from lll.prediction_family_state import check
    p,t,_,outcome=fixture(tmp_path,'validation',models=2)
    for task in t:c=outcome(task,score=9.)
    assert check(c,t[-1],policy=p,threshold=5.) is None
    failures=list((tmp_path/'family-state').glob('seed-*.json'))
    assert len(failures)==1 and not (tmp_path/'stop-request.json').exists()


def test_validation_futility_rejects_missing_finite_threshold(tmp_path):
    from lll.prediction_family_state import check
    p,t,_,outcome=fixture(tmp_path,'validation');c=outcome(t[0])
    with pytest.raises(ValueError):check(c,t[0],policy=p,threshold=None)
    assert not (tmp_path/'stop-request.json').exists()
