# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest
import ilvis0_profile_verification_worker as worker


def fixture():
    tasks=[];results=[]
    for anchor in ('primary','repeat'):
        for start in ('primary','repeat'):
            identity=anchor+'::'+start
            tasks.append(dict(identity=identity,kind='profile',anchor_role=anchor,start_role=start))
            results.append(dict(identity=identity,kind='profile',status='error',
                reason='ValueError: invalid native charge',conditional_stability=dict(passed=True),
                normalized_parameters=[.1,.2],residual_sum_squares=12.))
    return dict(plan=dict(tasks=tasks)),dict(results=results,controls_passed=True)


def test_verification_plan_has_no_fit_or_retry_allowance():
    manifest,summary=fixture();original=copy.deepcopy(summary)
    plan=worker.make_plan(manifest,summary)
    assert plan['maximum_native_evaluations']==12 and plan['maximum_optimizer_starts']==0
    assert len(plan['tasks'])==4 and plan['retries']==0
    assert all(t['identity'].endswith('::verify_saved_endpoint') for t in plan['tasks'])
    assert summary==original


@pytest.mark.parametrize('change',['controls','gate','error','missing'])
def test_verification_rejects_an_unqualified_source(change):
    manifest,summary=fixture()
    if change=='controls':summary['controls_passed']=False
    if change=='gate':summary['results'][0]['conditional_stability']['passed']=False
    if change=='error':summary['results'][0]['reason']='another failure'
    if change=='missing':summary['results'].pop()
    with pytest.raises(ValueError):worker.make_plan(manifest,summary)
