# SPDX-License-Identifier: AGPL-3.0-or-later
"""Archival raw-increment motion factors; conditional physics, no empirical Earth fits.

Preintegration retains within-block finite rotations and rotating specific force.
Group-1 navigation is never an observation here. Factory coning/sculling and processing
remain unknown; the within-packet constant-body-rate/force hypothesis is explicit.
"""
import argparse
from dataclasses import dataclass
import fcntl
import gzip
import json
import math
import os
from pathlib import Path
import platform

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import ilvis0_installation as installation, ilvis0_observation as observation
from . import models

VERSION = 'ilvis0-joint-motion-forward-v1'
POLICY = dict(version=VERSION, maximum_files=6, nominal_period_s=.005,
    within_packet_model='constant body angular rate and specific force; exact interval integrals',
    selection='Previously frozen complete diagnostic seconds; no Earth residual selection',
    original_increments_preserved=True, scientific_eligible=False,
    empirical_earth_fitting_enabled=False, no_fused_navigation_observations=True)


def vector(value):
    a=np.asarray(value,float)
    if a.shape != (3,) or not np.all(np.isfinite(a)):
        raise ValueError('finite three-vector required')
    return a


def rotation(value):
    r=np.asarray(value,float)
    if r.shape != (3,3) or not np.all(np.isfinite(r)) or not np.allclose(r.T@r,np.eye(3),atol=1e-8,rtol=0) or abs(np.linalg.det(r)-1)>1e-8:
        raise ValueError('proper orthonormal rotation required')
    return r


def skew(value):
    x,y,z=vector(value)
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def interval_matrices(theta):
    """Exp(theta), integral Exp(u theta) du, integral (1-u)Exp(u theta) du."""
    theta=vector(theta); q=float(theta@theta); k=skew(theta); kk=k@k
    if q<1e-4:
        a=1-q/6+q*q/120-q**3/5040
        b=.5-q/24+q*q/720-q**3/40320
        c=1/6-q/120+q*q/5040-q**3/362880
        d=1/24-q/720+q*q/40320-q**3/3628800
    else:
        angle=math.sqrt(q)
        a=math.sin(angle)/angle; b=(1-math.cos(angle))/q
        c=(angle-math.sin(angle))/(q*angle)
        d=(q/2+math.cos(angle)-1)/(q*q)
    identity=np.eye(3)
    return identity+a*k+b*kk, identity+b*k+c*kk, .5*identity+c*k+d*kk


def exp(theta):
    return interval_matrices(theta)[0]


def log(r):
    r=rotation(r)
    w=np.array([r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]])/2
    s=float(np.linalg.norm(w)); c=float(np.clip((np.trace(r)-1)/2,-1,1))
    if s<1e-10:
        if c>0:
            return w
        _,basis=np.linalg.eigh((r+r.T)/2)
        axis=basis[:,-1]
        if axis[np.argmax(np.abs(axis))]<0:axis=-axis
        return axis*math.pi
    return w*(math.atan2(s,c)/s)


class Preintegration:
    """Relative inertial-frame factors. No gravity/Earth correction or attitude truth."""
    def __init__(self):
        self.r=np.eye(3); self.v=np.zeros(3)
        self.p={k:np.zeros(3) for k in ('header_elapsed','nominal_200Hz')}
        self.duration={k:0. for k in self.p}
        self.sum_theta=np.zeros(3); self.sum_dv=np.zeros(3); self.samples=0

    def step(self,theta,dv,dt):
        theta,dv=vector(theta),vector(dv)
        if not math.isfinite(dt) or dt<=0:raise ValueError('positive finite interval required')
        e,j,k=interval_matrices(theta)
        position_increment=self.r@(k@dv)
        velocity_increment=self.r@(j@dv)
        for label,period in (('header_elapsed',dt),('nominal_200Hz',POLICY['nominal_period_s'])):
            self.p[label]+=self.v*period+position_increment*period
            self.duration[label]+=period
        self.v+=velocity_increment; self.r=self.r@e
        self.sum_theta+=theta; self.sum_dv+=dv; self.samples+=1

    def result(self):
        return dict(samples=self.samples, delta_rotation=self.r.tolist(),
            rotated_specific_force_integral_mps=self.v.tolist(),
            specific_force_position_integral_m_by_clock={k:v.tolist() for k,v in self.p.items()},
            duration_s_by_clock=self.duration.copy(),
            summed_body_angle_increments_rad=self.sum_theta.tolist(),
            summed_body_velocity_increments_mps=self.sum_dv.tolist(),
            finite_rotation_difference_from_summed_angles_rad=float(np.linalg.norm(log(exp(self.sum_theta).T@self.r))),
            rotated_force_difference_from_unrotated_sum_mps=float(np.linalg.norm(self.v-self.sum_dv)),
            gravity_removed=False, earth_rate_removed=False, independent_attitude=False)


def compose(first,second,clock='header_elapsed'):
    """Compose adjacent factors only; caller must establish time/installation continuity."""
    r1=rotation(first['delta_rotation']); r2=rotation(second['delta_rotation'])
    v1=vector(first['rotated_specific_force_integral_mps']);v2=vector(second['rotated_specific_force_integral_mps'])
    t2=second['duration_s_by_clock'][clock]
    p1=vector(first['specific_force_position_integral_m_by_clock'][clock])
    p2=vector(second['specific_force_position_integral_m_by_clock'][clock])
    return dict(delta_rotation=(r1@r2).tolist(),rotated_specific_force_integral_mps=(v1+r1@v2).tolist(),
        duration_s_by_clock={clock:first['duration_s_by_clock'][clock]+t2},
        specific_force_position_integral_m_by_clock={clock:(p1+v1*t2+r1@p2).tolist()})


def coordinate_kinematics(model,latitude_rad,height_m,coordinate_rate,disc_radius_m=None):
    """Model-specific metric for reported phi/lambda/height, not raw GNSS evidence."""
    dphi,dlam,dh=vector(coordinate_rate); phi=float(latitude_rad); h=float(height_m)
    if model not in models.EXPECTED_K or not math.isfinite(phi+h) or abs(phi)>=math.pi/2-1e-6:
        raise ValueError('unsupported model or polar coordinate domain')
    earth=models.earth_rate_sphere(phi) if model=='sphere_rotating' else np.zeros(3)
    if model=='flat_still':
        if disc_radius_m is None or not math.isfinite(disc_radius_m) or disc_radius_m<=0:
            raise ValueError('disc metric scale must be explicit and positive')
        v=np.array([disc_radius_m*dphi,disc_radius_m*(math.pi/2-phi)*dlam,-dh])
        transport=np.array([0.,0.,-dlam])
    else:
        rm,rn=models.radii(phi)
        if min(rm+h,rn+h)<=0:raise ValueError('invalid globe metric height')
        v=np.array([(rm+h)*dphi,(rn+h)*math.cos(phi)*dlam,-dh])
        transport=np.array([math.cos(phi)*dlam,-dphi,-math.sin(phi)*dlam])
    return dict(velocity_ned_mps=v,earth_rate_ned_rads=earth,transport_rate_ned_rads=transport,
        coordinate_assumption='Conditional metric mapping of receiver coordinates; not independent raw GNSS geometry')


def local_step(c,v,theta,dv,dt,earth,transport,gravity):
    """One strapdown midpoint step; c maps body to local NED. Gravity is explicit."""
    c=rotation(c);v,theta,dv,earth,transport,gravity=map(vector,(v,theta,dv,earth,transport,gravity))
    if not math.isfinite(dt) or dt<=0:raise ValueError('positive finite interval required')
    win=earth+transport
    middle=exp(-win*dt/2)@c@exp(theta/2)
    c_next=exp(-win*dt)@c@exp(theta)
    a=skew(2*earth+transport)*dt/2
    v_next=np.linalg.solve(np.eye(3)+a,(np.eye(3)-a)@v+middle@dv+gravity*dt)
    return c_next,v_next,(v+v_next)*dt/2


def predicted_increments(c0,c1,v0,v1,dt,earth,transport,gravity,*,earth_retention,transport_retention):
    """Conditional joint gyro/acceleration factor with explicit processing hypotheses.

    Returned increments are in body axes before sensor gain/bias/mount effects.
    Neither retention is silently assumed to be established for archival Group4.
    """
    c0,c1=rotation(c0),rotation(c1)
    v0,v1,earth,transport,gravity=map(vector,(v0,v1,earth,transport,gravity))
    if not math.isfinite(dt) or dt<=0:raise ValueError('positive finite interval required')
    if earth_retention is None or transport_retention is None or not all(math.isfinite(r) and 0<=r<=1 for r in (earth_retention,transport_retention)):
        raise ValueError('explicit valid Earth/transport retention hypotheses required')
    win=earth+transport
    theta=log(c0.T@exp(win*dt)@c1)
    middle=exp(-win*dt/2)@c0@exp(theta/2)
    cross=skew(2*earth+transport)*dt/2
    dv=middle.T@((np.eye(3)+cross)@v1-(np.eye(3)-cross)@v0-gravity*dt)
    recorded_theta=theta-middle.T@((1-earth_retention)*earth+(1-transport_retention)*transport)*dt
    return recorded_theta,dv


@dataclass(frozen=True)
class CalibrationBounds:
    """Externally supplied bounds; no default sensor-performance claim."""
    gyro_bias_rads: float
    accel_bias_mps2: float
    gain_fraction: float
    mounting_angle_rad: float

    def validate(self,gyro_bias,accel_bias,gyro_gain,accel_gain,mounting_vector):
        limits=(self.gyro_bias_rads,self.accel_bias_mps2,self.gain_fraction,self.mounting_angle_rad)
        if not all(math.isfinite(x) and x>=0 for x in limits) or self.gain_fraction>=1:
            raise ValueError('finite nonnegative calibration bounds and gain below one required')
        for value,bound in ((gyro_bias,self.gyro_bias_rads),(accel_bias,self.accel_bias_mps2),
                            (gyro_gain,self.gain_fraction),(accel_gain,self.gain_fraction)):
            if np.max(np.abs(vector(value)))>bound:raise ValueError('calibration outside explicit bounds')
        if np.linalg.norm(vector(mounting_vector))>self.mounting_angle_rad:
            raise ValueError('mounting outside explicit angular bound')


def apply_calibration(theta,dv,dt,gyro_bias,accel_bias,gyro_gain,accel_gain,mounting_vector,bounds):
    bounds.validate(gyro_bias,accel_bias,gyro_gain,accel_gain,mounting_vector)
    if not math.isfinite(dt) or dt<=0:raise ValueError('positive finite interval required')
    r=exp(mounting_vector)
    return r@((vector(theta)-vector(gyro_bias)*dt)/(1+vector(gyro_gain))),r@((vector(dv)-vector(accel_bias)*dt)/(1+vector(accel_gain)))


def antenna_offsets(c,relative_body_rate,lever_body):
    """GNSS/IMU lever geometry; rate is body relative to local frame, not raw gyro."""
    c=rotation(c);omega,r=vector(relative_body_rate),vector(lever_body)
    return c@r,c@np.cross(omega,r)


def coordinate_rates(model,latitude_rad,height_m,velocity,disc_radius_m=None):
    """Inverse candidate metric; disc scale and coordinate assumptions stay explicit."""
    v=vector(velocity);phi=float(latitude_rad);h=float(height_m)
    # Reuse all domain/metric validation rather than silently accepting polar singularities.
    coordinate_kinematics(model,phi,h,[0,0,0],disc_radius_m)
    if model=='flat_still':
        return np.array([v[0]/disc_radius_m,v[1]/(disc_radius_m*(math.pi/2-phi)),-v[2]])
    rm,rn=models.radii(phi)
    return np.array([v[0]/(rm+h),v[1]/((rn+h)*math.cos(phi)),-v[2]])


def forward_window(initial,increments,model,gravity,*,processing_hypothesis,disc_radius_m=None):
    """Stream candidate navigation predictions from raw calibrated body increments.

    Initial attitude/velocity/calibration are nuisance inputs, never fused observations.
    This function does not estimate them or provide a calibrated likelihood. GPS epochs
    may later constrain predicted states; no GPS measurement is interpolated here.
    """
    if processing_hypothesis!='unsubtracted_increment_hypothesis':
        raise ValueError('forward mechanization requires an explicit unsubtracted-increment hypothesis')
    c=rotation(initial['attitude_body_to_ned']).copy();v=vector(initial['velocity_ned_mps']).copy()
    coordinates=vector([initial['latitude_rad'],initial['longitude_rad'],initial['height_m']])
    elapsed=0.
    for theta,dv,dt in increments:
        rate=coordinate_rates(model,coordinates[0],coordinates[2],v,disc_radius_m)
        middle=coordinates+rate*dt/2
        context=coordinate_kinematics(model,middle[0],middle[2],rate,disc_radius_m)
        _,estimate,_=local_step(c,v,theta,dv,dt,context['earth_rate_ned_rads'],context['transport_rate_ned_rads'],gravity)
        # A predictor/corrector uses midpoint velocity for transport and coordinate motion.
        rate=coordinate_rates(model,middle[0],middle[2],(v+estimate)/2,disc_radius_m)
        context=coordinate_kinematics(model,middle[0],middle[2],rate,disc_radius_m)
        c,v,_=local_step(c,v,theta,dv,dt,context['earth_rate_ned_rads'],context['transport_rate_ned_rads'],gravity)
        coordinates+=rate*dt;elapsed+=dt
        yield dict(elapsed_s=elapsed,latitude_rad=float(coordinates[0]),longitude_rad=float(coordinates[1]),
            height_m=float(coordinates[2]),velocity_ned_mps=v.copy(),attitude_body_to_ned=c.copy(),
            processing_hypothesis=processing_hypothesis,coordinate_assumptions_conditional=True)


def gps_endpoints(factors,fixes,leap):
    """Associate actual GGA epochs; retain endpoint offsets, never interpolate fixes."""
    _,fixes=follow.mapped_context([],fixes,dict(accepted=True,gps_minus_utc_s=leap))
    t=np.array([f['utc_week_s'] for f in fixes])
    if len(t) and np.any(np.diff(t)<=0):raise ValueError('duplicate/reversed GPS epochs; no repair')
    def nearest(time):
        i=int(np.searchsorted(t,time)); candidates=[j for j in (i-1,i) if 0<=j<len(t)]
        if not candidates:return None
        distances=[abs(t[j]-time) for j in candidates]; best=min(distances)
        chosen=[j for j,d in zip(candidates,distances) if abs(d-best)<1e-9]
        if len(chosen)!=1 or best>.0075:return None
        f=fixes[chosen[0]]
        return dict(f,epoch_minus_factor_endpoint_s=float(t[chosen[0]]-time))
    for factor in factors:
        factor['receiver_start']=nearest(factor['first_interval_start_s'])
        factor['receiver_end']=nearest(factor['last_time_s'])
        factor['receiver_epoch_coincidence_assumed']=False
        factor['gnss_imu_lever_arm_established']=False
    return len(fixes)


def preintegrate_file(path,expected_hash,prior_blocks,leap):
    """Revisit every native packet; select only frozen completeness, not measured signal."""
    expected={b['utc_second']:b for b in prior_blocks if b['complete_diagnostic_block']}
    previous,setting,current=None,None,None
    reports=[]; raw_count=0; fixes=[]; nmea=ap.NMEA()
    def finish():
        if current is None:return
        second,p,raw_sums,first_start,last,signature,first_offset,last_offset=current
        old=expected[second]
        if p.samples!=old['samples'] or raw_sums!=old['raw_increment_sums'] or signature!=old['installation_signature']:
            raise ValueError('frozen packet/block correspondence did not reproduce')
        result=p.result()
        result.update(utc_second=second,first_interval_start_s=first_start,last_time_s=last,
            installation_signature=signature,first_packet_offset=first_offset,last_packet_offset=last_offset,
            raw_increment_sums=raw_sums.copy(),scientific_eligible=False)
        reports.append(result)
    with il.open_source(path) as original:
        stream=follow.HashedReader(original)
        for frame in ap.frames(stream):
            if frame.tag=='$MSG' and frame.group in (1,20):
                setting=dict(installation.installation_message(frame),signature=frame.packet[10:-4].hex())
            elif frame.tag=='$GRP' and frame.group==4:
                row=ap.group4(frame);raw_count+=1;time=follow.utc_tag(row,leap)
                if previous is not None:
                    dt=time-follow.utc_tag(previous,leap)
                    if dt<=0 or previous['time_types']!=row['time_types']:
                        raise ValueError('IMU time reversal or basis change')
                else:dt=None
                if row['imu_type']!=6 or row['rate_code']!=2:
                    raise ValueError('unsupported IMU/rate in frozen six-file forward check')
                second=int(math.floor(time))
                if current is not None and current[0]!=second:
                    finish();current=None
                if second in expected:
                    if dt is None or not .0025<=dt<=.0075 or row['data_status'] or row['imu_status'] or setting is None or not setting['usable']:
                        raise ValueError('previous complete block now has unsupported measurement')
                    if current is None:
                        current=[second,Preintegration(),[0]*6,time-dt,time,setting['signature'],frame.offset,frame.offset]
                    if current[5]!=setting['signature']:
                        raise ValueError('mounting epoch changed inside frozen block')
                    values=[int(row[k]) for k in ap.RAW_FIELDS]
                    mount=np.array(setting['imu_to_aircraft_rotation'])
                    current[1].step(mount@np.array(values[3:])*installation.ANGLE_SCALE,
                                    mount@np.array(values[:3])*installation.VELOCITY_SCALE,dt)
                    current[2]=[a+b for a,b in zip(current[2],values)];current[4]=time;current[7]=frame.offset
                previous=row
            elif frame.tag=='$GRP' and frame.group==10001:
                header=ap.time_header(frame)
                for sentence in nmea.feed(ap.group10001(frame)[1]):
                    if not sentence['valid']:continue
                    f=sentence['fields']
                    if f[0].endswith('GGA') and int(f[6]) in (1,2,4,5):
                        if f[10]!='M' or (f[11] and f[12]!='M'):raise ValueError('unsupported GPS height units')
                        height=float(f[9]) if f[9] else None
                        geoid=float(f[11]) if f[11] else None
                        if any(v is not None and not math.isfinite(v) for v in (height,geoid)):
                            raise ValueError('nonfinite GPS height')
                        fixes.append(dict(header,sod=follow.utc_sod(f[1]),latitude_deg=ap.coordinate(f[2],f[3]),
                            longitude_deg=ap.coordinate(f[4],f[5]),orthometric_height_m=height,
                            geoid_separation_m=geoid,ellipsoid_height_m=height+geoid if height is not None and geoid is not None else None,
                            fix_quality=int(f[6]),nmea_sentence=sentence['sentence'],receiver_stream_offset=sentence['stream_offset']))
            if len(fixes)>20000:raise ValueError('bounded GPS context capacity exceeded')
    finish()
    if stream.digest.hexdigest()!=expected_hash:raise ValueError('original SHA-256 mismatch')
    if {r['utc_second'] for r in reports}!=set(expected):raise ValueError('frozen diagnostic seconds missing')
    fix_count=gps_endpoints(reports,fixes,leap)
    return reports,dict(source_sha256=expected_hash,source_bytes=stream.size,raw_imu_packets=raw_count,
        earth_model_fit_attempts=0,group1_observations_used=False,receiver_positions=fix_count,nmea=nmea.finish(),
        physical_conversion_status='Empirical scale and clock hypotheses; earlier marginal scale failure remains; no decoder promotion')


def summarize_factors(factors):
    runs=[];current=None;last=None
    for f in factors:
        continuous=last is not None and abs(f['first_interval_start_s']-last['last_time_s'])<1e-8 and f['installation_signature']==last['installation_signature']
        if not continuous:
            current=dict(first_utc_second=f['utc_second'],last_utc_second=f['utc_second'],seconds=1,
                header_factor=f,nominal_factor=f);runs.append(current)
        else:
            current['header_factor']=compose(current['header_factor'],f,'header_elapsed')
            current['nominal_factor']=compose(current['nominal_factor'],f,'nominal_200Hz')
            current['seconds']+=1;current['last_utc_second']=f['utc_second']
        last=f
    return dict(complete_diagnostic_seconds=len(factors),runs=runs,
        paired_receiver_endpoints=sum(f['receiver_start'] is not None and f['receiver_end'] is not None for f in factors),
        max_finite_rotation_difference_rad=max((f['finite_rotation_difference_from_summed_angles_rad'] for f in factors),default=0.),
        max_rotating_force_difference_mps=max((f['rotated_force_difference_from_unrotated_sum_mps'] for f in factors),default=0.),
        interpretation='Motion factors include measured inertial rotation and specific force; they are not corrected Earth signals or independent attitude truth.')


def verify_factor_report(report,artifact,task,source_hash):
    if report['task_id']!=task or report['version']!=VERSION or report['scientific_eligible'] or report['earth_model_fit_attempts']:
        raise ValueError('invalid cached forward report')
    if 'error' not in report and (il.sha256(artifact)!=report['factors_sha256'] or report['provenance']['source_sha256']!=source_hash):
        raise ValueError('cached forward artifact/source mismatch')


def run(corpus,prior,output):
    corpus,prior,output=map(Path,(corpus,prior,output))
    old=json.loads((prior/'summary.json').read_text())
    if old['state']!='complete' or old['errors'] or old['files']!=6:raise ValueError('requires completed six-file observation check')
    records={r['task_id']:r for r in map(json.loads,(corpus/'records.jsonl').read_text().splitlines())}
    sources=[Path(m.__file__) for m in (ap,il,follow,installation,observation,models)]+[Path(__file__),Path(__file__).parents[1]/'tests/ilvis0_forward_worker.py']
    inputs=[prior/'manifest.json',prior/'summary.json',corpus/'records.jsonl']+[prior/(r['task_id']+'-blocks.json.gz') for r in old['results']]
    manifest=dict(version=VERSION,policy=POLICY,sources={str(p):il.sha256(p) for p in sources},
        inputs={str(p):il.sha256(p) for p in inputs},tasks=[r['task_id'] for r in old['results']],
        python=platform.python_version(),numpy=np.__version__,
        threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
    if output.exists() and not (output/'manifest.json').exists():raise ValueError('unmarked forward output directory')
    output.mkdir(parents=True,exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'manifest.json').exists():
            if json.loads((output/'manifest.json').read_text())!=manifest:raise ValueError('forward source/input/environment freeze mismatch')
        else:follow.atomic_json(output/'manifest.json',manifest)
        reports=[]
        for row in old['results']:
            for p in sources+inputs:
                if il.sha256(p)!=manifest['sources'].get(str(p),manifest['inputs'].get(str(p))):raise ValueError('frozen forward source/input changed')
            task=row['task_id'];dest=output/(task+'.json');artifact=output/(task+'-factors.json.gz')
            follow.atomic_json(output/'status.json',dict(state='running',pid=os.getpid(),completed=len(reports),total=6,task_id=task))
            if dest.exists():
                report=json.loads(dest.read_text())
                verify_factor_report(report,artifact,task,row['provenance']['source_sha256'])
            else:
                try:
                    old_artifact=prior/(task+'-blocks.json.gz')
                    if il.sha256(old_artifact)!=row['blocks_sha256']:raise ValueError('prior increment artifact hash mismatch')
                    with gzip.open(old_artifact,'rt') as stream:blocks=json.load(stream)['blocks']
                    factors,provenance=preintegrate_file(follow.source_path(corpus,records[task]),row['provenance']['source_sha256'],blocks,row['provenance']['timing']['gps_minus_utc_s'])
                    observation.gzip_json(artifact,dict(version=VERSION,source_sha256=provenance['source_sha256'],factors=factors))
                    report=dict(provenance=provenance,motion=summarize_factors(factors),factors_sha256=il.sha256(artifact),
                        processing_independence_established=False,conditional_equations_available=True)
                except ValueError as error:report=dict(error=str(error))
                report.update(version=VERSION,task_id=task,filename=row['filename'],scientific_eligible=False,earth_model_fit_attempts=0)
                follow.atomic_json(dest,report)
            reports.append(report)
        summary=dict(version=VERSION,state='complete',files=6,errors=sum('error' in r for r in reports),results=reports,
            earth_model_fit_attempts=0,scientific_eligibility_changes=0,originals_deleted=0)
        follow.atomic_json(output/'summary.json',summary)
        compact={k:v for k,v in summary.items() if k!='results'}
        follow.atomic_json(output/'status.json',dict(compact,pid=os.getpid()));print(json.dumps(compact),flush=True)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus',type=Path,default=Path('data/ilvis0-ready'))
    p.add_argument('--prior',type=Path,default=Path('data/ilvis0-observation-20261007'))
    p.add_argument('--output',type=Path,default=Path('data/ilvis0-forward-20261007'))
    a=p.parse_args();run(a.corpus,a.prior,a.output)


if __name__=='__main__':main()
