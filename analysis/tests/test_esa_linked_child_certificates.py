# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

import pytest


def test_child_certificate_can_only_tighten_an_existing_bound():
    from lll.esa_linked_child_certificates import certified_disposition

    assert certified_disposition(8., Fraction(1), Fraction(12), []) == (False, 8.)
    assert certified_disposition(8., Fraction(1), Fraction(4), [Fraction(3)]) == (False, 4.)
    assert certified_disposition(8., Fraction(-1), Fraction(4), []) == (True, None)
    with pytest.raises(ValueError, match='saved feasible witness'):
        certified_disposition(8., Fraction(-1), Fraction(4), [Fraction(3)])
    with pytest.raises(ValueError, match='saved feasible witness'):
        certified_disposition(8., Fraction(1), Fraction(2), [Fraction(3)])
