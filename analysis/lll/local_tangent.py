# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small reusable diagnostics for saved whitened local training Jacobians."""


def conditional_column_norm(matrix, index, *, rank_rtol=1e-10):
    """Norm of one column after projection off all other nuisance columns.

    Its square is local conditional information in whitened units. The
    calculation does not establish nonlinear identifiability or coverage.
    """
    import numpy as np

    matrix=np.asarray(matrix,dtype=float)
    if (matrix.ndim!=2 or matrix.shape[1]<2 or matrix.shape[0]<matrix.shape[1]
            or not np.all(np.isfinite(matrix)) or type(index) is not int
            or not 0<=index<matrix.shape[1] or not 0<rank_rtol<1):
        raise ValueError('finite rectangular whitened Jacobian and column required')
    target=matrix[:,index]
    others=np.delete(matrix,index,axis=1)
    left,singular,_=np.linalg.svd(others,full_matrices=False)
    rank=int(np.count_nonzero(singular>rank_rtol*singular[0])) if singular[0]>0 else 0
    residual=target-left[:,:rank]@(left[:,:rank].T@target)
    return float(np.linalg.norm(residual))
