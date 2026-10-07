# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research prediction jointly varying wind, forward direction and specific-force errors.

No production fit, eligibility or decision policy uses this class. Six coherent error
modes have independent unit priors; they are not a complete measurement-error model.
"""
import numpy as np
from scipy.sparse import csr_matrix

import acceleration_motion as motion
from lll import models
from lll.inference import CandidateProblem
from lll.inference_policy import digest

JOINT_POLICY = dict(version='joint-observed-motion-development-1', window_seconds=30.,
    error_modes=['acceleration_n', 'acceleration_e', 'acceleration_down', 'force_x', 'force_y', 'force_z'],
    error_sigma_bound=3., error_prior='Six fully coherent marginal-error patterns with independent unit Gaussian priors',
    gyro_weight_source='Frozen original preliminary weights; no new residual-weight estimate',
    forward_bound_sigmas=3., angular_step_rad=2e-6, wind_step_mps=2e-3, error_step=2e-3,
    support='Fixed observable support including simultaneous three-sigma acceleration-mode norm bound; no state-dependent row selection',
    uncertainty_status='Local joint curvature and six error modes only; unvalidated coverage',
    production_enabled=False, decisions_enabled=False)


def integration_matrix(t, valid, bins):
    """Fixed trapezoidal minute integration; no derivative/filter gap bridging."""
    rows, columns, values = [], [], []
    supported = np.zeros(len(bins['t']), bool)
    for run in motion.regular_runs(t, valid):
        for j, (middle, duration) in enumerate(zip(bins['t'], bins['dt'])):
            left, right = middle-duration/2, middle+duration/2
            if left < t[run[0]] or right > t[run[-1]]: continue
            inner = run[(t[run] > left) & (t[run] < right)]
            grid = np.r_[left, t[inner], right]
            weights = (np.r_[0., np.diff(grid)]+np.r_[np.diff(grid), 0.])/(2*duration)
            for point, weight in zip(grid, weights):
                index = np.searchsorted(t, point)
                if index < len(t) and t[index] == point:
                    rows.append(j); columns.append(index); values.append(weight)
                else:
                    fraction = (point-t[index-1])/(t[index]-t[index-1])
                    rows.extend([j, j]); columns.extend([index-1, index]); values.extend([weight*(1-fraction), weight*fraction])
            supported[j] = True
    return csr_matrix((values, (rows, columns)), shape=(len(bins['t']), len(t))), supported


def subset_bins(bins, keep):
    return {k:(v[keep] if k not in ('mount_matrices','up_reference') and isinstance(v, np.ndarray) and len(v)==len(keep) else v) for k,v in bins.items()}


class MotionContext:
    """Observable-only preparation, independent of gyro outcomes and model anchors."""
    def __init__(self, inputs):
        self.forward, self.sigma = inputs['forward'], inputs['sigma']
        gn, t = inputs['gnss'], inputs['t']
        window = JOINT_POLICY['window_seconds']
        self.prepared = motion.prepare(t, gn['speed_mps'], gn['bearing_deg'], gn['alt_m'],
                                      inputs['force'], inputs['valid'], window)
        self.sigma_a, self.sigma_f = motion.independent_uncertainty(t, gn['speed_mps'], gn['bearing_deg'],
            gn['speed_acc_mps'], gn['bearing_acc_deg'], gn['v_acc_m'], inputs['sem'], inputs['valid'], window)
        velocity, _ = motion.matched_filter(t, np.column_stack([gn['speed_mps']*np.cos(np.radians(gn['bearing_deg'])),
            gn['speed_mps']*np.sin(np.radians(gn['bearing_deg']))]), inputs['valid'], window)
        self.velocity = velocity
        valid = self.prepared['valid'] & np.isfinite(self.sigma_a).all(axis=1) & np.isfinite(self.sigma_f).all(axis=1)
        # This sufficient norm bound covers simultaneous coherent error-mode perturbations.
        maximum = np.linalg.norm(np.nan_to_num(self.prepared['acceleration']), axis=1)+3*np.linalg.norm(np.nan_to_num(self.sigma_a), axis=1)
        valid &= maximum <= motion.MOTION_POLICY['maximum_acceleration_mps2']
        self.prepared['valid'] = valid
        _, rate_support = motion.local_derivative(t, np.zeros((len(t), 3)), valid)
        operator, self.bin_mask = integration_matrix(t, rate_support, inputs['bins'])
        if not self.bin_mask.any(): raise ValueError('no complete fixed motion support')
        self.operator = operator[self.bin_mask]
        self.bins = subset_bins(inputs['bins'], self.bin_mask)
        self.matrices = self.bins['mount_matrices'][self.bins['epoch']]
        self.valid = valid
        self.rate_support = rate_support
        self.t = t
        self.error_sigma_bound = JOINT_POLICY['error_sigma_bound']

    def state(self, heading, forward_angle, errors):
        errors = np.asarray(errors)
        if errors.shape != (6,) or not np.isfinite(errors).all() or np.any(abs(errors)>self.error_sigma_bound+1e-8):
            raise ValueError('coherent error modes outside frozen bounds')
        acceleration = self.prepared['acceleration']+self.sigma_a*errors[:3]
        force = self.prepared['force']+self.sigma_f*errors[3:]
        C = np.full((len(self.t), 3, 3), np.nan)
        for run in motion.regular_runs(self.t, self.valid):
            if len(run)<3: continue
            apparent = motion.unit(force[run]); fwd = np.broadcast_to(motion.unit(self.forward), apparent.shape)
            fwd = fwd*np.cos(forward_angle)+np.cross(apparent, fwd)*np.sin(forward_angle)+apparent*np.sum(apparent*fwd,axis=1)[:,None]*(1-np.cos(forward_angle))
            _, C[run], _ = motion.recover_up(force[run], acceleration[run], fwd, heading[run])
        derivative, support = motion.local_derivative(self.t, C, self.valid)
        if not np.array_equal(support, self.rate_support):
            raise ValueError('trial state changed fixed derivative support')
        W = -derivative@np.swapaxes(C, 1, 2)
        omega = np.column_stack([W[:,2,1]-W[:,1,2], W[:,0,2]-W[:,2,0], W[:,1,0]-W[:,0,1]])/2
        average_C = (self.operator@np.nan_to_num(C.reshape(len(C), 9))).reshape(-1,3,3)
        average_rate = self.operator@np.nan_to_num(omega)
        return np.einsum('nji,njk->nik', self.matrices, average_C), np.einsum('nji,nj->ni', self.matrices, average_rate)


class JointAccelerationProblem(CandidateProblem):
    """Same wind/bias parameterization with motion recomputed at every trial state."""
    def __init__(self, context, bias_fn, prior_sigma, settings):
        if settings['crab_model'] not in ('wind', 'wind_tas') or settings.get('mount_yaw_model', 'none') != 'none':
            raise ValueError('joint prototype supports the two wind candidates without mount-yaw fitting')
        if not settings.get('forward_uncertainty'):
            raise ValueError('joint prototype requires forward uncertainty')
        self.context = context
        bins = context.bins
        tangent0 = np.cross(motion.unit(bins['up_reference']), context.forward)
        tangent = np.einsum('nji,j->ni', context.matrices, tangent0)
        super().__init__(bins, bins['forward'], bias_fn, prior_sigma, settings,
                         forward_sigma_rad=context.sigma, forward_tangent=tangent)
        self.original_npar = self.npar
        self.error_slice = slice(self.npar-1, self.npar+5)
        self.npar += 6  # Forward angle stays last, preserving inherited prior/profile contracts.
        self.y = (bins['gyro']-bias_fn(bins['t'])).ravel()
        self.linear_bias = self.X[:,3:].copy()
        self.terms = np.stack(models.terms(bins['lat'], bins['h'], bins['v_n'], bins['v_e'], bins['lon_rate']), axis=-1)
        self.high_B, _ = interpolate_basis(context.t, self.knots)
        nominal = np.zeros(self.npar)
        _, self.X = self.linear_prediction(nominal)
        self._motion_cache = None

    def expand_saved(self, parameters):
        if len(parameters) != self.original_npar: raise ValueError('saved parameter layout differs')
        return np.r_[parameters[:-1], np.zeros(6), parameters[-1]]

    def high_heading(self, z):
        q = z[self.p:self.p+self.nc]
        psi = self.context.prepared['heading']
        if self.wind_tas is not None:
            wind = self.high_B@q.reshape(-1,3)[:,:2]
            air = self.context.velocity-wind
            return np.arctan2(air[:,1],air[:,0])
        coefficients = q.reshape(-1,2)
        angles = (self.high_B@coefficients[:,0])*np.sin(psi)+(self.high_B@coefficients[:,1])*np.cos(psi)
        return psi+angles

    def linear_prediction(self, z):
        C, rate = self.context.state(self.high_heading(z), z[-1], z[self.error_slice])
        science = np.einsum('nij,njk->nik', C, self.terms).reshape(-1,3)
        X = np.column_stack([science, self.linear_bias])
        return rate.ravel(), X

    def prediction(self, z, jac=False):
        z = np.asarray(z)
        nuisance = z[self.p:]
        cached = getattr(self, '_motion_cache', None)
        if cached is not None and np.array_equal(nuisance, cached[0]):
            rate, X = cached[1:]
        else:
            rate, X = self.linear_prediction(z)
            self._motion_cache = (nuisance.copy(), rate, X)
        prediction = X@z[:self.p]+rate
        if not jac: return prediction
        J = np.zeros((len(self.y),self.npar)); J[:,:self.p] = X
        lo, hi = self.bounds()
        for column in range(self.p,self.npar):
            if self.wind_tas is not None and column < self.p+self.nc and (column-self.p)%3 == 2:
                continue  # TAS affects the auxiliary speed observation, not body heading.
            step = JOINT_POLICY['wind_step_mps'] if self.wind_tas is not None and column < self.p+self.nc else JOINT_POLICY['error_step'] if column in range(self.error_slice.start,self.error_slice.stop) else JOINT_POLICY['angular_step_rad']
            plus, minus = z.copy(), z.copy()
            plus[column] = min(z[column]+step,hi[column]); minus[column] = max(z[column]-step,lo[column])
            J[:,column] = (self.prediction(plus)-self.prediction(minus))/(plus[column]-minus[column])
        return prediction, J

    def penalty(self, **kwargs):
        base = super().penalty(**kwargs)
        errors = np.zeros((6,self.npar)); errors[:,self.error_slice] = np.eye(6)
        return np.vstack([base,errors])

    def bounds(self):
        lo, hi = super().bounds()
        lo[self.error_slice], hi[self.error_slice] = -3., 3.
        lo[-1], hi[-1] = -3*self.forward_sigma, 3*self.forward_sigma
        if self.wind_tas is None:
            lo[self.p:self.p+self.nc], hi[self.p:self.p+self.nc] = -np.radians(15), np.radians(15)
        return lo, hi

    def provenance(self):
        return dict(policy=JOINT_POLICY, policy_hash=digest(JOINT_POLICY),
            base_motion_policy_hash=digest(motion.MOTION_POLICY),fixed_bins=len(self.bins['t']),
            original_bins=len(self.context.bin_mask),production_enabled=False,decisions_enabled=False)


def interpolate_basis(times, knots):
    """Reuse the candidate's exact knot locations at high-rate observed timestamps."""
    clipped = np.clip(times,knots[0],knots[-1])
    index = np.clip(np.searchsorted(knots,clipped,side='right')-1,0,len(knots)-2)
    width = knots[index+1]-knots[index]
    fraction = (clipped-knots[index])/width
    B, D = np.zeros((len(times),len(knots))), np.zeros((len(times),len(knots)))
    rows = np.arange(len(times))
    B[rows,index], B[rows,index+1] = 1-fraction, fraction
    interior = (times >= knots[0]) & (times <= knots[-1])
    D[rows[interior],index[interior]], D[rows[interior],index[interior]+1] = -1/width[interior], 1/width[interior]
    return B,D
