# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research GLS objective with fixed, full shared-input covariance.

No optimizer, covariance selection, eligibility or production decision is provided.
The supplied matrices remain frozen when science/nuisance coefficients change.
"""
import numpy as np
from scipy.linalg import solve_triangular

POLICY=dict(version='frozen-shared-covariance-objective-1',
    observation_order='Measured-minus-predicted gyro followed by positive physical wind speed constraint',
    covariance='Frozen full covariance in that same residual sign/order; shared cross blocks retained',
    minimum_relative_correlation_eigenvalue=1e-12,
    singular_rule='Explicit failure; no jitter, eigenvalue clipping or discarded observation modes',
    penalty='Existing deterministic parameter penalties appended after joint whitening',
    covariance_updates_during_fit=False,optimizer_calls=0,
    production_enabled=False,decisions_enabled=False)


class FrozenWhitening:
    def __init__(self,covariance):
        covariance=np.asarray(covariance,float)
        if covariance.ndim!=2 or covariance.shape[0]!=covariance.shape[1] or not len(covariance):raise ValueError('nonempty square covariance required')
        if not np.isfinite(covariance).all():raise ValueError('finite covariance required')
        diagonal=np.diag(covariance)
        if np.any(diagonal<=0):raise ValueError('strictly positive covariance diagonal required')
        sigma=np.sqrt(diagonal);correlation=covariance/sigma[:,None]/sigma[None,:]
        if not np.allclose(correlation,correlation.T,atol=1e-12,rtol=1e-10):raise ValueError('symmetric covariance required')
        correlation=(correlation+correlation.T)/2
        eigenvalues=np.linalg.eigvalsh(correlation)
        margin=float(eigenvalues[0]/eigenvalues[-1])
        if margin<=POLICY['minimum_relative_correlation_eigenvalue']:raise ValueError('singular or numerically unstable covariance')
        self.sigma=sigma.copy();self.cholesky=np.linalg.cholesky(correlation)
        self.relative_eigenvalue_margin=margin
        self.logdet=float(2*np.log(sigma).sum()+2*np.log(np.diag(self.cholesky)).sum())

    def apply(self,values):
        values=np.asarray(values,float)
        if values.ndim not in (1,2) or len(values)!=len(self.sigma) or not np.isfinite(values).all():raise ValueError('finite residual/Jacobian with matching rows required')
        scale=self.sigma if values.ndim==1 else self.sigma[:,None]
        return solve_triangular(self.cholesky,values/scale,lower=True,check_finite=False)

    def scores(self,residual,penalty):
        quadratic=float(np.sum(self.apply(residual)**2));prior=float(np.sum(np.asarray(penalty)**2))
        deviance=quadratic+self.logdet
        return dict(data_quadratic=quadratic,penalty_quadratic=prior,penalized_least_squares=quadratic+prior,
            covariance_logdet=self.logdet,gaussian_deviance=deviance,
            gaussian_nll=float(.5*(deviance+len(self.sigma)*np.log(2*np.pi))),
            penalized_gaussian_deviance=deviance+prior)


class FrozenCovarianceObjective:
    def __init__(self,equation,covariance,penalty=None):
        self.equation=equation;self.whitening=FrozenWhitening(covariance)
        self.penalty=equation.problem.penalty().copy() if penalty is None else np.asarray(penalty,float).copy()
        if self.penalty.ndim!=2 or self.penalty.shape[1]!=equation.problem.npar or not np.isfinite(self.penalty).all():raise ValueError('finite matching parameter penalty required')

    def raw_residual(self,z):
        # Covariance was propagated for [+gyro residual,+auxiliary residual].
        # Flipping just one block would change its cross-covariance signs.
        return np.r_[self.equation.residual(z),self.equation.auxiliary(z)]

    def raw_jacobian(self,z):
        J=self.equation.parameter_jacobian(z);_,aux=self.equation.auxiliary(z,jac=True)
        return np.vstack([-J,aux])

    def residual(self,z):
        return np.r_[self.whitening.apply(self.raw_residual(z)),self.penalty@z]

    def jacobian(self,z):
        return np.vstack([self.whitening.apply(self.raw_jacobian(z)),self.penalty])

    def scores(self,z):return self.whitening.scores(self.raw_residual(z),self.penalty@z)


def local_response(raw_jacobian,penalty,whitening):
    """Sampling response of a frozen-covariance linearized estimator, not a refit.

    Prior curvature and sampling covariance are separate: penalties are held fixed.
    """
    whitened=whitening.apply(raw_jacobian);A=np.vstack([whitened,penalty])
    scales=np.maximum(np.linalg.norm(A,axis=0),1e-30)
    inverse=np.linalg.pinv(A/scales,rcond=1e-10)/scales[:,None]
    W=whitening.apply(np.eye(len(raw_jacobian)))
    response=-inverse[:,:len(raw_jacobian)]@W
    covariance_curvature=inverse@inverse.T
    residual_response=np.eye(len(raw_jacobian))+raw_jacobian@response
    return response,residual_response,covariance_curvature
