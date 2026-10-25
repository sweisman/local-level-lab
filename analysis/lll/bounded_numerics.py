# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small saved-matrix numerical references; never fit or call native code."""


def dense_geometry(innovation_factor,design,earlier,*,method):
    import numpy as np
    from scipy.linalg import solve_triangular
    l=np.asarray(innovation_factor,float);x=np.asarray(design,float);y=np.asarray(earlier,float)
    if (l.ndim!=2 or l.shape[0]!=l.shape[1] or not 1<len(l)<=128
            or x.ndim!=2 or x.shape[0]!=len(l) or not 1<=x.shape[1]<=27
            or y.ndim!=1 or not 0<len(y)<len(l)
            or any(not np.all(np.isfinite(v)) for v in (l,x,y))
            or np.any(np.triu(l,1)!=0) or np.any(np.diag(l)<=0)
            or method not in ('triangular','covariance','scaled-covariance','generic-LU')):
        raise ValueError('finite small innovation factor, complete design and earlier values only required')
    m=len(y);n=len(l)
    if method=='triangular':
        a=solve_triangular(l[:m,:m],x[:m],lower=True)
        b=solve_triangular(l[:m,:m],y,lower=True)
        shared=l[m:,:m];future=l[m:,m:]
        return dict(whitened_design=a,whitened_values=b,conditional_mean=shared@b,
            contrasts=x[m:]-shared@a,conditional_variance=np.einsum('ij,ij->i',future,future),
            training_response_norm=np.linalg.norm(shared,axis=1))
    covariance=l@l.T
    scale=1/np.sqrt(np.diag(covariance)) if method=='scaled-covariance' else np.ones(n)
    c=covariance*scale[:,None]*scale[None,:]
    lower=np.linalg.cholesky(c[:m,:m]);carry=np.linalg.solve(c[:m,:m],c[:m,m:]).T
    solve=(lambda rhs:np.linalg.solve(lower,rhs)) if method=='generic-LU' else (lambda rhs:solve_triangular(lower,rhs,lower=True))
    a=solve(x[:m]*scale[:m,None]);b=solve(y*scale[:m])
    return dict(whitened_design=a,whitened_values=b,conditional_mean=(carry@(y*scale[:m]))/scale[m:],
        contrasts=x[m:]-(carry@(x[:m]*scale[:m,None]))/scale[m:,None],
        conditional_variance=np.diag(c[m:,m:]-carry@c[:m,m:])/scale[m:]**2,
        training_response_norm=np.linalg.norm(carry@lower,axis=1)/scale[m:])


def envelope_reference(arrays,*,method,rank_tolerance,alpha_training,alpha_prediction):
    import numpy as np
    from .ilvis0_bounded_prediction import Region,predict,known_scale
    l=arrays['innovation_factor'];x=arrays['forecast_jacobian'];y=arrays['earlier_residual']
    g=dense_geometry(l,x,y,method=method);m=len(y)
    scale=known_scale(1.,source_id='declared-linear-control',covariance_id='same-saved-operator')
    region=Region(g['whitened_values'],g['whitened_design'],arrays['region_0_bounds'],scale=scale,
        covariance_id='same-saved-operator',remainder_radius=0.,alpha=alpha_training,
        rank_tolerance=rank_tolerance,design_is_fixed=False)
    result=predict(region,arrays['forecast_coordinates'].ravel()[m:]+g['conditional_mean'],g['contrasts'],
        conditional_variance=g['conditional_variance'],training_response_norm=g['training_response_norm'],
        future_remainder_bounds=np.zeros(len(l)-m),alpha=alpha_prediction,
        prediction_ids=[str(i) for i in range(m,len(l))])
    return result,g,region


def exact_triangular_reference(lower,right):
    """Exact rational forward substitution of small saved binary64 arrays.

    Only the final answer is rounded to binary64. Dimensions, product count and
    integer sizes are bounded; this is a diagnostic, not a production solver.
    """
    import numpy as np
    from fractions import Fraction
    l=np.asarray(lower,float);b=np.asarray(right,float)
    if (l.ndim!=2 or l.shape[0]!=l.shape[1] or not 1<=len(l)<=36
            or b.ndim!=2 or b.shape[0]!=len(l) or not 1<=b.shape[1]<=28
            or not np.all(np.isfinite(l)) or not np.all(np.isfinite(b))
            or np.any(np.triu(l,1)!=0) or np.any(np.diag(l)<=0)):
        raise ValueError('small finite triangular reference and complete right-hand side required')
    a=[[Fraction(float(v)) for v in row] for row in l]
    values=[];bits=0;terms=0
    for i,row in enumerate(b):
        result=[]
        for col,v in enumerate(row):
            products=[a[i][j]*values[j][col] for j in range(i)];terms+=len(products)
            value=(Fraction(float(v))-sum(products,Fraction(0)))/a[i][i]
            size=max(value.numerator.bit_length(),value.denominator.bit_length())
            bits=max(bits,size)
            if bits>200000:raise ValueError('exact-reference integer-size allowance exceeded')
            result.append(value)
        values.append(result)
    rounded=np.array([[float(v) for v in row] for row in values])
    if not np.all(np.isfinite(rounded)):raise ValueError('exact answer cannot be represented in binary64')
    return dict(rounded=rounded,product_terms=terms,maximum_rational_bits=bits,
        exact_binary64_inputs=True,native_calls=0,optimizer_starts=0)


def diagnose_saved_arrays(arrays,*,rank_tolerance,alpha_training,alpha_prediction,comparison_rtol,comparison_atol):
    import numpy as np
    if not all(np.isfinite(v) and v>=0 for v in (comparison_rtol,comparison_atol)):
        raise ValueError('explicit finite comparison tolerances required')
    l=arrays['innovation_factor'];m=len(arrays['earlier_residual']);x=arrays['forecast_jacobian']
    covariance=l@l.T;lower=np.linalg.cholesky(covariance[:m,:m])
    rhs=np.column_stack((x[:m],arrays['earlier_residual']))
    exact=exact_triangular_reference(lower,rhs);reference=exact.pop('rounded')
    from scipy.linalg import solve_triangular
    variants={'general_lu':np.linalg.solve(lower,rhs),'triangular':solve_triangular(lower,rhs,lower=True),
        'structured':np.column_stack((arrays['region_0_design'],arrays['region_0_values']))}
    exact.update({key+'_maximum_error':float(np.max(abs(value-reference))) for key,value in variants.items()})
    methods={}
    for method in ('generic-LU','covariance','scaled-covariance','triangular'):
        result,g,region=envelope_reference(arrays,method=method,rank_tolerance=rank_tolerance,
            alpha_training=alpha_training,alpha_prediction=alpha_prediction)
        if not result['supported']:
            methods[method]=dict(supported=False,reason=result['reason']);continue
        methods[method]=dict(supported=True,maximum_endpoint_difference=max(
            float(np.max(abs(result[k]-arrays['structured_'+k]))) for k in ('lower','upper')),
            original_comparison_passed=all(bool(np.allclose(result[k],arrays['structured_'+k],
                rtol=comparison_rtol,atol=comparison_atol)) for k in ('lower','upper')),
            rank=region.rank,minimum_conditional_variance=float(np.min(g['conditional_variance'])),
            whitened_design_difference=float(np.linalg.norm(g['whitened_design']-arrays['region_0_design'])))
    return dict(methods=methods,exact_whitening=exact,factor_condition=float(np.linalg.cond(l)),
        covariance_condition=float(np.linalg.cond(covariance)),native_calls=0,optimizer_starts=0,
        labels_changed=False,qualification_promoted=False,nonlinear_coverage_established=False)
