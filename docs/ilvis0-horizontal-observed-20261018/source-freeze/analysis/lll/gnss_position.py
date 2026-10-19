# SPDX-License-Identifier: AGPL-3.0-or-later
"""GPS-only code positioning under explicit conventional GNSS assumptions.

No IMU/fused navigation inputs, carrier ambiguity fixing, rejection by residual,
calibrated covariance or Earth-model inference. Standard orbit/clock/Klobuchar
equations follow IS-GPS-200; recorded Trimble ionosphere fields remain traceable.
"""
import math
import struct

import numpy as np

from . import trimble_observations as orbit

C = 299792458.
OMEGA = 7.2921151467e-5
GAMMA = (1575.42/1227.60)**2
REFERENCES = {
    'gps': 'https://www.navcen.uscg.gov/sites/default/files/pdf/gps/IS-GPS-200N.pdf',
    'ionosphere_payload': 'https://receiverhelp.trimble.com/oem-gnss/icd-pkt-response55h-utc-ion.html',
    'position_crosscheck': 'https://raw.githubusercontent.com/tomojitakasu/RTKLIB/master/src/pntpos.c',
    'clock_crosscheck': 'https://raw.githubusercontent.com/tomojitakasu/RTKLIB/master/src/ephemeris.c',
    'atmosphere': 'https://www.grc.nasa.gov/www/k-12/airplane/atmosmet.html',
}


def decode_ionosphere(payload):
    if len(payload)!=123 or payload[:1]!=b'\x03':
        raise ValueError('unsupported recorded ionosphere/UTC layout')
    values=struct.unpack('>14d',payload[2:114])
    if not all(math.isfinite(v) for v in values):
        raise ValueError('nonfinite recorded ionosphere/UTC parameters')
    return dict(alpha=list(values[:4]),beta=list(values[4:8]),utc_a0=values[8],utc_a1=values[9],
        utc_reference_s=values[10],leap_seconds=values[11],future_leap_seconds=values[12],
        ion_time_s=values[13],utc_week_mod256=payload[114],future_week_mod256=payload[115],
        day_number=payload[116],reserved_hex=payload[117:].hex(),raw_payload_hex=payload.hex())


def ecef(latitude,longitude,height):
    f=1/298.257223563; e2=f*(2-f)
    n=6378137/math.sqrt(1-e2*math.sin(latitude)**2)
    return np.array([(n+height)*math.cos(latitude)*math.cos(longitude),
        (n+height)*math.cos(latitude)*math.sin(longitude),(n*(1-e2)+height)*math.sin(latitude)])


def geodetic(position):
    x,y,z=map(float,position); horizontal=math.hypot(x,y)
    if not all(math.isfinite(v) for v in (x,y,z)) or np.linalg.norm(position)<6e6:
        raise ValueError('invalid receiver coordinate iterate')
    f=1/298.257223563; e2=f*(2-f)
    latitude=math.atan2(z,horizontal*(1-e2))
    for _ in range(12):
        n=6378137/math.sqrt(1-e2*math.sin(latitude)**2)
        new=math.atan2(z+e2*n*math.sin(latitude),horizontal)
        if abs(new-latitude)<1e-14:
            latitude=new; break
        latitude=new
    n=6378137/math.sqrt(1-e2*math.sin(latitude)**2)
    height=horizontal/math.cos(latitude)-n if abs(math.cos(latitude))>1e-8 else abs(z)-n*(1-e2)
    return latitude,math.atan2(y,x),height


def local_rotation(latitude,longitude):
    s,c=math.sin(latitude),math.cos(latitude); sl,cl=math.sin(longitude),math.cos(longitude)
    return np.array([[-s*cl,-s*sl,c],[-sl,cl,0.],[c*cl,c*sl,s]]) # North, East, Up


def clock(ephemeris,week,seconds,relativity=True):
    delta=(week-ephemeris['gps_week'])*604800+seconds-ephemeris['toc_s']
    value=ephemeris['af0']+delta*(ephemeris['af1']+delta*ephemeris['af2'])
    if relativity:
        dt=(week-ephemeris['gps_week'])*604800+seconds-ephemeris['toe_s']
        mean=ephemeris['m0_rad']+(math.sqrt(3.986005e14/ephemeris['sqrt_a_m']**6)+ephemeris['delta_n_rad_s'])*dt
        eccentric=mean
        for _ in range(20):
            correction=(eccentric-ephemeris['eccentricity']*math.sin(eccentric)-mean)/(1-ephemeris['eccentricity']*math.cos(eccentric))
            eccentric-=correction
            if abs(correction)<1e-13:
                break
        else:
            raise ValueError('clock eccentric anomaly did not converge')
        value-=2*math.sqrt(3.986005e14)*ephemeris['sqrt_a_m']*ephemeris['eccentricity']*math.sin(eccentric)/C**2
    return value


def satellite_state(ephemeris,week,receive_seconds,l1_range):
    """Use the observed L1 code to determine signal time, then broadcast clock."""
    raw_transmit=receive_seconds-l1_range/C
    transmit=raw_transmit
    for _ in range(3):
        transmit=raw_transmit-clock(ephemeris,week,transmit,relativity=False)
    position=orbit.gps_position(ephemeris,week,transmit)
    return position,clock(ephemeris,week,transmit),transmit


def klobuchar(seconds,latitude,longitude,azimuth,elevation,ionosphere):
    if not 0<elevation<=math.pi/2:
        raise ValueError('ionosphere requires a positive elevation')
    if ionosphere is None:
        raise ValueError('recorded ionosphere coefficients required; no default-date substitution')
    psi=.0137/(elevation/math.pi+.11)-.022
    phi=max(-.416,min(.416,latitude/math.pi+psi*math.cos(azimuth)))
    lam=longitude/math.pi+psi*math.sin(azimuth)/math.cos(phi*math.pi)
    geomagnetic=phi+.064*math.cos((lam-1.617)*math.pi)
    time=(43200*lam+seconds)%86400
    alpha,beta=ionosphere['alpha'],ionosphere['beta']
    amplitude=max(0.,sum(a*geomagnetic**i for i,a in enumerate(alpha)))
    period=max(72000.,sum(b*geomagnetic**i for i,b in enumerate(beta)))
    phase=2*math.pi*(time-50400)/period
    delay=5e-9
    if abs(phase)<1.57:
        delay+=amplitude*(1-phase**2/2+phase**4/24)
    return C*(1+16*(.53-elevation/math.pi)**3)*delay


def troposphere(latitude,height,elevation,humidity=.5):
    """Standard-atmosphere sensitivity model, not measured weather.

    Pressure/temperature use NASA's separate troposphere/lower-stratosphere
    formulae; don't silently zero the delay above 10 km. Ellipsoid height is an
    explicit approximation to atmospheric altitude. Mapping is plane-parallel.
    """
    if not -100<=height<=20000 or not 0<elevation<=math.pi/2 or not 0<=humidity<=1:
        raise ValueError('atmosphere outside the declared height/elevation/humidity domain')
    height=max(0.,height)
    if height<11000:
        temperature=15.04-.00649*height+273.1
        pressure=10*101.29*(temperature/288.08)**5.256 # hPa
    else:
        temperature=-56.46+273.1
        pressure=10*22.65*math.exp(1.73-.000157*height)
    vapour=6.108*humidity*math.exp((17.15*temperature-4684)/(temperature-38.45))
    hydro=.0022768*pressure/(1-.00266*math.cos(2*latitude)-.00028*height/1000)
    wet=.002277*(1255/temperature+.05)*vapour
    return (hydro+wet)/math.sin(elevation)


def observations(record,ephemerides,method):
    if method not in ('l1_broadcast','dual_frequency'):
        raise ValueError('unsupported code positioning method')
    selected=[]; omissions=[]; week=record['gps_week']; seconds=record['gps_week_seconds']
    for satellite in record['satellites']:
        prn=satellite['sv_id']
        if satellite['system']!=0 or satellite['antenna']!=0:
            omissions.append(dict(sv_id=prn,system=satellite['system'],reason='GPS-only development scope')); continue
        if satellite.get('unhealthy') or satellite.get('raim_fault') or (len(satellite['flags'])>1 and record['format']=='RT27' and satellite['flags'][1]&2):
            omissions.append(dict(sv_id=prn,reason='recorded satellite unhealthy/RAIM/alert flag')); continue
        def candidates(band,tracks):
            return [s for s in satellite['signals'] if s['band']==band and s['track_type'] in tracks
                and s['range_loaded'] and not s.get('unhealthy') and s.get('pseudorange_m') is not None
                and math.isfinite(s['pseudorange_m']) and 1e6<s['pseudorange_m']<6e7]
        l1=candidates(0,(0,))
        if len(l1)!=1:
            omissions.append(dict(sv_id=prn,reason='unique valid GPS L1 C/A code unavailable')); continue
        l2=candidates(1,(0,1,2,5))
        # Freeze preference for legacy/P-derived code ahead of L2C; no residual selection.
        l2=sorted(l2,key=lambda s:((0,1,2,5).index(s['track_type'])))
        if method=='dual_frequency' and not l2:
            omissions.append(dict(sv_id=prn,reason='valid supported L2 code unavailable')); continue
        ephem=[e for e in ephemerides if e['sv_id']==prn and not e['health'] and e['ura_index']!=15
            and (e['iodc']&255)==e['iode'] and abs((week-e['gps_week'])*604800+seconds-e['toe_s'])<=7200]
        if not ephem:
            omissions.append(dict(sv_id=prn,reason='consistent healthy recent GPS ephemeris unavailable')); continue
        ephem=min(ephem,key=lambda e:(abs((week-e['gps_week'])*604800+seconds-e['toe_s']),e['payload_sha256']))
        try:
            position,bias,transmit=satellite_state(ephem,week,seconds,l1[0]['pseudorange_m'])
        except ValueError as exc:
            omissions.append(dict(sv_id=prn,reason=str(exc))); continue
        raw=l1[0]['pseudorange_m']
        if method=='l1_broadcast':
            value=raw-C*ephem['tgd_s']; code_bias_correction=-C*ephem['tgd_s']
        else:
            value=(GAMMA*raw-l2[0]['pseudorange_m'])/(GAMMA-1); code_bias_correction=0.
        selected.append(dict(sv_id=prn,satellite_ecef_m=position.tolist(),satellite_clock_s=bias,
            transmit_gps_seconds=transmit,observed_corrected_code_m=value,raw_l1_code_m=raw,
            code_bias_correction_m=code_bias_correction,l2_track_type=l2[0]['track_type'] if l2 else None,
            ephemeris_payload_sha256=ephem['payload_sha256'],ura_index=ephem['ura_index']))
    return selected,omissions


def range_system(state,selected,seconds,method,ionosphere,humidity=.5,elevation_mask_deg=5.):
    latitude,longitude,height=geodetic(state[:3])
    rotation=local_rotation(latitude,longitude)
    rows=[]; residuals=[]; used=[]; rejected=[]
    for item in selected:
        satellite=np.array(item['satellite_ecef_m']); delta=satellite-state[:3]
        distance=float(np.linalg.norm(delta)); direction=delta/distance
        north,east,up=rotation@direction
        elevation=math.asin(max(-1.,min(1.,up))); azimuth=math.atan2(east,north)% (2*math.pi)
        if math.degrees(elevation)<elevation_mask_deg:
            rejected.append(dict(sv_id=item['sv_id'],reason='computed elevation below fixed mask')); continue
        sagnac=OMEGA/C*(satellite[0]*state[1]-satellite[1]*state[0])
        ion=klobuchar(seconds,latitude,longitude,azimuth,elevation,ionosphere) if method=='l1_broadcast' else 0.
        trop=troposphere(latitude,height,elevation,humidity)
        predicted=distance+sagnac+state[3]-C*item['satellite_clock_s']+ion+trop
        residuals.append(item['observed_corrected_code_m']-predicted)
        derivative=-direction
        derivative[0]-=OMEGA/C*satellite[1]; derivative[1]+=OMEGA/C*satellite[0]
        rows.append([*derivative,1.])
        used.append(item | dict(elevation_deg=math.degrees(elevation),ionosphere_m=ion,
            troposphere_m=trop,sagnac_m=sagnac,residual_m=residuals[-1]))
    return np.array(rows),np.array(residuals),used,rejected


def solve(record,ephemerides,ionosphere,method,initial,humidity=.5,maximum_iterations=12):
    selected,omissions=observations(record,ephemerides,method)
    state=np.array([*initial,0.],dtype=float)
    converged=False
    for iteration in range(maximum_iterations):
        design,residuals,used,rejected=range_system(state,selected,record['gps_week_seconds'],method,ionosphere,humidity)
        if len(used)<5 or np.linalg.matrix_rank(design)!=4:
            return dict(status='abstain',reason='at least five ranges and full rank required',
                observations=len(used),omissions=omissions+rejected,iterations=iteration+1)
        step=np.linalg.lstsq(design,residuals,rcond=None)[0]
        state+=step
        if np.linalg.norm(step)<1e-4:
            converged=True; break
    if not converged:
        return dict(status='abstain',reason='position solver did not converge',iterations=maximum_iterations,
            observations=len(used),omissions=omissions+rejected)
    design,residuals,used,rejected=range_system(state,selected,record['gps_week_seconds'],method,ionosphere,humidity)
    if len(used)<5 or np.linalg.matrix_rank(design)!=4:
        return dict(status='abstain',reason='final rank/support changed',iterations=iteration+1)
    latitude,longitude,height=geodetic(state[:3]); rotation=local_rotation(latitude,longitude)
    inverse=np.linalg.pinv(design); geometry=inverse@inverse.T
    variance=float(residuals@residuals/(len(residuals)-4))
    local=rotation@geometry[:3,:3]@rotation.T
    return dict(status='converged',ecef_m=state[:3].tolist(),receiver_clock_m=float(state[3]),
        latitude_rad=latitude,longitude_rad=longitude,ellipsoid_height_m=height,
        observations=len(used),iterations=iteration+1,range_rms_m=float(np.sqrt(np.mean(residuals**2))),
        residual_range_variance_m2=variance,
        formal_sigma_neu_m=np.sqrt(np.diag(local)*variance).tolist(),
        formal_covariance_neu_m2=(local*variance).tolist(),
        covariance_calibrated=False,used=used,omissions=omissions+rejected,
        assumptions='GPS broadcast/ECEF; equal independent range weights; no differential code-bias products; no carrier ambiguity fixing')
