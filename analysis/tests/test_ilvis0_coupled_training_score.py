from fractions import Fraction as F

import numpy as np

from lll.ilvis0_coupled_training_score import certify, direct_proposal, propose, tangent_proposal, translate_rows


def test_loss_constraint_and_static_map_both_restrict_support():
    design = np.array([[1., 1.]])
    residual = np.zeros(1)
    lower, upper = -np.ones(2), np.ones(2)
    static = [[1., -1.], [-1., 1.]]
    limits = [0., 0.]
    objective = np.array([1., 0.])
    proposal = propose(design, residual, lower, upper, objective, static, limits,
                       radius=.5, iterations=4, seed=[1.])
    direction = proposal['direction']
    projected = [(F(direction[0]), F(direction[0]))]*2
    result = certify(residual, direction, projected, [(F(1), F(1)), (F(0), F(0))],
                     lower, upper, static, limits, proposal['weights'], increase=F(1, 4), unshared=0)
    assert result == F(1, 4)


def test_cut_translation_rounds_against_excluding_a_point():
    rows, upper, center = [[.1, -.4]], [.2], [.13, .66]
    value = translate_rows(rows, upper, center)[0]
    original = F(upper[0])-sum(F(a)*F(b) for a,b in zip(rows[0], center, strict=True))
    assert F(value) >= original
    assert float(F(value)-original) < 1e-16


def test_direct_proposal_finds_the_known_relaxed_optimum():
    residual = np.zeros(1)
    design = np.array([[1., 1.]])
    objective = np.array([1., 0.])
    lower, upper = -np.ones(2), np.ones(2)
    static, bounds = [[1., -1.], [-1., 1.]], [0., 0.]
    result = direct_proposal(design, residual, lower, upper, objective, static, bounds,
                             radius=.5, start=np.zeros(2), iterations=20)
    assert np.allclose(result['point'], [.25, .25], rtol=0., atol=1e-10)
    direction = result['direction']
    train = [(F(direction[0]), F(direction[0]))]*2
    bound = certify(residual, direction, train, [(F(1), F(1)), (F(0), F(0))],
                    lower, upper, static, bounds, result['weights'], increase=F(1,4), unshared=0.)
    assert F(1,4) <= bound <= F(.2500000001)


def test_support_handles_subboxes_on_either_side_of_the_fit():
    for lo, hi, low_weight, high_weight, expected in [
        (-2, -1, -3, -2, 6), (1, 2, 2, 3, 6), (1, 2, -3, -2, -2),
    ]:
        assert certify([0], [0], [(F(0), F(0))], [(F(low_weight), F(high_weight))],
                       [lo], [hi], [], [], [], increase=F(1,4), unshared=0.) == expected


def test_scaled_tangent_certifies_the_original_small_coefficient_row():
    design, residual = np.ones((1,1)), np.zeros(1)
    lower, upper = np.array([0.]), np.array([2.])
    objective = np.array([12.])
    rows, b = [[2.**-36]], [2.**-37]
    proposal = tangent_proposal(design,residual,lower,upper,objective,rows,b,
                                radius=1.,point=np.array([.5]),scaled=True)
    coefficient = F(proposal['direction'][0])
    bound = certify(residual,proposal['direction'],[(coefficient,coefficient)],
                    [(F(12),F(12))],lower,upper,rows,b,proposal['weights'],increase=1,unshared=0)
    assert proposal['tangent_proposed'] and bound==6


def test_unsuccessful_tangent_still_supplies_a_zero_weight_certificate(monkeypatch):
    monkeypatch.setattr('lll.ilvis0_coupled_training_score.linear_proposal',lambda *args:None)
    proposal = tangent_proposal(np.ones((1,1)),np.zeros(1),np.array([0.]),np.array([2.]),
                                np.array([1.]),[[1.]], [1.],radius=1.,point=np.array([.5]),scaled=True)
    assert proposal['tangent_proposed'] is False
    assert proposal['direction'].tolist()==[0.]
    assert proposal['weights'].tolist()==[0.]
