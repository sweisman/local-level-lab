# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit local-polynomial receiver derivatives and conditional covariance.

This linear operator uses actual epochs and a supplied full coordinate
covariance. It does not select windows, interpolate science streams, estimate
sensor calibration or account for polynomial truncation and covariance error.
"""
import math

import numpy as np

VERSION='ilvis0-joint-receiver-derivatives-v1'


class LocalPolynomial:
    def __init__(self,times_s,target_s,coordinate_covariance,*,degree,maximum_gap_s):
        times=np.asarray(times_s,float);covariance=np.asarray(coordinate_covariance,float)
        if (type(degree) is not int or degree not in (2,3,4) or times.ndim!=1
                or len(times)<degree+1 or not np.all(np.isfinite(times))
                or not math.isfinite(target_s) or not math.isfinite(maximum_gap_s)
                or maximum_gap_s<=0. or np.any(np.diff(times)<=0.)
                or np.any(np.diff(times)>maximum_gap_s)
                or not times[0]<=target_s<=times[-1]):
            raise ValueError('finite ordered supported epochs and declared polynomial/gap limits required')
        n=len(times)
        if (covariance.shape!=(3*n,3*n) or not np.all(np.isfinite(covariance))
                or not np.allclose(covariance,covariance.T,rtol=1e-12,atol=0.)):
            raise ValueError('finite symmetric full epoch-major coordinate covariance required')
        try:cholesky=np.linalg.cholesky(covariance)
        except np.linalg.LinAlgError as error:
            raise ValueError('positive definite declared coordinate covariance required') from error
        scale=float(np.max(abs(times-target_s)));x=(times-target_s)/scale
        basis=np.column_stack([x**order/math.factorial(order) for order in range(degree+1)])
        design=np.kron(basis,np.eye(3))
        whitened=np.linalg.solve(cholesky,design)
        norms=np.linalg.norm(whitened,axis=0)
        if not np.all(np.isfinite(norms)) or np.any(norms==0.):
            raise ValueError('unrepresentable polynomial coefficient scales')
        u,singular,vt=np.linalg.svd(whitened/norms,full_matrices=False)
        cutoff=np.finfo(float).eps*max(whitened.shape)*singular[0]
        rank=int(np.sum(singular>cutoff))
        if rank!=design.shape[1]:
            raise ValueError('deficient polynomial rank; no coefficient may be silently dropped')
        # Column scaling changes the solve, not the physical coordinate weights.
        coefficient_operator=((vt.T/singular)@u.T)/norms[:,None]
        coefficient_operator=coefficient_operator@np.linalg.solve(cholesky,np.eye(3*n))
        weights=coefficient_operator[:9]/np.repeat([1.,scale,scale**2],3)[:,None]
        self.weights=weights
        propagated=weights@covariance@weights.T
        # H C H.T is symmetric analytically. Preserve that identity despite
        # roundoff in near-cancelled entries; never modify the supplied C.
        self.covariance=(propagated+propagated.T)/2
        self._prediction=design@coefficient_operator
        self._count=n
        self.policy=dict(version=VERSION,degree=degree,target_s=float(target_s),
            support_start_s=float(times[0]),support_end_s=float(times[-1]),
            maximum_gap_s=float(maximum_gap_s),rank=rank,coefficient_count=design.shape[1],
            covariance_order=['position_x','position_y','position_z','rate_x','rate_y','rate_z',
                              'acceleration_x','acceleration_y','acceleration_z'])
        if not np.all(np.isfinite(self.covariance)) or not np.all(np.isfinite(weights)):
            raise ValueError('unrepresentable derivative operator or covariance')
        self.weights.flags.writeable=False;self.covariance.flags.writeable=False

    def apply(self,coordinates):
        observations=np.asarray(coordinates,float)
        if observations.shape!=(self._count,3) or not np.all(np.isfinite(observations)):
            raise ValueError('finite epoch-major three-coordinate observations required')
        flat=observations.ravel()
        with np.errstate(over='ignore',invalid='ignore'):
            estimate=self.weights@flat
            residual=(flat-self._prediction@flat).reshape(-1,3)
        if not np.all(np.isfinite(estimate)) or not np.all(np.isfinite(residual)):
            raise ValueError('unrepresentable receiver derivatives or polynomial residuals')
        return dict(position=estimate[:3],rate=estimate[3:6],acceleration=estimate[6:9],
            covariance=self.covariance.copy(),coordinate_residuals=residual,
            policy=dict(self.policy),covariance_calibrated=False,truncation_error_included=False,
            scientific_decision='abstain')
