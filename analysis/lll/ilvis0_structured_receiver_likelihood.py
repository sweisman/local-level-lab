# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matrix-free innovations for a declared long-recording receiver law.

This computes the same Gaussian likelihood as the small dense reference.
It neither estimates the covariance nor establishes aircraft error coverage.
"""

import numpy as np

from .ilvis0_error_model import Spec
from .state_space_covariance import LinearInnovations

VERSION='ilvis0-structured-receiver-likelihood-v1'


def _loading(covariance):
    """Factor a declared semidefinite latent covariance without adding noise."""
    values,vectors=np.linalg.eigh(covariance)
    retained=values>0
    return vectors[:,retained]*np.sqrt(values[retained])


class StructuredWhitening:
    """Whiten residuals and every Jacobian column with one fixed Kalman filter."""

    def __init__(self,times,spec,*,formal_blocks=None,transforms=None,
                 axes=(0,1,2)):
        t=np.asarray(times,float)
        axes=tuple(axes)
        if (not isinstance(spec,Spec) or t.ndim!=1 or not len(t) or
                not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0) or
                not axes or len(set(axes))!=len(axes) or
                any(type(axis) is not int or axis not in (0,1,2) for axis in axes)):
            raise ValueError('declared receiver law, ordered times and unique axes required')
        n=len(t)
        formal=(np.zeros((n,3,3)) if formal_blocks is None else
                np.asarray(formal_blocks,float))
        if (formal.shape!=(n,3,3) or not np.all(np.isfinite(formal)) or
                not np.allclose(formal,formal.transpose(0,2,1),rtol=1e-12,atol=0.) or
                np.min(np.linalg.eigvalsh(formal))<
                -32*np.finfo(float).eps*max(1.,np.max(abs(formal)))):
            raise ValueError('finite positive semidefinite formal blocks required')
        transform=(np.broadcast_to(np.eye(3),(n,3,3)) if transforms is None else
                   np.asarray(transforms,float))
        if (transform.shape!=(n,3,3) or not np.all(np.isfinite(transform)) or
                np.any(np.linalg.slogdet(transform)[0]==0)):
            raise ValueError('finite invertible per-epoch transform required')
        self.times=t.copy()
        self.spec=spec
        self.formal=formal.copy()
        self.transforms=transform.copy()
        self.axes=axes
        self.size=3*(len(spec.components)+2)
        roots=[_loading(matrix) for _,matrix in spec.components]
        roots.extend((_loading(spec.offset),_loading(spec.drift)))
        initial=np.zeros((self.size,sum(root.shape[1] for root in roots)))
        column=0
        for block,root in enumerate(roots):
            width=root.shape[1]
            initial[3*block:3*block+3,column:column+width]=root
            column+=width
        dimension=len(axes)
        def steps():
            for i,timestamp in enumerate(t):
                transition=np.eye(self.size)
                process=[]
                if i:
                    elapsed=timestamp-t[i-1]
                    for j,(tau,matrix) in enumerate(spec.components):
                        decay=np.exp(-elapsed/tau)
                        transition[3*j:3*j+3,3*j:3*j+3]*=decay
                        process.append((j,np.sqrt(1-decay*decay)*roots[j]))
                loading=np.zeros((self.size,sum(root.shape[1]
                                                for _,root in process)))
                column=0
                for j,root in process:
                    width=root.shape[1]
                    loading[3*j:3*j+3,column:column+width]=root
                    column+=width
                observation=np.zeros((3,self.size))
                for j in range(len(spec.components)):
                    observation[:,3*j:3*j+3]=np.eye(3)
                observation[:,self.size-6:self.size-3]=np.eye(3)
                observation[:,self.size-3:self.size]=(
                    (timestamp-spec.drift_origin_s)/spec.drift_span_s*np.eye(3))
                metric=transform[i][list(axes),:]
                observation=metric@observation
                white=metric@(spec.white+formal[i])@metric.T
                yield dict(transition=transition,process_loading=loading,
                           observation=observation,
                           white_loading=np.linalg.cholesky(white))
        self.operator=LinearInnovations(
            steps(),epoch_count=n,state_dimension=self.size,
            observation_dimension=dimension,initial_loading=initial,
            maximum_bytes=256*1024*1024,design_is_fixed=True,
            error_distribution='gaussian')

    def apply(self,residual,jacobian):
        n=len(self.times)
        residual=np.asarray(residual,float)
        jacobian=np.asarray(jacobian,float)
        if (residual.shape!=(3*n,) or jacobian.ndim!=2 or
                jacobian.shape[0]!=3*n or not np.all(np.isfinite(residual)) or
                not np.all(np.isfinite(jacobian))):
            raise ValueError('finite full receiver residual and Jacobian required')
        values=np.column_stack((residual,jacobian)).reshape(n,3,-1)
        selected=values[:,list(self.axes),:].reshape(n*len(self.axes),-1)
        whitened=self.operator.whiten(selected)
        error=whitened[:,0]
        logdet=self.operator.log_determinant
        return dict(version=VERSION,residual=error,jacobian=whitened[:,1:],
                    quadratic=float(error@error),log_determinant=logdet,
                    negative_log_likelihood=.5*(float(error@error)+logdet+
                        len(error)*np.log(2*np.pi)),
                    receiver_covariance_calibrated=False)


def from_legacy_assumption(times,latitudes,heights,formal_blocks,assumption,
                           *,axes=(0,1,2)):
    """Represent exactly the old dense WGS84 receiver law without a dense matrix.

    A constant positive piece of each formal block becomes the required white
    state-space covariance; the remainder stays in its original epoch block.
    This algebraic split changes no covariance or physical assumption.
    """
    from .ilvis0_gps_sensitivity import Assumption,formal_blocks as checked_blocks
    t=np.asarray(times,float)
    phi=np.asarray(latitudes,float)
    h=np.asarray(heights,float)
    b=checked_blocks(formal_blocks)
    if (not isinstance(assumption,Assumption) or t.ndim!=1 or len(t)<2 or
            phi.shape!=t.shape or h.shape!=t.shape or b.shape!=(len(t),3,3)
            or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0) or
            not np.all(np.isfinite(phi)) or not np.all(np.isfinite(h)) or
            np.any(abs(phi)>=np.pi/2)):
        raise ValueError('complete ordered nonpolar receiver prefix required')
    minimum=float(np.min(np.linalg.eigvalsh(b)))
    split=.5*minimum
    if not np.isfinite(split) or split<=0:
        raise ValueError('positive formal covariance required')
    noise=np.square(assumption.noise_neu_m)
    white=np.eye(3)*split
    components=()
    if assumption.correlation_s:
        components=((assumption.correlation_s,np.diag(noise)),)
    else:
        white+=np.diag(noise)
    spec=Spec(white=white,components=components,
        offset=np.diag(np.square(assumption.offset_neu_m)),
        drift=np.diag(np.square(assumption.drift_neu_m)),
        drift_origin_s=float(t[0]),drift_span_s=float(t[-1]-t[0]))
    a,e2=6378137.,6.6943799901413165e-3
    denominator=1-e2*np.sin(phi)**2
    meridian=a*(1-e2)/denominator**1.5+h
    parallel=(a/np.sqrt(denominator)+h)*np.cos(phi)
    if np.any(meridian<=0) or np.any(parallel<=0):
        raise ValueError('invalid conventional coordinate metric')
    transform=np.zeros((len(t),3,3))
    transform[:,0,0]=1/meridian
    transform[:,1,1]=1/parallel
    transform[:,2,2]=1.
    return StructuredWhitening(t,spec,formal_blocks=b-np.eye(3)*split,
        transforms=transform,axes=axes)
