# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicitly assumed geometry for cheap development design search; no IMU fit."""
import numpy as np
from scipy.spatial.transform import Rotation

from . import models
from .inference import CandidateProblem
from .inference_policy import INFERENCE_POLICY
from .calib import RAD2DPH
from .maneuvers import maneuver_mask, turn_motion_check
from .trajectory import TrackReplay


def geometry_kinematics(design):
    sim=design['simulator']
    if sim.get('trajectory_input') is not None:
        replay=TrackReplay(sim['trajectory_input'])
        t=np.arange(0.,replay.duration,1.)
        values=replay.sample(t)
        return dict(t=t,**values,bearing_ok=replay.support(t)),replay.duration
    duration=sum(v[1] for v in sim['legs'])*60.+600.
    t=np.arange(0.,duration,1.); rate=np.zeros(len(t)); start=300.
    for (a,minutes),(b,_) in zip(sim['legs'][:-1],sim['legs'][1:]):
        start+=minutes*60.
        angle=(b-a+180.)%360.-180.; length=abs(angle)/3.
        ramp=np.clip(np.minimum(t-start,start+length+5.-t)/5.,0.,1.)
        rate+=np.sign(angle)*np.radians(3.)*ramp
        start+=length+5.
    psi=np.radians(sim['legs'][0][0])+np.cumsum(rate)
    speed=np.full(len(t),sim['speed']); vn,ve=speed*np.cos(psi),speed*np.sin(psi)
    lat=np.empty(len(t)); lon=np.empty(len(t)); lat[0],lon[0]=np.radians([sim['lat0'],sim['lon0']])
    h=float(sim['h'])
    for i in range(1,len(t)):
        rm,rn=models.radii(lat[i-1]); lat[i]=lat[i-1]+vn[i-1]/(rm+h)
        lon[i]=lon[i-1]+ve[i-1]/((rn+h)*np.cos(lat[i-1]))
    return dict(t=t,lat=lat,lon=lon,h=np.full(len(t),h),psi=psi,psi_dot=rate,
        speed=speed,v_n=vn,v_e=ve,vz=np.zeros(len(t)),bearing_ok=np.ones(len(t),bool)),duration


def geometry_problem(design,schedule,crab_model,*,kin=None):
    kin,duration=geometry_kinematics(design) if kin is None else kin
    if design['simulator'].get('trajectory_input',{}):
        if design['simulator']['trajectory_input']['mode']=='observed_fixes':
            raise ValueError('coarse observations cannot certify high-rate cruise geometry')
    motion=maneuver_mask(kin)
    centers=np.arange(30.,duration,60.)
    safe=np.array([turn_motion_check(motion,t-30.,t+30.)['safe'] for t in centers])
    # Require a ten-minute continuous interval before deliberate IMU turns split it.
    aircraft_ok=np.array([turn_motion_check(motion,t,t)['safe'] for t in kin['t']])
    qualified=np.zeros(len(aircraft_ok),bool)
    edges=np.flatnonzero(np.diff(np.r_[False,aircraft_ok,False]))
    for a,b in zip(edges[::2],edges[1::2]):
        if kin['t'][b-1]-kin['t'][a]>=600.: qualified[a:b]=True
    safe &= np.interp(centers,kin['t'],qualified.astype(float))==1.
    sim=design['simulator']
    for minute in schedule:
        safe &= (centers+30.<minute*60.-1.) | (centers-30.>minute*60.+sim['turn_seconds']+20.)
    t=centers[safe]
    if not len(t): raise ValueError('no qualifying analytic bins')
    def interpolate(key): return np.interp(t,kin['t'],np.unwrap(kin[key]) if key=='psi' else kin[key])
    epoch=np.searchsorted(np.array(schedule)*60.+sim['turn_seconds'],t)
    tray=np.array([[0.,1.,0.],[1.,0.,0.],[0.,0.,-1.]])
    if sim['mount']!='tray': raise ValueError('geometry search supports same-side-up tray turns')
    mount=Rotation.from_euler('ZY',[sim['mount_yaw_deg'],sim['mount_tilt_deg']],degrees=True).as_matrix()@tray
    frames=mount@Rotation.from_euler('Z',(epoch*np.pi)[:,None]).as_matrix()
    up=np.einsum('nji,j->ni',frames,[0.,0.,-1.]); forward=np.einsum('nji,j->ni',frames,[1.,0.,0.])
    lat,h,vn,ve=(interpolate(k) for k in ('lat','h','v_n','v_e'))
    _,rn=models.radii(lat)
    bins=dict(t=t,dt=np.full(len(t),60.),seg=epoch,epoch=epoch,lat=lat,h=h,v_n=vn,v_e=ve,
        psi=interpolate('psi'),psi_dot=np.zeros(len(t)),lon_rate=ve/((rn+h)*np.cos(lat)),
        up=up,dup_dt=np.zeros((len(t),3)),gyro=np.zeros((len(t),3)))
    settings=dict(crab_model=crab_model,crab_knot_seconds=INFERENCE_POLICY['wind_knot_seconds' if crab_model=='wind' else 'crab_knot_seconds'],
        crab_rate_sigma_dph=INFERENCE_POLICY['crab_rate_sigma_dph'],crab_sigma_deg=5.,
        bias_model='dynamic',bias_knot_seconds=INFERENCE_POLICY['bias_knot_seconds'],
        bias_rw_sigma_dph_sqrth=INFERENCE_POLICY['bias_rw_sigma_dph_sqrth'],forward_uncertainty=True,
        design_mode='envelope',max_nfev=200)
    return CandidateProblem(bins,forward,lambda _:0.,np.full(3,2/RAD2DPH),settings,
                            forward_sigma_rad=np.radians(5.))
