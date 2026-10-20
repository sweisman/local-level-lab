# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math

import pytest
from scipy.stats import chi2

from lll import ilvis0_exact_scale as exact


def dense_solve(matrix, vector):
    """Independent small rational Gaussian elimination, no state-space code."""
    rows=[list(a)+[b] for a,b in zip(matrix,vector)]
    for j in range(len(rows)):
        pivot=rows[j][j];rows[j]=[v/pivot for v in rows[j]]
        for i in range(len(rows)):
            if i!=j:
                factor=rows[i][j];rows[i]=[a-factor*b for a,b in zip(rows[i],rows[j])]
    return [row[-1] for row in rows]


@pytest.mark.parametrize('rho,offset,drift',[(F(0),F(0),F(0)),(F(3,4),F(2),F(3)),(F(1),F(1,2),F(0))])
def test_innovations_equal_independent_exact_dense_quadratic(rho,offset,drift):
    y=[F(2,3),F(-1),F(7,9),F(3,5),F(-2,7)]
    law=exact.Covariance(rho,F(1,4),F(3,2),offset,drift)
    n=len(y);t=[F(i,n-1) for i in range(n)]
    covariance=[[F(3,2)*rho**abs(i-j)+offset+drift*t[i]*t[j]+(F(1,4) if i==j else 0)
                 for j in range(n)] for i in range(n)]
    expected=sum(a*b for a,b in zip(y,dense_solve(covariance,y)))
    result=exact.residual_quadratic(y,law,budget=exact.Budget())
    assert result==expected and result>=0


@pytest.mark.parametrize('degrees',[3,8,24,100,850])
def test_quantile_floor_has_exact_certificate_and_valid_tail(degrees):
    floor=exact.quantile_floor(degrees,F(1,100))
    assert floor['q']>0 and floor['k']*2<degrees
    product=math.prod(degrees-2*j for j in range(1,floor['k']+1))
    assert floor['q']**floor['k']<=F(1,100)*product
    assert chi2.cdf(float(floor['q']),degrees)<=.01


@pytest.mark.parametrize('value',[F(0),F(2),F(1,2**2200),F(2**2000),F(10**500,3**800)])
def test_square_root_endpoint_is_outward_at_extreme_scales(value):
    upper=exact.sqrt_upper(value)
    assert math.isfinite(upper) and F(upper)**2>=value
    if upper>math.ulp(0.):
        assert F(math.nextafter(upper,0.))**2<value


def test_scale_counts_all_reference_columns_and_bad_mean_only_widens():
    # All four declared columns count even when a reference is rank deficient.
    small=exact.scale_upper(F(3),observations=20,reference_columns=4,alpha=F(1,100))
    large=exact.scale_upper(F(300),observations=20,reference_columns=4,alpha=F(1,100))
    assert small['degrees']==16 and large['upper']>small['upper']
    assert small['observational_coverage_qualified'] is False
    assert small['scientific_decision']=='abstain'
    assert F(small['upper'])**2*small['quantile']['q']>=3


def test_reference_residual_is_exact_on_fixed_time_polynomial():
    values=[F(3),F(2),F(1),F(0),F(-1)]
    assert exact.polynomial_residuals(values,[F(1),F(-2)])==[F(0)]*5
    assert exact.polynomial_residuals(values,[F(0)])==values


def test_cooperative_work_precision_and_deadline_limits():
    law=exact.Covariance(F(3,4),F(1),F(1),F(1),F(1))
    with pytest.raises(exact.Unsupported,match='step'):
        exact.residual_quadratic([F(1)]*5,law,budget=exact.Budget(maximum_steps=2))
    with pytest.raises(exact.Unsupported,match='precision'):
        exact.residual_quadratic([F(1,2**100)]*2,law,budget=exact.Budget(maximum_bits=32))
    with pytest.raises(exact.Unsupported,match='time'):
        exact.residual_quadratic([F(1)]*2,law,budget=exact.Budget(maximum_seconds=0))


def test_invalid_and_unrepresentable_domains_are_explicit():
    with pytest.raises(ValueError):exact.Covariance(F(1,2),F(0),F(1),F(1),F(1))
    with pytest.raises(ValueError):exact.quantile_floor(2,F(1,100))
    with pytest.raises(ValueError):exact.sqrt_upper(F(-1))
    with pytest.raises(exact.Unsupported):exact.sqrt_upper(F(2**2100))
    with pytest.raises(ValueError):exact.residual_quadratic([F(1)],exact.Covariance(F(0),F(1),F(0),F(0),F(0)),budget=exact.Budget())
