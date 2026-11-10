# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned working receiver weights; no calibration, selection or model fitting.

Reported full NEU covariance remains distinct from assumed temporal correlation
and added uncertainty. Numerical libraries are imported only inside operations.
"""
from dataclasses import dataclass
import math

VERSION='esa-working-receiver-errors-v1'


@dataclass(frozen=True)
class Policy:
    identity:str
    scale:float
    time_constant_s:float
    correlated_share:float=.95
    floor_neu_m:tuple=(.05,.05,.15)

    def describe(self):
        return dict(version=VERSION,policy_id=self.identity,standard_deviation_scale=self.scale,
            correlation_time_s=self.time_constant_s,correlated_variance_share=self.correlated_share,
            added_floor_neu_m=list(self.floor_neu_m),coordinate_chart='receiver WGS84 latitude/longitude/ellipsoidal height',
            receiver_covariance_calibrated=False,uses_fitted_residuals=False,uses_imu=False,
            geometry_candidate_used=False,scientific_decision='abstain')


_POLICIES={p.identity:p for p in (Policy('reported-short-v1',1.,1.),Policy('reported-persistent-v1',3.,60.))}


def policies():
    return {name:p.describe() for name,p in _POLICIES.items()}


def _reported_matrix(diagonal,cross):
    import numpy as np
    from lll.ilvis0_error_model import factor
    diagonal=np.asarray(diagonal,float);cross=np.asarray(cross,float)
    if (diagonal.shape!=(3,) or cross.shape!=(3,)
            or not np.all(np.isfinite(diagonal)) or not np.all(np.isfinite(cross))):
        raise ValueError('complete finite reported covariance required')
    nn,ee,hh=diagonal;en,nh,eh=cross
    result=np.array([[nn,en,nh],[en,ee,eh],[nh,eh,hh]])
    factor(result)
    return result


def reported_covariance(row):
    """Validate one original NEU matrix for quality screening, without a floor."""
    try:return _reported_matrix(row['position_variance_m2'],row['position_cross_covariance_m2'])
    except (KeyError,TypeError) as error:raise ValueError('full reported covariance fields required') from error


@dataclass(frozen=True)
class WorkingError:
    policy:Policy
    times:object
    marginal_neu:object
    transforms:object
    spec:object
    source_sha256:str

    @property
    def descriptor(self):return self.policy.describe()

    @property
    def configuration(self):
        from lll.studies.artifacts import digest,encoded
        return digest(encoded(dict(policy=self.descriptor,source_sha256=self.source_sha256)))

    def operator(self):
        from lll.ilvis0_structured_covariance import Innovations
        return Innovations(self.times,self.spec,transforms=self.transforms)

    def dense(self,*,maximum_epochs):
        if type(maximum_epochs) is not int or not 1<=maximum_epochs<=2048 or len(self.times)>maximum_epochs:
            raise ValueError('explicit sufficient dense epoch cap in [1,2048] required; use the structured operator for longer records')
        from lll.ilvis0_error_model import covariance
        return covariance(self.times,self.spec,transforms=self.transforms)


def build(rows,*,policy_id):
    """Use only supplied receiver rows; all candidates receive identical weights.

    The caller owns source integrity, selection and the training-only boundary.
    Positive-definiteness is checked before adding a working uncertainty floor.
    This factory cannot certify the reported accuracy or underlying error law.
    """
    import numpy as np
    from lll.models import WGS84_A,WGS84_E2
    from lll.ilvis0_error_model import Spec,factor
    from lll.studies.artifacts import digest,encoded
    if not isinstance(policy_id,str) or policy_id not in _POLICIES:raise ValueError('versioned working receiver policy required')
    policy=_POLICIES[policy_id]
    try:
        rows=list(rows);n=len(rows)
        values=np.asarray([[r[k] for k in ('time_s','latitude_deg','longitude_deg','height_m')] for r in rows],float)
        weeks=np.asarray([r['gps_week'] for r in rows],float)
        diagonal=np.asarray([r['position_variance_m2'] for r in rows],float)
        cross=np.asarray([r['position_cross_covariance_m2'] for r in rows],float)
    except (KeyError,TypeError,ValueError) as error:
        raise ValueError('complete numeric receiver coordinates, timing and full covariance required') from error
    if (n<2 or values.shape!=(n,4) or weeks.shape!=(n,) or diagonal.shape!=(n,3) or cross.shape!=(n,3)
            or any(not np.all(np.isfinite(v)) for v in (values,weeks,diagonal,cross))
            or np.any(np.diff(values[:,0])<=0) or np.any((values[:,0]<0)|(values[:,0]>=604800))
            or np.any(weeks<0) or np.any(weeks!=np.floor(weeks)) or np.any(weeks!=weeks[0])
            or np.any(abs(values[:,1])>=90.-math.degrees(1e-6)) or np.any(abs(values[:,2])>180.)):
        raise ValueError('finite ordered single-week nonpolar receiver observations and full covariance required')
    times=values[:,0].copy();marginal=np.empty((n,3,3));transforms=np.empty_like(marginal)
    phi=np.radians(values[:,1]);height=values[:,3];q=1-WGS84_E2*np.sin(phi)**2
    mn=WGS84_A*(1-WGS84_E2)/q**1.5+height;me=(WGS84_A/np.sqrt(q)+height)*np.cos(phi)
    if np.any(mn<=0) or np.any(me<=0):raise ValueError('positive common receiver-coordinate metric required')
    floor=np.diag(np.square(policy.floor_neu_m))
    for i in range(n):
        reported=_reported_matrix(diagonal[i],cross[i])
        marginal[i]=policy.scale**2*(reported+floor)
        transforms[i]=np.diag([1/mn[i],1/me[i],1.])@factor(marginal[i])
    spec=Spec(white=(1-policy.correlated_share)*np.eye(3),
        components=((policy.time_constant_s,policy.correlated_share*np.eye(3)),))
    source=digest(encoded(dict(fields=['time_s','latitude_deg','longitude_deg','height_m'],values=values.tolist(),
        gps_week=int(weeks[0]),reported_diagonal_m2=diagonal.tolist(),reported_cross_neu_m2=cross.tolist())))
    for array in (times,marginal,transforms):array.setflags(write=False)
    return WorkingError(policy,times,marginal,transforms,spec,source)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_error_policy.py',
        'analysis/tests/test_airquantumgrav_error_policy.py','analysis/tests/test_ilvis0_structured_covariance.py',
        'analysis/tests/test_ilvis0_error_model.py','docs/ESA_ERROR_POLICY.md','analysis/lll/studies/qualification.py'])


def required_tests():
    names=['test_outcome_and_gyro_metadata_cannot_change_weights_or_binding',
        'test_reported_covariance_quality_check_preserves_the_original_matrix']
    for name in ('test_policy_preserves_reported_cross_axes_and_upward_height',
                 'test_structured_whitening_matches_dense_for_residuals_and_all_27_columns'):
        names += [f'{name}[{policy}]' for policy in _POLICIES]
    names += ['test_time_correlation_has_the_declared_share_and_actual_elapsed_time[reported-short-v1-1.0-1.0]',
        'test_time_correlation_has_the_declared_share_and_actual_elapsed_time[reported-persistent-v1-60.0-3.0]']
    names += [f'test_unsupported_reported_data_are_rejected_without_repair[{v}]'
        for v in ('negative_covariance','singular_covariance','cross_covariance','time','week','nonfinite','pole','shape','policy')]
    names += [f'test_dense_allocation_requires_a_sufficient_finite_explicit_cap[{v}]' for v in ('None','0','3','2049')]
    return names
