# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_component_scale_transfer import make_case
from lll.esa_component_scale_feasibility import Quadratic, inspect_box, search


def quadratic(index, error, persistent, maneuver):
    return Quadratic(make_case(index, dict(native=np.eye(len(error)), persistent=np.asarray(persistent),
                                           maneuver=np.asarray(maneuver)), error))


def test_corner_bounds_enclose_an_independent_diagonal_answer():
    curve = quadratic(1, [2., 3., 4.], [[2.], [0.], [0.]], [[0.], [3.], [0.]])
    lower, upper = curve.bounds((.4, 2.))
    exact = 4./(1.+.4*4.) + 9./(1.+2.*9.) + 16.
    assert lower < exact < upper
    assert upper - lower < 1e-8


def test_touching_reference_stays_open():
    interval, _ = inspect_box([(1., 1.), (4., 4.)], [(1., 1.), (4., 4.)],
                              ratio_box=((0., 0.), (0., 0.)),
                              scale_bounds=(.1, 10.), reference=(1., 4.))
    assert interval[0] <= 1. <= interval[1]


def test_full_range_checks_separate_feasible_and_incompatible_cases():
    zero = np.zeros((3, 1))
    high = quadratic(1, [2., 0., 0.], zero, zero)
    low = quadratic(2, [.5, 0., 0.], zero, zero)
    inconsistent = search([high, low], reference=(1., 2.), maximum=8)
    assert inconsistent['status'] == 'incompatible'
    assert len(inconsistent['excluded']) == 1
    assert not inconsistent['open']
    feasible = search([high, high], reference=(1., 2.), maximum=8)
    assert feasible['status'] == 'witness'
    assert 4./feasible['witness']['native'] == pytest.approx(
        1.5, abs=.1)


def test_evaluation_limit_preserves_the_open_cover():
    column = np.array([[1.], [0.], [0.]])
    zero = 0.*column
    high = quadratic(1, [3., 0., 0.], column, zero)
    low = quadratic(2, [1., 0., 0.], zero, zero)
    charges = []
    result = search([high, low], reference=(1., 2.), maximum=1,
                    reserve=lambda: charges.append(1))
    assert result['status'] == 'unresolved'
    assert len(result['open']) == 2
    assert charges == [1]
