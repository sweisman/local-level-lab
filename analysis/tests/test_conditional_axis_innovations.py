# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.state_space_covariance import LinearInnovations


def make_operator(count=7):
    def steps():
        for i in range(count):
            yield dict(transition=np.array([[.9, .02*i], [.1, .98]]),
                process_loading=np.array([[.12, -.03], [.05, .1]]),
                observation=np.array([[1., .2], [.2, 1.], [-.3, .7]]),
                white_loading=np.array([[1., 0., 0.], [.2, .8, 0.], [-.4, .9, .2]]))
    return LinearInnovations(steps(), epoch_count=count, state_dimension=2,
        observation_dimension=3, initial_loading=np.eye(2), maximum_bytes=4096,
        design_is_fixed=True, error_distribution='gaussian')


@pytest.mark.parametrize('axes', [(0, 1), (2,), (2, 0, 1)])
def test_marginal_whiten_matches_dense_schur_complement_and_block_replay(axes):
    full = make_operator()
    cut = 3
    marginal = full.conditional_axes(axes, first_epoch=cut, maximum_bytes=4096)
    root = full.unwhiten(np.eye(21))
    sigma = root @ root.T
    indices = [3*i+j for i in range(cut, 7) for j in axes]
    cross = sigma[indices, :3*cut]
    conditioned = sigma[np.ix_(indices, indices)]-cross @ np.linalg.solve(sigma[:3*cut, :3*cut], cross.T)
    errors = np.arange(len(indices)*2, dtype=float).reshape(-1, 2)/3
    expected = np.linalg.solve(np.linalg.cholesky(conditioned), errors)
    np.testing.assert_allclose(marginal.whiten(errors), expected, atol=1e-11)
    size = 2*len(axes)
    head, state = marginal.apply_block(errors[:size], first_epoch=0)
    tail, _ = marginal.apply_block(errors[size:], first_epoch=2, state=state)
    np.testing.assert_array_equal(np.vstack((head, tail)), marginal.whiten(errors))
    assert marginal.storage_bytes == (7-cut)*(2**2+2*2*len(axes)+len(axes)**2)*8


@pytest.mark.parametrize('axes,cut', [((0, 0), 1), ((3,), 1), ((0,), 7), ((), 0)])
def test_rejects_invalid_axis_or_cut(axes, cut):
    with pytest.raises(ValueError, match='axis|axes'):
        make_operator().conditional_axes(axes, first_epoch=cut, maximum_bytes=4096)


def test_storage_limit_is_enforced_before_construction():
    with pytest.raises(ValueError, match='storage'):
        make_operator().conditional_axes((0, 1), first_epoch=3, maximum_bytes=511)
