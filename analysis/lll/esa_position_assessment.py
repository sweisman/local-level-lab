# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only development diagnosis; never an eligibility replacement."""
import math
import re


def position_covariance(row):
    nn,ee,hh=row['position_variance_m2'];en,nh,eh=row['position_cross_covariance_m2']
    return [[nn,en,nh],[en,ee,eh],[nh,eh,hh]]


def precision_checked(lines,*,maximum_records=100000):
    if type(maximum_records)!=int or maximum_records<1:raise ValueError('finite receiver record limit required')
    count=0
    for line in lines:
        text=line.decode('ascii') if isinstance(line,bytes) else line;parts=text.split()
        if parts and re.fullmatch(r'\d{8}',parts[0]):
            if count>=maximum_records:raise ValueError('receiver epoch allowance exhausted before decoding')
            count+=1
            if len(parts)<4 or any(not re.fullmatch(r'[+-]?\d+\.\d{'+str(d)+r',}',parts[k])
                    for k,d in ((1,10),(2,10),(3,3))):
                raise ValueError('declared ten-decimal-degree / millimetre export precision required')
        yield line


def window_indices(times,sequence,index):
    import numpy as np
    t=np.asarray(times,float);seq=np.asarray(sequence);lower=t[index]-5.;upper=t[index]+5.
    if lower<t[0] or upper>t[-1]:return None
    a=int(np.searchsorted(t,lower,side='left'));b=int(np.searchsorted(t,upper,side='right'))
    first=a if t[a]==lower else a-1;last=b-1 if t[b-1]==upper else b
    if first<0 or last>=len(t) or b-a<4:return None
    if np.any(np.diff(t[first:last+1])>.75) or np.any(np.diff(seq[first:last+1])!=1):return None
    return a,b


class Windows:
    def __init__(self,maximum,save,check):
        if type(maximum)!=int or not 1<=maximum<=2048:raise ValueError('finite window allowance required')
        self.maximum=maximum;self.save=save;self.check=check;self.used=0
        self.calls=dict(position=0,point=0,residual=0)

    def begin(self,index):
        self.check()
        if self.used>=self.maximum:raise ValueError('window allowance exhausted')
        ordinal=self.used+1
        self.save(f'window-{ordinal:04d}-reservation.json',dict(windows=ordinal,index=index,
            maximum_windows=self.maximum,maximum_calls=dict(position=1,point=1,residual=1)))
        self.used=ordinal;seen=set()
        def claim(kind):
            self.check()
            if kind not in self.calls or kind in seen:raise ValueError('window stage cannot be repeated')
            seen.add(kind);self.calls[kind]+=1
        return claim


def residual_diagnostic(times,chart,*,center_s):
    import numpy as np
    t=np.asarray(times,float);p=np.asarray(chart,float);tau=(t-center_s)/5.
    design=np.column_stack((np.ones(len(t)),tau,tau**2,tau**3))
    coefficient,_,rank,_=np.linalg.lstsq(design,p,rcond=None)
    if rank!=4:raise ValueError('all cubic coefficients required')
    residual=p-design@coefficient;rms=np.sqrt(np.mean(residual**2,axis=0));correlation=[]
    for axis in range(3):
        left=residual[:-1,axis];right=residual[1:,axis]
        correlation.append(None if min(np.std(left),np.std(right))<1e-9 else float(np.corrcoef(left,right)[0,1]))
    return dict(rms_m=rms.tolist(),lag1=correlation,residuals_m=residual.tolist(),
        correlation_numerical_floor_m=1e-9,covariance_calibrated=False)


def assess_window(rows,times,sequence,index,old,*,claim):
    import numpy as np
    from lll.airquantumgrav_position_motion import assess,course_box
    common=dict(index=index,time_s=rows[index]['time_s'],airborne_supported=old.get('airborne_supported')=='True',
        previous_motion_failed=old.get('version1_motion_failed')=='True',
        eligibility_policy_changed=False,scientific_decision='abstain')
    support=window_indices(times,sequence,index)
    if support is None:return dict(common,supported=False,reason='incomplete_ten_second_support')
    a,b=support;selected=rows[a:b];t=np.asarray(times[a:b]);center=float(times[index])
    p=np.array([[math.radians(r['latitude_deg']),math.radians(r['longitude_deg']),r['height_m']] for r in selected])
    covariance=np.array([position_covariance(r) for r in selected])
    claim('position')
    try:result=assess(t,p,covariance,center_s=center,degree=3,maximum_gap_s=.75,alpha=.01,
        rounding_m=[1e-5,1e-5,.0005],time_constant_s=-.5/math.log(.8))
    except ValueError as error:return dict(common,supported=False,reason=str(error),source_indices=[a,b])
    claim('point');jet=np.array(result['geodetic_jet']);point=course_box(np.column_stack((jet,jet)))
    velocity=np.array([[r['north_mps'],r['east_mps']] for r in selected]);mean_velocity=velocity.mean(axis=0)
    ne=[sum(point[name])/2 for name in ('north_mps','east_mps')] if point['supported'] else None
    origin=np.array(result['chart_origin']);scale=np.array(result['chart_scales'])
    chart=np.column_stack(((p[:,0]-origin[0])*scale[0],(np.unwrap(p[:,1])-origin[1])*scale[1],p[:,2]-origin[2]))
    claim('residual');residual=residual_diagnostic(t,chart,center_s=center)
    if max(abs(a-b) for a,b in zip(residual['rms_m'],result['chart_residual_rms_m']))>1e-8:
        raise ValueError('independent cubic residual calculation disagrees')
    old_rate=old.get('trend_rate_deg_s');old_rate=float(old_rate) if old_rate else None
    new_rate=result['point_course_rate_deg_s']
    return dict(common,supported=True,source_indices=[a,b],actual_fit_support_s=[float(t[0]),float(t[-1])],
        epochs=len(t),position_course_rate_deg_s=new_rate,old_velocity_course_rate_deg_s=old_rate,
        course_rate_difference_deg_s=None if old_rate is None or new_rate is None else new_rate-old_rate,
        mean_reported_speed_kmh=float(np.hypot(velocity[:,0],velocity[:,1]).mean()*3.6),
        median_abs_reported_vertical_mps=float(np.median([abs(r['up_mps']) for r in selected])),
        position_point_ne_mps=ne,mean_reported_ne_mps=mean_velocity.tolist(),
        position_minus_reported_ne_mps=None if ne is None else (np.array(ne)-mean_velocity).tolist(),
        median_reported_position_sd_m=np.median(np.sqrt(np.diagonal(covariance,axis1=1,axis2=2)),axis=0).tolist(),
        median_reported_velocity_sd_mps=np.median(np.sqrt(np.array([np.diag(r['velocity_covariance_m2_s2']) for r in selected])),axis=0).tolist(),
        position=result,residual=residual,observational_covariance_verified=False)


def evaluate(task,context):
    import csv
    import gzip
    import json
    import numpy as np
    from lll.airquantumgrav_motion import velocity_records
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue,path_within,_sha
    from lll.ilvis0_receipt_journal import durable_write
    spec=task['payload'];definition=read(context.input_path())
    if (spec!=dict(maximum_windows=2048,maximum_epochs=100000) or definition['recording']!=187
            or definition['maximum_receiver_reads']!=1 or definition['maximum_windows']!=2048):
        raise ValueError('single development recording and finite saved-window scope required')
    context.save('receiver-read-reservation.json',dict(receiver_reads=1,maximum_epochs=100000))
    reference=read(context.input_path('receiver-reference'))
    source=path_within(context.root.parent.parent,reference['path']);rows=[]
    if source.stat().st_size!=reference['bytes'] or _sha(source)!=reference['sha256']:
        raise ValueError('retained original receiver file changed')
    with source.open() as handle:
        for row in velocity_records(precision_checked(handle)):
            if len(rows)>=100000:raise ValueError('receiver epoch allowance exhausted')
            rows.append(row)
    if len(rows)!=definition['expected_epochs']:raise ValueError('saved receiver epoch count changed')
    with context.input_path('old-windows').open() as handle:baseline=list(csv.DictReader(handle))
    indices=[int(r['index']) for r in baseline]
    if (len(indices)!=2048 or len(set(indices))!=2048 or indices!=sorted(indices)
            or indices!=definition['indices'] or min(indices)<0 or max(indices)>=len(rows)):
        raise ValueError('complete original fixed center list required')
    times=np.array([r['time_s'] for r in rows]);sequence=np.array([r['sequence'] for r in rows])
    budget=Windows(2048,context.save,lambda:_check_continue(context.root,context.manifest));results=[]
    for index,old in zip(indices,baseline,strict=True):
        claim=budget.begin(index);results.append(assess_window(rows,times,sequence,index,old,claim=claim))
    artifact=context.directory/'windows.json.gz';artifact.parent.mkdir(parents=True,exist_ok=True)
    durable_write(artifact,gzip.compress(json.dumps(plain(results),sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0))
    context.note_file(artifact)
    supported=[r for r in results if r['supported']];airborne=[r for r in supported if r['airborne_supported']]
    counts={}
    for mode in ('independent','supplied_correlation','arbitrary_correlation'):
        intervals=[r['position']['intervals'][mode] for r in airborne]
        counts[mode]=dict(supported=sum(v['supported'] for v in intervals),
            wholly_quiet=sum(v['supported'] and v['lower_deg_s']>=-.02 and v['upper_deg_s']<=.02 for v in intervals),
            definitely_turning=sum(v['supported'] and (v['lower_deg_s']>.02 or v['upper_deg_s']<-.02) for v in intervals))
    return dict(identity=task['identity'],passed=len(results)==2048,receiver_reads=1,receiver_epochs=len(rows),
        windows_reserved=budget.used,actual_stage_calls=budget.calls,supported_windows=len(supported),
        airborne_supported=len(airborne),unsupported_windows=len(results)-len(supported),interval_counts=counts,
        point_turn_flags=sum(abs(r['position_course_rate_deg_s'])>.02 for r in airborne),
        old_velocity_point_turn_flags=sum(abs(r['old_velocity_course_rate_deg_s'])>.02 for r in airborne),
        old_inventory_eligible=0,new_eligible_inventory_created=False,eligibility_policy_changed=False,
        raw_imu_reads=0,native_evaluations=0,optimizer_starts=0,protected_confirmation_reads=0,
        observational_coverage_calibrated=False,scientific_decision='abstain')
