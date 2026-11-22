# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local information for independent covariance components of a fixed forecast."""


def information(roots, *, relative_cutoff=1e-10):
    """Fisher information for component log variances at the supplied factor scales."""
    import numpy as np
    from scipy.linalg import solve_triangular

    if len(roots)<2 or not 0<relative_cutoff<1:
        raise ValueError('at least two components and a declared rank cutoff required')
    names=list(roots)
    arrays=[np.asarray(roots[name],float) for name in names]
    n=arrays[0].shape[0] if arrays[0].ndim==2 else 0
    if not n or any(a.ndim!=2 or a.shape[0]!=n or not np.isfinite(a).all() for a in arrays):
        raise ValueError('complete aligned finite covariance roots required')
    covariance=sum(a@a.T for a in arrays)
    factors=np.linalg.cholesky(covariance)
    whitened=[solve_triangular(factors,a,lower=True) for a in arrays]
    derivative=np.column_stack([(a@a.T).ravel()/np.sqrt(2.) for a in whitened])
    singular=np.linalg.svd(derivative,compute_uv=False)
    cutoff=relative_cutoff*singular[0]
    profile={}
    for i,name in enumerate(names):
        target=derivative[:,i]
        other=np.delete(derivative,i,axis=1)
        u,s,_=np.linalg.svd(other,full_matrices=False)
        basis=u[:,s>cutoff]
        remaining=target-basis@(basis.T@target)
        magnitude=float(np.linalg.norm(remaining))
        profile[name]=0. if magnitude<=cutoff else magnitude**2
    return dict(components=names,fisher_matrix=(derivative.T@derivative).tolist(),
        rank=int(np.count_nonzero(singular>cutoff)),
        profile_information=profile,singular_values=singular.tolist())
