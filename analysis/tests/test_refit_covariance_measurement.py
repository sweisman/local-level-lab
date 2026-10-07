# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from types import SimpleNamespace

import numpy as np
import pytest
import covariance_measurement_objective as objective
import refit_covariance_measurement as refits


@pytest.mark.parametrize('kind',['wind','wind_tas'])
def test_fast_columns_match_full_equation_derivative(kind):
    from test_continuous_measurement_motion import equation_fixture
    eq,z,_=equation_fixture(kind);n=len(eq.residual(z))+len(eq.auxiliary(z))
    fast=refits.FastObjective(eq,np.eye(n))
    full=objective.FrozenCovarianceObjective(eq,np.eye(n))
    assert fast.raw_jacobian(z)==pytest.approx(full.raw_jacobian(z),rel=2e-3,abs=1e-8)


def test_correlated_gls_solver_and_fixed_science_match_closed_form():
    A=np.array([[1.,.2,-.3,.8],[.5,1.,.2,-.4],[.1,.3,1.,.2],[1.,1.,1.,-.2],[.3,-.4,.2,1.]])
    y=np.array([1.,-.2,.5,.4,.8]);C=np.eye(5);C[0,-1]=C[-1,0]=.4
    P=np.eye(4)*.3
    eq=SimpleNamespace(problem=SimpleNamespace(npar=4,bounds=lambda:(np.full(4,-10.),np.full(4,10.))),bins={'t':np.array([1.])})
    working=SimpleNamespace(equation=eq,penalty=P,whitening=objective.FrozenWhitening(C))
    working.raw_residual=lambda z:y-A@z
    working.raw_jacobian=lambda z:-A
    working.residual=lambda z:np.r_[working.whitening.apply(y-A@z),P@z]
    working.jacobian=lambda z:np.vstack([working.whitening.apply(-A),P])
    working.scores=lambda z:working.whitening.scores(y-A@z,P@z)
    normal=A.T@np.linalg.solve(C,A)+P.T@P
    arrays,meta=refits.solve(working,np.zeros(4))
    assert meta['success'] and arrays['z']==pytest.approx(np.linalg.solve(normal,A.T@np.linalg.solve(C,y)))
    fixed=np.array([1.,1.,0.]);other,metadata=refits.solve(working,np.zeros(4),fixed)
    expected=(A[:,3]@np.linalg.solve(C,y-A[:,:3]@fixed))/(normal[3,3])
    assert metadata['success'] and other['z']==pytest.approx(np.r_[fixed,expected])
    assert np.all(other['sampling_covariance'][:3]==0)
    assert metadata['scores']['penalized_least_squares']>=meta['scores']['penalized_least_squares']


def test_recovery_preserves_truncated_bytes_and_counts_interrupted_starts(tmp_path):
    path=tmp_path/'attempts.jsonl'
    refits.append(path,dict(event='started',attempt=1))
    with path.open('ab') as out:out.write(b'{"event":')
    events=refits.history(path)
    assert len(events)==1 and events[0]['attempt']==1
    recovery=json.loads((tmp_path/'recovery.jsonl').read_text())
    assert bytes.fromhex(recovery['truncated_hex'])==b'{"event":'
    assert path.read_bytes().endswith(b'\n')


def test_complete_malformed_journal_is_rejected(tmp_path):
    path=tmp_path/'attempts.jsonl';path.write_text('{broken}\n')
    with pytest.raises(json.JSONDecodeError):refits.history(path)
