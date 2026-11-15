# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe saved ESA conditional receiver errors without refitting."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_conditional_forecast_report import (HISTORICAL, MANIFEST_SHA256,
    SCORING_SHA256, STUDY, TASK)


def training_vertical(times,difference,*,last_count):
    """Describe the sealed training receiver-minus-forecast height trend."""
    import statistics
    import numpy as np
    times=np.asarray(times,dtype=float);difference=np.asarray(difference,dtype=float)
    if (times.ndim!=1 or len(times)<2 or difference.shape!=(len(times),3) or
            type(last_count) is not int or not 2<=last_count<=len(times) or
            not np.all(np.isfinite(times)) or not np.all(np.isfinite(difference)) or
            np.any(np.diff(times)<=0)):
        raise ValueError('complete finite aligned ordered training series required')
    error=-difference[:,2]
    full=statistics.linear_regression(times,error)
    tail=statistics.linear_regression(times[-last_count:],error[-last_count:])
    return dict(first_m=float(error[0]),last_m=float(error[-1]),
        mean_m=float(np.mean(error)),rms_m=float(np.sqrt(np.mean(error*error))),
        full_slope_m_per_min=float(60*full.slope),
        last_slope_m_per_min=float(60*tail.slope),last_count=last_count,
        last_mean_m=float(np.mean(error[-last_count:])))


def receiver_boundary(rows,*,cut,window):
    """Report separate receiver velocity across a fixed split."""
    import statistics
    import numpy as np
    if (type(cut) is not int or type(window) is not int or
            not 2<=window<=cut<len(rows)-window+1):
        raise ValueError('interior receiver split and complete windows required')
    try:
        time=np.asarray([r['time_s'] for r in rows],dtype=float)
        north=np.asarray([r['north_mps'] for r in rows],dtype=float)
        east=np.asarray([r['east_mps'] for r in rows],dtype=float)
        up=np.asarray([r['up_mps'] for r in rows],dtype=float)
    except (KeyError,TypeError) as exc:
        raise ValueError('complete receiver velocity rows required') from exc
    if (not all(np.all(np.isfinite(v)) for v in (time,north,east,up)) or
            np.any(np.diff(time)<=0)):
        raise ValueError('finite ordered receiver velocities required')
    speed=np.hypot(north,east)
    course=np.degrees(np.arctan2(east,north))%360
    def row(i):
        return dict(speed_mps=float(speed[i]),course_deg=float(course[i]),
            up_mps=float(up[i]))
    before=row(cut-1);after=row(cut)
    turn=float((after['course_deg']-before['course_deg']+180)%360-180)
    return dict(before=before,after=after,
        time_gap_s=float(time[cut]-time[cut-1]),
        speed_change_mps=after['speed_mps']-before['speed_mps'],
        course_change_deg=turn,up_change_mps=after['up_mps']-before['up_mps'],
        window_epochs=window,
        pre_mean_speed_mps=float(statistics.mean(speed[cut-window:cut])),
        post_mean_speed_mps=float(statistics.mean(speed[cut:cut+window])),
        pre_up_sd_mps=float(statistics.pstdev(up[cut-window:cut])),
        post_up_sd_mps=float(statistics.pstdev(up[cut:cut+window])))


def vertical_correction(raw,conditional,receiver):
    """Decompose signed later height error without changing the forecast."""
    import numpy as np
    raw,conditional,receiver=(np.asarray(x,dtype=float)
                              for x in (raw,conditional,receiver))
    if (raw.ndim!=2 or raw.shape[1:]!=(3,) or len(raw)<1 or
            conditional.shape!=raw.shape or receiver.shape!=raw.shape or
            not all(np.all(np.isfinite(x)) for x in (raw,conditional,receiver))):
        raise ValueError('complete finite aligned later routes required')
    values=dict(raw_receiver_minus_forecast_m=receiver[:,2]-raw[:,2],
        conditional_adjustment_m=conditional[:,2]-raw[:,2],
        conditional_receiver_minus_forecast_m=receiver[:,2]-conditional[:,2])
    if not np.allclose(values['raw_receiver_minus_forecast_m'],
                       values['conditional_adjustment_m']+
                       values['conditional_receiver_minus_forecast_m'],
                       rtol=0,atol=1e-10):
        raise ValueError('vertical correction identity differs')
    return {key:dict(first=float(v[0]),last=float(v[-1]),
        mean=float(np.mean(v)),rms=float(np.sqrt(np.mean(v*v))))
        for key,v in values.items()}


def describe_coverage(forecast, receiver, covariance, *,
                      parameter_uncertainty_included=False):
    """Descriptive marginal coverage; fitted-parameter uncertainty is absent."""
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors
    from .models import radii

    forecast=np.asarray(forecast,dtype=float)
    receiver=np.asarray(receiver,dtype=float)
    covariance=np.asarray(covariance,dtype=float)
    if (type(parameter_uncertainty_included) is not bool or
            forecast.ndim!=2 or forecast.shape[1:]!=(3,) or len(forecast)<1 or
            receiver.shape!=forecast.shape or covariance.shape!=(len(forecast),3,3) or
            not all(np.all(np.isfinite(v)) for v in (forecast,receiver,covariance))):
        raise ValueError('complete finite aligned forecast, receiver and covariance required')
    scale=np.maximum(np.abs(covariance),np.abs(covariance.transpose(0,2,1)))
    if np.any(np.abs(covariance-covariance.transpose(0,2,1))>1e-10*scale):
        raise ValueError('symmetric covariance required')
    try:
        factors=np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError as exc:
        raise ValueError('positive definite covariance required') from exc

    # The saved covariance uses radians/radians/metres. Match receiver_errors'
    # local coordinate metric before reporting physical-unit standard deviations.
    rm,rn=radii(receiver[:,0])
    metric=np.column_stack((rm+receiver[:,2],
        (rn+receiver[:,2])*np.cos(receiver[:,0]),np.ones(len(receiver))))
    errors=-receiver_errors(forecast,receiver)
    sigma=np.diagonal(factors@factors.transpose(0,2,1),axis1=1,axis2=2)**0.5
    normalized=errors/(sigma*metric)
    coordinate_errors=errors/metric
    distance=np.linalg.solve(factors,coordinate_errors[...,None])[...,0]
    mahalanobis=np.sum(distance*distance,axis=1)
    axes={}
    for j,label in enumerate(('north','east','up')):
        values=normalized[:,j]
        lag=(float(np.corrcoef(values[:-1],values[1:])[0,1])
             if len(values)>2 and np.std(values[:-1])>0 and np.std(values[1:])>0
             else None)
        axes[label]=dict(mean_normalized=float(np.mean(values)),
            mean_error_m=float(np.mean(errors[:,j])),
            first_error_m=float(errors[0,j]),last_error_m=float(errors[-1,j]),
            normalized_rms=float(np.sqrt(np.mean(values*values))),
            nominal_95_fraction=float(np.mean(np.abs(values)<=1.959963984540054)),
            lag_one_normalized_correlation=lag,
            sigma_m_range=[float(np.min(sigma[:,j]*metric[:,j])),
                           float(np.max(sigma[:,j]*metric[:,j]))])
    return dict(epochs=len(receiver),axes=axes,
        nominal_95_ellipsoid_fraction=float(np.mean(mahalanobis<=7.814727903251179)),
        maximum_mahalanobis_squared=float(np.max(mahalanobis)),
        covariance_positive_definite=True,
        parameter_uncertainty_included=parameter_uncertainty_included,
        calibrated_coverage=False)


def build(root):
    import numpy as np
    from .studies.closed import ClosedStudy

    root=Path(root).resolve()
    study=ClosedStudy(root,STUDY)
    historical=ClosedStudy(root,HISTORICAL)
    try:
        if (study.completion['manifest_sha256']!=MANIFEST_SHA256 or
                study.completion['state']!='complete' or study.summary['completed']!=1 or
                study.summary['total']!=1 or study.rows[TASK]['passed'] is not True or
                historical.manifest['inputs']['scoring']['sha256']!=SCORING_SHA256):
            raise ValueError('exact sealed conditional forecast and scoring input required')
        saved=study.artifact(TASK,'conditional-forecast.json')
        weighted=study.input('weighted-forecast')
        if (saved['training_epochs']!=800 or saved['prediction_epochs']!=400 or
                saved['optimization_performed'] is not False or
                saved['later_receiver_values_used'] is not False or
                saved['fixed_calibration_only'] is not True or
                saved['scientific_decision']!='abstain' or
                weighted['training_epochs']!=800 or
                weighted['coordinates']!=saved['raw_coordinates']):
            raise ValueError('sealed early-only forecast required')
        rows=json.loads(gzip.decompress(historical.input('scoring',raw=True)))
        if len(rows)!=1200:raise ValueError('complete later receiver rows required')
        receiver=np.asarray([[math.radians(row['latitude_deg']),
            math.radians(row['longitude_deg']),row['height_m']] for row in rows[800:]])
        coverage=describe_coverage(saved['conditional_receiver_mean'],receiver,
            saved['conditional_receiver_covariance'])
        correction=vertical_correction(np.asarray(saved['raw_coordinates'])[800:],
            saved['conditional_receiver_mean'],receiver)
        training=training_vertical(weighted['times_s'][:800],
            weighted['training_coordinate_difference'],last_count=200)
        boundary=receiver_boundary(rows,cut=800,window=200)
        return dict(version='esa-saved-conditional-coverage-diagnostic-v4',
            study=STUDY,manifest_sha256=MANIFEST_SHA256,scoring_sha256=SCORING_SHA256,
            vertical_correction=correction,training_vertical=training,
            receiver_boundary=boundary,
            reporter_sha256=hashlib.sha256((root/'analysis/lll/esa_conditional_coverage_report.py')
                .read_bytes()).hexdigest(),diagnostic=coverage,
            later_receiver_used_for_fit=False,protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:
        historical.close();study.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    result=build(args.root)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result['diagnostic'],sort_keys=True))


if __name__=='__main__':main()
