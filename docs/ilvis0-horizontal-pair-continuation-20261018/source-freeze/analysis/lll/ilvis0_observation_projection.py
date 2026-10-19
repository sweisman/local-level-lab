# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-coordinate likelihood projections for separate research controls.

These projections retain the IMU inputs and every nuisance column. They change
only which receiver coordinates enter an objective; initialization, trajectory
screening and covariance construction remain separately declared dependencies.
No archival fit, evidence gate or frozen objective is changed by this module.
"""
import numpy as np
from scipy.linalg import solve_triangular

VERSION='ilvis0-receiver-marginal-projection-v1'
AXES=('latitude','longitude','height')


class ReceiverProjection:
    """Marginalize excluded coordinates before whitening the retained ones.

Input residuals and Jacobians use the original full Cholesky whitening. Undo
that whitening, select epoch-major coordinates, and whiten by their marginal
covariance. Dropping already-whitened rows generally gives a different problem.
"""
    def __init__(self,covariance,axes):
        covariance=np.asarray(covariance,float);axes=tuple(axes)
        if (covariance.ndim!=2 or covariance.shape[0]!=covariance.shape[1]
                or not len(covariance) or len(covariance)%3 or not np.all(np.isfinite(covariance))
                or not np.allclose(covariance,covariance.T,rtol=1e-12,atol=0.)
                or not axes or any(not isinstance(a,str) or a not in AXES for a in axes)
                or len(set(axes))!=len(axes)):
            raise ValueError('symmetric finite 3D receiver covariance and unique coordinate axes required')
        self.axes=axes;self.full_size=len(covariance);self.epochs=self.full_size//3
        self.indices=np.array([3*i+AXES.index(a) for i in range(self.epochs) for a in axes],int)
        try:
            full=np.linalg.cholesky(covariance)
            marginal=np.linalg.cholesky(covariance[np.ix_(self.indices,self.indices)])
        except np.linalg.LinAlgError as error:
            raise ValueError('positive definite receiver covariance required') from error
        self.transform=(np.eye(self.full_size) if axes==AXES else
                        solve_triangular(marginal,full[self.indices,:],lower=True))
        self.indices.flags.writeable=False;self.transform.flags.writeable=False

    def apply(self,residual,jacobian):
        residual=np.asarray(residual,float);jacobian=np.asarray(jacobian,float)
        if (residual.shape!=(self.full_size,) or jacobian.ndim!=2 or jacobian.shape[0]!=self.full_size
                or not np.all(np.isfinite(residual)) or not np.all(np.isfinite(jacobian))):
            raise ValueError('finite full residual and every compatible nuisance column required')
        return self.transform@residual,self.transform@jacobian

    def report(self):
        return dict(version=VERSION,retained_coordinates=list(self.axes),epochs=self.epochs,
            full_observations=self.full_size,retained_observations=len(self.indices),
            marginal_covariance=True,gyro_increments_removed=False,
            accelerometer_increments_removed=False,initialization_changed=False,
            selector_changed=False,scientific_eligible=False,scientific_decision='abstain')
