import numpy as np
import pytest

from lll.ilvis0_physical_score import propose


def search(evaluations):
    return propose(np.eye(2),np.zeros(2),np.array([1.,0.]),[0.],[-1.],[1.],[0.],
        values=lambda x:x*x,derivative=lambda x:np.array([[2*x[0]]]),
        radius=.5,iterations=50,evaluations=evaluations)


def test_linked_constraint_changes_the_attainable_score():
    result = search(50)
    expected = np.sqrt((np.sqrt(2.)-1.)/2.)
    assert result['success']
    assert result['point'][0]==pytest.approx(expected,abs=1e-9)
    assert result['evaluations']<=50


def test_proposal_cannot_exceed_the_map_evaluation_budget():
    result = search(1)
    assert result['status']=='evaluation_limit'
    assert result['evaluations']==1
    assert result['best_approximate'].tolist()==[0.]
