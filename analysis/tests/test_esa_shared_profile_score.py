# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

from lll.esa_shared_profile_score import support


def test_shared_score_sums_signed_coefficients_before_taking_magnitudes():
    result = support([1.,-2.],[1.,-1.],[2.,1.],[[1.,-1.],[1.,-2.]])
    assert result['lower']==(Fraction(0),Fraction(0))
    assert result['upper']==(Fraction(1),Fraction(2))
    assert result['linked']==3
    assert result['independent']==10
