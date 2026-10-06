# SPDX-License-Identifier: AGPL-3.0-or-later
"""Experimental wind triangle with a smooth latent true-airspeed constraint."""
import numpy as np

WIND_TAS_POLICY = dict(version='wind-tas-1',knot_seconds=900.,wind_sigma_mps=20.,
    wind_rate_sigma_mps_per_h=10.,wind_component_bound_mps=60.,
    tas_reference_mps=250.,tas_log_sigma=.2,tas_log_rate_sigma_per_h=.08,
    tas_min_mps=120.,tas_max_mps=350.,ground_constraint_sigma_mps=2.,
    boundary_fraction=.01,minimum_ground_speed_mps=100.,
    evidence='Conditional GNSS speed constraint with latent smooth TAS; no independent heading or airspeed observation',
    provenance='Provisional development assumptions; independent wind truth, calibration and hardware checks required')


class WindTAS:
    """Knot-major [north wind m/s, east wind m/s, log(TAS/reference)] parameters."""
    def __init__(self,bins,policy):
        from .inference import crab_basis
        self.policy=dict(policy)
        if self.policy!=WIND_TAS_POLICY:
            raise ValueError('unrecognized physical wind/TAS policy')
        self.B,self.D,self.knots=crab_basis(bins,'dynamic',policy['knot_seconds'])
        self.npar=3*len(self.knots)
        self.ground=np.column_stack([bins['v_n'],bins['v_e']])
        self.speed=np.linalg.norm(self.ground,axis=1)
        self.psi=np.arctan2(self.ground[:,1],self.ground[:,0])
        self.psi_dot=np.asarray(bins['psi_dot'],float)
        if len(self.speed)<2 or not np.isfinite(self.ground).all() or not np.isfinite(self.psi_dot).all() or np.min(self.speed)<policy['minimum_ground_speed_mps']:
            raise ValueError('physical wind/TAS requires finite cruise ground vectors')
        speed_rate=np.gradient(self.speed,np.asarray(bins['t'],float))
        unit=self.ground/self.speed[:,None]
        self.ground_dot=speed_rate[:,None]*unit+self.psi_dot[:,None]*self.speed[:,None]*np.column_stack([-unit[:,1],unit[:,0]])

    def state(self,q):
        q=np.asarray(q).reshape(-1,3)
        wind=self.B@q[:,:2]; wind_dot=self.D@q[:,:2]
        air=self.ground-wind; air_dot=self.ground_dot-wind_dot
        norm2=np.sum(air*air,axis=1)
        if np.any(norm2<=1.) or not np.isfinite(norm2).all(): raise ValueError('degenerate physical air velocity')
        tas=self.policy['tas_reference_mps']*np.exp(self.B@q[:,2])
        angle=np.angle(np.exp(1j*(np.arctan2(air[:,1],air[:,0])-self.psi)))
        cross=air[:,0]*air_dot[:,1]-air[:,1]*air_dot[:,0]
        rate=cross/norm2-self.psi_dot
        return dict(wind=wind,air=air,air_dot=air_dot,norm2=norm2,tas=tas,angle=angle,rate=rate,cross=cross)

    def angles(self,q,jac=False):
        s=self.state(q)
        if not jac: return s['angle'],s['rate']
        an,ae=s['air'].T; dn,de=s['air_dot'].T; r=s['norm2'][:,None]; c=s['cross'][:,None]
        angle_j=np.zeros((len(an),len(self.knots),3)); rate_j=np.zeros_like(angle_j)
        angle_j[:,:,0]=ae[:,None]*self.B/r
        angle_j[:,:,1]=-an[:,None]*self.B/r
        rate_j[:,:,0]=(-de[:,None]*self.B+ae[:,None]*self.D)/r+2*c*an[:,None]*self.B/r**2
        rate_j[:,:,1]=(-an[:,None]*self.D+dn[:,None]*self.B)/r+2*c*ae[:,None]*self.B/r**2
        return s['angle'],s['rate'],angle_j.reshape(len(an),-1),rate_j.reshape(len(an),-1)

    def speed_constraint(self,q,jac=False):
        s=self.state(q); norm=np.sqrt(s['norm2']); sigma=self.policy['ground_constraint_sigma_mps']
        residual=(norm-s['tas'])/sigma
        if not jac: return residual
        J=np.empty((len(norm),len(self.knots),3))
        J[:,:,0]=-s['air'][:,0,None]*self.B/(norm[:,None]*sigma)
        J[:,:,1]=-s['air'][:,1,None]*self.B/(norm[:,None]*sigma)
        J[:,:,2]=-s['tas'][:,None]*self.B/sigma
        return residual,J.reshape(len(norm),-1)

    def penalty(self,wind=1.,rate=1.,airspeed=1.,airspeed_rate=1.):
        p=self.policy
        if min(wind,rate,airspeed,airspeed_rate)<=0: raise ValueError('positive physical prior widening required')
        sd=np.tile([p['wind_sigma_mps']*wind]*2+[p['tas_log_sigma']*airspeed],len(self.knots))
        level=np.diag(1/sd)
        differences=np.kron(np.diff(np.eye(len(self.knots)),axis=0),np.eye(3))
        rate_sd=np.tile([p['wind_rate_sigma_mps_per_h']*rate]*2+[p['tas_log_rate_sigma_per_h']*airspeed_rate],len(self.knots)-1)
        rate_sd*=np.repeat(np.diff(self.knots)/3600.,3)
        return np.vstack([level,differences/rate_sd[:,None]])

    def bounds(self):
        p=self.policy
        lo=np.tile([-p['wind_component_bound_mps']]*2+[np.log(p['tas_min_mps']/p['tas_reference_mps'])],len(self.knots))
        hi=np.tile([p['wind_component_bound_mps']]*2+[np.log(p['tas_max_mps']/p['tas_reference_mps'])],len(self.knots))
        return lo,hi

    def boundary(self,q):
        lo,hi=self.bounds(); q=np.asarray(q)
        margin=float(np.min(np.minimum(q-lo,hi-q)/(hi-lo)))
        return dict(relative_margin=margin,near_boundary=margin<=self.policy['boundary_fraction'])

    def report(self,q):
        s=self.state(q)
        return dict(policy=self.policy,knot_times_s=self.knots.tolist(),
            knot_wind_ne_mps=np.asarray(q).reshape(-1,3)[:,:2].tolist(),
            per_bin_wind_ne_mps=s['wind'].tolist(),per_bin_tas_mps=s['tas'].tolist(),
            per_bin_derived_airspeed_mps=np.sqrt(s['norm2']).tolist(),
            speed_constraint_chi2=float(np.sum(self.speed_constraint(q)**2)),
            gnss_conditioning='Ground vectors held fixed during gyro bootstrap; joint replay calibration required',
            **self.boundary(q))
