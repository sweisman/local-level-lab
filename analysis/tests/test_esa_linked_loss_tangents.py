# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import numpy as np


def test_tangent_multipliers_certify_the_unscaled_known_support():
    from lll.esa_linked_loss_tangents import tangent_proposals
    from lll.ilvis0_coupled_training_score import certify

    class Context:
        charges = []

        def charge(self, **limits):
            self.charges.append(limits)

    context = Context()
    residual = np.array([-1.])
    static, limits = [[1.]], [1.25]
    earlier, score = tangent_proposals(context, np.ones((1, 1)), residual, [0.], [4.],
        static, limits, np.ones(1), [1.], 1.5, seed=[1.])
    assert earlier is None
    assert score['success'] and score['iterations'] <= 16
    direction = F(score['direction'][0])
    bound = certify(residual, score['direction'], [(direction, direction)], [(F(1), F(1))],
        [0.], [4.], static, limits, score['weights'], increase=F(5, 4), unshared=0)
    assert bound == F(5, 4)
    assert context.charges == [dict(bound_calls=1, bound_steps=16)]
