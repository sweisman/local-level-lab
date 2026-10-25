# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.mark.parametrize('method',['triangular','covariance','scaled-covariance','generic-LU'])
def test_dense_innovation_geometry_matches_exact_block_arithmetic(method):
    import numpy as np
    from lll.bounded_numerics import dense_geometry
    factor=np.array([[2.,0.,0.],[1.,3.,0.],[4.,5.,6.]])
    x=np.array([[1.],[2.],[3.]]);y=np.array([2.,4.])
    g=dense_geometry(factor,x,y,method=method)
    np.testing.assert_allclose(g['whitened_values'],[1.,1.])
    np.testing.assert_allclose(g['whitened_design'],[[.5],[.5]])
    np.testing.assert_allclose(g['conditional_mean'],[9.])
    np.testing.assert_allclose(g['contrasts'],[[-1.5]])
    np.testing.assert_allclose(g['conditional_variance'],[36.])
    np.testing.assert_allclose(g['training_response_norm'],[41.**.5])


def test_square_root_geometry_preserves_tiny_conditional_variance_without_subtraction():
    import numpy as np
    from lll.bounded_numerics import dense_geometry
    l=np.array([[1.,0.],[1.,1e-12]]);x=np.array([[1.],[1.]])
    stable=dense_geometry(l,x,np.array([.1]),method='triangular')
    subtracted=dense_geometry(l,x,np.array([.1]),method='covariance')
    assert stable['conditional_variance'][0]==pytest.approx(1e-24)
    assert subtracted['conditional_variance'][0]==0.
    assert subtracted['conditional_variance'][0]!=stable['conditional_variance'][0]


@pytest.mark.parametrize('bad',['shape','upper_triangle','later_values','nonfinite','method'])
def test_dense_geometry_rejects_incomplete_or_noninnovation_inputs(bad):
    import numpy as np
    from lll.bounded_numerics import dense_geometry
    l=np.eye(4);x=np.ones((4,2));y=np.zeros(2);method='triangular'
    if bad=='shape':x=x[:-1]
    elif bad=='upper_triangle':l[0,-1]=1.
    elif bad=='later_values':y=np.zeros(4)
    elif bad=='nonfinite':l[-1,-1]=float('nan')
    else:method='unknown'
    with pytest.raises(ValueError):dense_geometry(l,x,y,method=method)


def test_exact_triangular_reference_matches_closed_form_rationals():
    import numpy as np
    from fractions import Fraction
    from lll.bounded_numerics import exact_triangular_reference
    lower=np.array([[3.,0.],[2.,7.]])
    rhs=np.array([[1.,2.],[4.,5.]])
    result=exact_triangular_reference(lower,rhs)
    expected=np.array([[float(Fraction(1,3)),float(Fraction(2,3))],
        [float(Fraction(10,21)),float(Fraction(11,21))]])
    np.testing.assert_array_equal(result['rounded'],expected)
    assert result['product_terms']==2 and result['maximum_rational_bits']<100


def test_exact_triangular_reference_checks_finite_allowances_before_arithmetic():
    import numpy as np
    from lll.bounded_numerics import exact_triangular_reference
    for a,b in ((np.eye(37),np.ones((37,1))),(np.eye(2),np.ones((2,29))),
            (np.array([[1.,1.],[0.,1.]]),np.ones((2,1)))):
        with pytest.raises(ValueError):exact_triangular_reference(a,b)


def test_saved_matrix_diagnosis_reports_exact_arithmetic_without_promoting_a_gate():
    import numpy as np
    from lll.bounded_numerics import diagnose_saved_arrays,envelope_reference
    arrays=dict(innovation_factor=np.array([[2.,0.,0.],[1.,3.,0.],[4.,5.,6.]]),
        forecast_jacobian=np.array([[1.],[2.],[3.]]),earlier_residual=np.array([2.,4.]),
        forecast_coordinates=np.zeros((3,1)),region_0_bounds=np.array([[-1.,1.]]),
        region_0_design=np.array([[.5],[.5]]),region_0_values=np.array([1.,1.]))
    r,_,_=envelope_reference(arrays,method='triangular',rank_tolerance=1e-10,alpha_training=.01,alpha_prediction=.01)
    arrays.update(structured_lower=r['lower'],structured_upper=r['upper'])
    d=diagnose_saved_arrays(arrays,rank_tolerance=1e-10,alpha_training=.01,alpha_prediction=.01,
        comparison_rtol=1e-8,comparison_atol=1e-8)
    assert d['qualification_promoted'] is False and d['labels_changed'] is False
    assert d['exact_whitening']['product_terms']==2
    assert all(v['original_comparison_passed'] for v in d['methods'].values())
    assert d['native_calls']==0 and d['optimizer_starts']==0
