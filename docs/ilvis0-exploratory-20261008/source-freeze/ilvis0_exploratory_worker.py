# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six recorded files, 24 charged starts, 200 evaluations each; no calibrated decision."""
import argparse
import csv
import fcntl
import gzip
import json
import math
import os
from pathlib import Path
import shutil
import time

import numpy as np
from lll import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from lll import ilvis0_installation as installation, ilvis0_forward as forward
from lll import ilvis0_estimator as estimator, ilvis0_exploratory as explore
from lll import ilvis0_gps_sensitivity as sensitivity, ilvis0_observation as observation, runtime


def load(path):
    if str(path).endswith('.gz'):
        with gzip.open(path,'rt') as stream:return json.load(stream)
    return json.loads(Path(path).read_text())


def select(factors):
    """Longest prior complete contiguous run; ties by earliest time, before any fit."""
    runs=[]
    for f in factors:
        if not runs or abs(runs[-1][-1]['last_time_s']-f['first_interval_start_s'])>1e-8 or runs[-1][-1]['installation_signature']!=f['installation_signature']:
            runs.append([])
        runs[-1].append(f)
    return min(runs,key=lambda r:(-len(r),r[0]['first_interval_start_s']))


def prepare(path, source_hash, factors, leap):
    chosen=select(factors); by_second={r['utc_second']:r for r in chosen}
    rows=[]; previous=None; setting=None; sums={s:[0]*6 for s in by_second}; counts=dict.fromkeys(by_second,0)
    with il.open_source(path) as original:
        stream=follow.HashedReader(original)
        for frame in ap.frames(stream):
            if frame.tag=='$MSG' and frame.group in (1,20):
                setting=dict(installation.installation_message(frame),signature=frame.packet[10:-4].hex())
            if frame.tag!='$GRP' or frame.group!=4:continue
            row=ap.group4(frame); t=follow.utc_tag(row,leap); second=int(math.floor(t))
            dt=None if previous is None else t-previous
            if second in by_second:
                old=by_second[second]
                if dt is None or not .0025<=dt<=.0075 or row['imu_type']!=6 or row['rate_code']!=2 or row['data_status'] or row['imu_status']:
                    raise ValueError('unsupported selected native packet')
                if not setting or not setting['usable'] or setting['signature']!=old['installation_signature']:
                    raise ValueError('installation mismatch')
                values=np.array([row[k] for k in ap.RAW_FIELDS],dtype=np.int64)
                mount=np.array(setting['imu_to_aircraft_rotation'])
                rows.append((frame.offset,t,dt,*values,*(mount@values[3:]*installation.ANGLE_SCALE),
                             *(mount@values[:3]*installation.VELOCITY_SCALE)))
                sums[second]=[int(a+b) for a,b in zip(sums[second],values)];counts[second]+=1
            previous=t
    if stream.digest.hexdigest()!=source_hash:raise ValueError('original uncompressed hash changed')
    if any(sums[s]!=by_second[s]['raw_increment_sums'] or counts[s]!=by_second[s]['samples'] for s in by_second):
        raise ValueError('native measurements differ from frozen preintegration')
    values=np.array(rows,float)
    if len(values)==0 or np.any(abs(np.diff(values[:,1])-values[1:,2])>1e-8):
        raise ValueError('selected native run has a gap')
    fixes={}
    for f in chosen:
        for key in ('receiver_start','receiver_end'):
            r=f[key]
            if r is None or r['ellipsoid_height_m'] is None:continue
            epoch=r['utc_week_s']; coords=(math.radians(r['latitude_deg']),math.radians(r['longitude_deg']),r['ellipsoid_height_m'])
            if epoch in fixes and fixes[epoch]!=coords:raise ValueError('conflicting receiver epoch')
            fixes[epoch]=coords
    start=values[0,1]-values[0,2]; duration=min(float(np.sum(values[:,2])),len(values)*.005)
    fixes={t:c for t,c in fixes.items() if .2<t-start<duration-.2}
    gps_times=np.array(sorted(fixes))-start;gps=np.array([fixes[t] for t in sorted(fixes)])
    if len(gps)<60 or np.any(np.diff(gps_times)>2):raise ValueError('insufficient contiguous actual receiver epochs')
    return values,gps_times,gps,dict(source_sha256=source_hash,source_bytes=stream.size,
        selection='longest already frozen complete native run, earliest tie; receiver support only',
        first_interval_start_utc_s=start,last_packet_utc_s=values[-1,1],native_packets=len(values),
        receiver_epochs=len(gps),duration_header_s=float(np.sum(values[:,2])),duration_nominal_s=len(values)*.005,
        raw_group4_preserved=True,source_frames_checksums_valid=True,group1_observations_used=False,
        conversion='IMU6 empirical angle pi/(180*9000), velocity 3.38e-5; earlier scale failures remain')


def initial(gps_times,gps,values,model):
    # Seed, not a motion observation: first ten seconds of receiver coordinates.
    mask=gps_times<=gps_times[0]+10
    coefficients=np.array([np.polyfit(gps_times[mask],gps[mask,i],1) for i in range(3)])
    coordinates=coefficients[:,1];rate=coefficients[:,0]
    velocity=forward.coordinate_kinematics(model,coordinates[0],coordinates[2],rate,6371000.)['velocity_ned_mps']
    yaw=math.atan2(velocity[1],velocity[0])
    # Gravity alignment is only an initialization assumption, corrected by the fit.
    force=np.mean(values[:min(2000,len(values)),12:15],axis=0)/.005
    a=force/np.linalg.norm(force); b=np.array([0.,0.,-1.]); cross=np.cross(a,b); dot=float(a@b)
    if dot<=-.99:raise ValueError('initial force orientation unsupported')
    skew=forward.skew(cross);tilt=np.eye(3)+skew+skew@skew/(1+dot)
    rotation=installation.rotation([0.,0.,math.degrees(yaw)])@tilt
    return dict(latitude_rad=coordinates[0],longitude_rad=coordinates[1],height_m=coordinates[2],
                velocity_ned_mps=velocity,attitude_body_to_ned=rotation),float(np.linalg.norm(force))


def run(root,output):
    prior=root/'data/ilvis0-forward-20261007';corpus=root/'data/ilvis0-ready'
    if output.exists() and not (output/'manifest.json').exists():raise ValueError('unmarked output')
    output.mkdir(parents=True,exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'completion.json').exists():raise ValueError('completed exploratory work is frozen')
        old=load(prior/'summary.json'); records={r['task_id']:r for r in map(json.loads,(corpus/'records.jsonl').read_text().splitlines())}
        if old['state']!='complete' or old['errors']:raise ValueError('prior forward work incomplete')
        sources=[Path(m.__file__) for m in (ap,il,follow,installation,forward,estimator,explore,sensitivity,observation,runtime)]
        sources += [Path(explore.__file__).with_name('ilvis0_native.c'),Path(__file__),root/'analysis/tests/test_ilvis0_exploratory.py',root/'analysis/lll/models.py']
        inputs=[prior/'manifest.json',prior/'summary.json',corpus/'records.jsonl']
        for row in old['results']:inputs += [prior/(row['task_id']+'.json'),prior/(row['task_id']+'-factors.json.gz'),
            root/'data/ilvis0-observation-20261007'/(row['task_id']+'.json')]
        kernel,build=explore.load_kernel(output/'kernel')
        manifest=dict(version=explore.VERSION,sources={str(p):il.sha256(p) for p in sources},
            inputs={str(p):il.sha256(p) for p in inputs},environment=runtime.numerical_environment(),build=build,
            tasks=[r['task_id'] for r in old['results']],limits=explore.LIMITS,
            maximum_starts=24,maximum_evaluations_per_start=200,
            fits_per_file=['three models, common Earth-removal fraction profiled in [0,1]',
                          'rotating globe, Earth-removal fraction fixed zero'],
            clock='nominal_200Hz; header-clock fixed-parameter sensitivity, not reprofiled',
            gravity_mps2=9.81,disc_radius_m=6371000.,
            gps_covariance_assumptions=['h1_v3_tau60','h10_v30_tau300'],
            onboard_transport_subtraction='not modeled in this finite first pass',
            group1_observations_used=False,scientific_eligible=False,
            authorization='Proceed despite waiting for records; assumptions/constraints documented; six files first')
        def verify():
            for name,digest in {**manifest['sources'],**manifest['inputs']}.items():
                if il.sha256(name)!=digest:raise ValueError('frozen input/source changed')
            if runtime.numerical_environment()!=manifest['environment']:raise ValueError('environment changed')
        path=output/'manifest.json'
        if path.exists():
            if load(path)!=manifest:raise ValueError('manifest changed; separate freeze required')
        else:
            follow.atomic_json(path,manifest);(output/'source-freeze').mkdir()
            for p in sources:shutil.copyfile(p,output/'source-freeze'/p.name)
        ledger=estimator.StartLedger(output/'empirical-starts.jsonl',il.sha256(path))
        results=[];grid={a.name:a for a in sensitivity.assumptions()}
        for row in old['results']:
            verify();task=row['task_id'];target=output/(task+'.json')
            if target.exists():
                record=load(target)
                if record['manifest_sha256']!=il.sha256(path):raise ValueError('cached result manifest mismatch')
                results.append(record);continue
            artifact=prior/(task+'-factors.json.gz')
            if il.sha256(artifact)!=row['factors_sha256']:raise ValueError('factor hash mismatch')
            factors=load(artifact)['factors'];old_observation=load(root/'data/ilvis0-observation-20261007'/(task+'.json'))
            follow.atomic_json(output/'status.json',dict(state='preparing',task=task,completed=len(results),pid=os.getpid()))
            values,times,gps,provenance=prepare(follow.source_path(corpus,records[task]),row['provenance']['source_sha256'],
                factors,old_observation['provenance']['timing']['gps_minus_utc_s'])
            native_path=output/(task+'-native.csv.gz')
            if not native_path.exists():
                with native_path.open('wb') as binary:
                    with gzip.GzipFile(filename='',mode='wb',fileobj=binary,mtime=0) as compressed:
                        import io
                        with io.TextIOWrapper(compressed,encoding='utf-8',newline='') as out:
                            writer=csv.writer(out);writer.writerow(['packet_offset','utc_week_s','dt_header_s',*ap.RAW_FIELDS,
                                'theta_x','theta_y','theta_z','dv_x','dv_y','dv_z']);writer.writerows(values.tolist())
            metric=np.column_stack((1/(6378137.+gps[:,2]),1/((6378137.+gps[:,2])*np.cos(gps[:,0])),np.ones(len(gps))))
            blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
            covariances={name:sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,grid[name]) for name in manifest['gps_covariance_assumptions']}
            fits=[]
            for model,profile in [(m,True) for m in explore.MODELS]+[('sphere_rotating',False)]:
                label=model+('_profiled_correction' if profile else '_unsubtracted_control')
                cached=output/(task+'-'+label+'.json');verify()
                if cached.exists():
                    fit=load(cached)
                    if fit['manifest_sha256']!=il.sha256(path):raise ValueError('fit manifest mismatch')
                    fits.append(fit);continue
                seed,force=initial(times,gps,values,model)
                kwargs=dict(clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
                    maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.,fit_earth_removal=profile,kernel=kernel)
                problem=explore.ConditionalProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,
                    covariances['h1_v3_tau60'],seed,estimator.Bounds(explore.LIMITS),**kwargs)
                start=np.zeros(len(problem.bounds.active))
                for i,name in enumerate(problem.bounds.active):
                    if name.startswith('accel_gain'):start[i]=np.clip((force/9.81-1)/explore.LIMITS[name],-.9,.9)
                    if name=='earth_removal':start[i]=-1.
                follow.atomic_json(output/'status.json',dict(state='fitting',task=task,model=model,profile=profile,
                    completed=len(results),pid=os.getpid()))
                begin=time.monotonic()
                try:
                    fit=explore.fit_conditional(problem,model,ledger=ledger,task=task,maximum_evaluations=200,start=start)
                    point=np.array(fit['normalized_parameters']); prediction=problem.predict(point,model)
                    residual=(prediction-gps)/metric
                    fit.update(elapsed_s=time.monotonic()-begin,residual_rms_neu_m=np.sqrt(np.mean(residual**2,axis=0)).tolist(),
                        residual_max_abs_neu_m=np.max(abs(residual),axis=0).tolist(),
                        conservative_covariance_fixed_parameter_cost=None,header_clock_fixed_parameter_rms_neu_m=None)
                    conservative=explore.ConditionalProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,
                        covariances['h10_v30_tau300'],seed,estimator.Bounds(explore.LIMITS),**kwargs)
                    z=conservative.whiten(prediction-gps)
                    fit['conservative_covariance_fixed_parameter_cost']=float(z@z)
                    header_kwargs=dict(kwargs,clock_hypothesis='header_elapsed')
                    header=explore.ConditionalProblem(values[:,9:12],values[:,12:15],values[:,2],times,gps,
                        covariances['h1_v3_tau60'],seed,estimator.Bounds(explore.LIMITS),**header_kwargs)
                    h=(header.predict(point,model)-gps)/metric
                    fit['header_clock_fixed_parameter_rms_neu_m']=np.sqrt(np.mean(h*h,axis=0)).tolist()
                    fit['evaluations']+=2
                    fit['counterfactuals_are_refits']=False
                except (ValueError,FloatingPointError) as error:
                    fit=dict(error=str(error),scientific_decision='abstain',model=model)
                fit.update(label=label,task=task,manifest_sha256=il.sha256(path))
                verify();follow.atomic_json(cached,fit);fits.append(fit)
                print(json.dumps(dict(task=task,label=label,converged=fit.get('converged'),rms=fit.get('residual_rms_neu_m'),
                    evaluations=fit.get('evaluations'),error=fit.get('error'))),flush=True)
            record=dict(task=task,filename=row['filename'],provenance=provenance,fits=fits,
                native_sha256=il.sha256(native_path),manifest_sha256=il.sha256(path),scientific_decision='abstain')
            follow.atomic_json(target,record);results.append(record)
        summary=dict(version=explore.VERSION,state='complete',files=len(results),results=results,
            optimizer_starts=sum(1 for _ in (output/'empirical-starts.jsonl').open()),
            fits=sum(len(r['fits']) for r in results),converged_fits=sum(bool(f.get('converged')) for r in results for f in r['fits']),
            failed_fits=sum('error' in f for r in results for f in r['fits']),scientific_eligibility_changes=0,
            scientific_decision='abstain',originals_deleted=0)
        verify();observation.gzip_json(output/'summary.json.gz',summary)
        compact={k:v for k,v in summary.items() if k!='results'}
        compact.update(manifest_sha256=il.sha256(path),summary_sha256=il.sha256(output/'summary.json.gz'))
        follow.atomic_json(output/'completion.json',compact);follow.atomic_json(output/'status.json',compact)
        print(json.dumps(compact),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-exploratory-20261008'))
    args=parser.parse_args();run(Path(__file__).resolve().parents[2],args.output.resolve())
