import numpy as np
import pytest

from lll.esa_linked_physical_replay import score_replay


def test_replay_keeps_the_earlier_part_in_the_conditioned_score():
    class Earlier:
        def whiten(self,x):
            return x

    class Later:
        def whiten(self,x):
            value = x.copy()
            value[3] -= .5*value[0]
            return value

    full = np.array([[.1,0.,0.],[1.,0.,0.]])
    approximation = np.array([[.05,0.,0.],[.9,0.,0.]])
    result = score_replay(full,approximation,np.array([1.,0.,0.]),Earlier(),Later(),
                          np.array([2.,1.,1.]),np.array([1.,0.,0.]),split=1,sign=-1)
    assert result['full_loss_increase']==pytest.approx(.21)
    assert not result['original_loss_passed']
    assert result['earlier_unshared_norm']==pytest.approx(.05)
    assert result['full_score']==pytest.approx(-1.9)
    assert result['linked_score']==pytest.approx(-1.75)
    assert result['later_signed_unshared']==pytest.approx(-.15)
