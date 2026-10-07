# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research diagnostics for still-recording input persistence; no certification."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from lll.format import read_session
from lll.runtime import numerical_environment

POLICY=dict(version='observed-still-input-persistence-1',
    phases=['bench','drift_pre','drift_post'],sampling_seconds=1,
    lags_seconds=[0,1,5,15,60,300],averaging_seconds=[1,15,60,300],
    minimum_imu_coverage_fraction=.8,maximum_imu_sample_gap_periods=3.,
    support='Complete observed seconds and contiguous runs only; no interpolation or gap bridging',
    treatments=['constant_mean_removed','linear_trend_removed'],
    scope='Descriptive input means, cross-channel covariance, lag correlations and block-mean variation; not calibrated error distributions',
    production_enabled=False,decisions_enabled=False)


def second_means(stream,fields,start_ns,end_ns,imu=False):
    """Average observed samples; an absent/incomplete second stays missing."""
    n=(int(end_ns)-int(start_ns))//1_000_000_000
    if n<=0:raise ValueError('at least one complete second required')
    means=np.full((n,len(fields)),np.nan);counts=np.zeros(n,int)
    if stream is None or not len(stream['t_ns']):return means,counts
    times=np.asarray(stream['t_ns'],dtype=np.int64)
    if np.any(np.diff(times)<=0):raise ValueError('strictly increasing stream timestamps required')
    values=np.column_stack([stream[f] for f in fields]);seconds=(times-int(start_ns))//1_000_000_000
    active=(seconds>=0)&(seconds<n);times=times[active];values=values[active];seconds=seconds[active]
    if not len(times):return means,counts
    saturation=np.asarray(stream.get('sat',np.zeros(len(stream['t_ns']),bool)))[active]
    period=float(np.median(np.diff(times)))/1e9 if len(times)>1 else 1.
    if imu and (not np.isfinite(period) or period<=0 or period>1.):raise ValueError('observable IMU sample period required')
    boundaries=np.r_[0,np.flatnonzero(np.diff(seconds))+1,len(seconds)]
    for left,right in zip(boundaries[:-1],boundaries[1:]):
        i=int(seconds[left]);counts[i]=right-left;data=values[left:right]
        if not np.isfinite(data).all() or saturation[left:right].any():continue
        if imu:
            if right-left<max(2,POLICY['minimum_imu_coverage_fraction']/period):continue
            offset=(times[left:right]-(int(start_ns)+i*1_000_000_000))/1e9
            if offset[0]>1.5*period or offset[-1]<1.-1.5*period or np.any(np.diff(offset)>POLICY['maximum_imu_sample_gap_periods']*period):continue
        means[i]=np.mean(data,axis=0)
    return means,counts


def runs(valid):
    indices=np.flatnonzero(valid)
    return [] if not len(indices) else np.split(indices,np.flatnonzero(np.diff(indices)>1)+1)


def detrend(values,valid,treatment):
    x=values.copy();indices=np.flatnonzero(valid);t=indices.astype(float)
    constant=np.ptp(x[valid],axis=0)==0.
    if treatment=='constant_mean_removed':
        x[valid]-=np.mean(x[valid],axis=0);slope=None
    else:
        A=np.column_stack([np.ones(len(t)),t-t.mean()])
        coefficients=np.linalg.lstsq(A,x[valid],rcond=None)[0];x[valid]-=A@coefficients;slope=coefficients[1].tolist()
    # Exact constant inputs have undefined correlation, not floating-point noise.
    x[np.ix_(valid,constant)]=0.
    return x,slope


def describe(values,channels):
    values=np.asarray(values,float)
    if values.ndim!=2 or values.shape[1]!=len(channels):raise ValueError('matching channels required')
    valid=np.isfinite(values).all(axis=1);segments=runs(valid);n=int(valid.sum())
    report=dict(channels=channels,total_seconds=len(valid),observed_complete_seconds=n,
        missing_or_rejected_seconds=int((~valid).sum()),contiguous_run_seconds=[len(s) for s in segments],
        status='insufficient' if n<3 else 'descriptive',treatments={})
    if n<3:return report
    for treatment in POLICY['treatments']:
        x,slope=detrend(values,valid,treatment);cov=x[valid].T@x[valid]/n
        std=np.sqrt(np.maximum(np.diag(cov),0));lags=[]
        for lag in POLICY['lags_seconds']:
            left=np.concatenate([s[:len(s)-lag] for s in segments if len(s)>lag]) if any(len(s)>lag for s in segments) else np.zeros(0,int)
            if len(left):
                cross=x[left].T@x[left+lag]/len(left);den=std[:,None]*std[None,:]
                correlation=np.divide(cross,den,out=np.full_like(cross,np.nan),where=den>0)
                # Undefined zero-variance entries are represented by JSON null.
                normalized=[[float(v) if np.isfinite(v) else None for v in row] for row in correlation]
                diagonal=[normalized[i][i] for i in range(len(channels))]
            else:cross=None;normalized=None;diagonal=None
            lags.append(dict(lag_seconds=lag,within_run_pairs=len(left),cross_covariance=None if cross is None else cross.tolist(),
                cross_correlation=normalized,autocorrelation=diagonal))
        averaging=[]
        for width in POLICY['averaging_seconds']:
            blocks=[]
            for s in segments:
                complete=len(s)//width
                if complete:blocks.extend(x[s[:complete*width]].reshape(complete,width,-1).mean(axis=1))
            block=np.asarray(blocks).reshape(-1,len(channels));count=len(block)
            averaging.append(dict(window_seconds=width,complete_nonoverlapping_blocks=count,
                standard_deviation_of_block_means=np.std(block,axis=0,ddof=1).tolist() if count>=2 else None))
        report['treatments'][treatment]=dict(second_mean_covariance=cov.tolist(),second_mean_standard_deviation=std.tolist(),
            removed_linear_slope_per_second=slope,lags=lags,averaging=averaging)
    return report


def characterize(session):
    phases=[p for p in session.manifest.get('phases',[]) if p['name'] in POLICY['phases']]
    if not phases:raise ValueError('explicit bench/drift still phases required; flight data are not still controls')
    results=[]
    for phase in phases:
        start,end=int(phase['start_ns']),int(phase['end_ns'])
        force,nf=second_means(session.slice('accel',start,end),('x','y','z'),start,end,imu=True)
        gyro,ng=second_means(session.slice(session.gyro_stream(),start,end),('x','y','z'),start,end,imu=True)
        imu_channels=['force_x_mps2','force_y_mps2','force_z_mps2','gyro_x_rad_s','gyro_y_rad_s','gyro_z_rad_s']
        imu=describe(np.column_stack([force,gyro]),imu_channels)
        gnss=session.slice('gnss',start,end);gps=None;accuracy=None;joint=None
        if gnss is not None and len(gnss['t_ns']):
            psi=np.radians(gnss['bearing_deg']);longitude=np.radians(gnss['lon']);finite=np.isfinite(longitude)
            # A still phase has a single local longitude neighborhood. Center the
            # wrap without propagating a missing sample through every later row.
            reference=longitude[finite][0] if finite.any() else 0.
            longitude=np.angle(np.exp(1j*(longitude-reference)))
            stream=dict(t_ns=gnss['t_ns'],v_n=gnss['speed_mps']*np.cos(psi),v_e=gnss['speed_mps']*np.sin(psi),
                height=gnss['alt_m'],latitude=np.radians(gnss['lat']),longitude=longitude)
            means,_=second_means(stream,('v_n','v_e','height','latitude','longitude'),start,end)
            gps_channels=['velocity_n_mps','velocity_e_mps','height_m','latitude_rad','relative_longitude_rad']
            gps=describe(means,gps_channels)
            joint=describe(np.column_stack([means,force,gyro]),gps_channels+imu_channels)
            accuracy={k:dict(finite_samples=int(np.isfinite(gnss[k]).sum()),median=float(np.median(gnss[k][np.isfinite(gnss[k])])) if np.isfinite(gnss[k]).any() else None)
                for k in ('h_acc_m','v_acc_m','speed_acc_mps','bearing_acc_deg')}
        temperature=session.slice('imu_temp',start,end)
        finite_temp=None if temperature is None else temperature['temp_c'][np.isfinite(temperature['temp_c'])]
        results.append(dict(phase=phase['name'],complete_phase_seconds=len(force),imu=imu,gps=gps,gps_imu_joint=joint,gps_accuracy_fields=accuracy,
            temperature_range_celsius=[float(finite_temp.min()),float(finite_temp.max())] if finite_temp is not None and len(finite_temp) else None,
            minimum_received_imu_samples_per_second=dict(force=int(nf.min()),gyro=int(ng.min()))))
    return dict(policy=POLICY,source_sha256=session.sha256,numerical_environment=numerical_environment(),phases=results,
        production_enabled=False,decisions_enabled=False,
        limitations=['Stillness is declared by the phase marker and must be checked experimentally.',
            'Still-run covariance includes unmodeled motion, temperature and drift; it is not purely sensor noise.',
            'Linear detrending may erase genuine slow drift; retain both treatments and the original recording.',
            'Stationary GPS behavior does not characterize airborne receiver errors or public-track interpolation.',
            'Lag estimates reuse samples; block counts do not imply independent observations or validated uncertainty.',
            'Lag moments are normalized by whole-phase variance; finite-sample lag estimates can exceed one and do not define a positive-definite temporal kernel.',
            'No exponential correlation time, covariance domain, gate, threshold or certification is selected.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('session',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=characterize(read_session(args.session))
    report['helper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.output.open('x') as out:out.write(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(phases=len(report['phases']),output=str(args.output),decisions_enabled=False)))
