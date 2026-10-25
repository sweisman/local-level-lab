# SPDX-License-Identifier: AGPL-3.0-or-later
"""Chronological prediction diagnostics; no fitting or significance decisions."""
import math

import numpy as np
from scipy.linalg import solve_triangular

from . import ilvis0_residuals as stats

VERSION = 'ilvis0-retrospective-prediction-v1'


def split(times):
    t=np.asarray(times,dtype=float)
    if t.ndim!=1 or len(t)<9 or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0):
        raise ValueError('at least nine increasing receiver epochs required')
    cut=2*len(t)//3
    return dict(training_epochs=cut,prediction_epochs=len(t)-cut,
        first_training_time_s=float(t[0]),last_training_time_s=float(t[cut-1]),
        first_prediction_time_s=float(t[cut]),last_prediction_time_s=float(t[-1]),
        selection='first floor(2*N/3) epochs train; remaining epochs predict')


def training_inputs(times,gps,values,time_offset_limit):
    """Pass only the training GPS and prefix needed for its native timing support."""
    t=np.asarray(times,dtype=float); g=np.asarray(gps,dtype=float); v=np.asarray(values,dtype=float)
    cut=split(t)['training_epochs']
    if (g.shape!=(len(t),3) or not np.all(np.isfinite(g)) or v.ndim!=2 or v.shape[1]!=15
        or not np.all(np.isfinite(v)) or np.any(v[:,2]<=0)
        or not math.isfinite(time_offset_limit) or time_offset_limit<0):
        raise ValueError('invalid training input shapes or intervals')
    ends=np.cumsum(v[:,2]); required=t[cut-1]+time_offset_limit
    count=int(np.searchsorted(ends,required,side='left'))+1
    if count>len(v) or t[0]-time_offset_limit<0:
        raise ValueError('training epochs lack native timing support')
    return t[:cut].copy(),g[:cut].copy(),v[:count].copy()


def conditional_errors(covariance,errors,training_components):
    """Condition receiver error on training residuals, with parameters held fixed."""
    c=np.asarray(covariance,dtype=float); r=np.asarray(errors,dtype=float)
    n=training_components
    if (r.ndim!=1 or c.shape!=(len(r),len(r)) or not isinstance(n,int) or not 0<n<len(r)
        or not np.all(np.isfinite(c)) or not np.all(np.isfinite(r))
        or not np.allclose(c,c.T,rtol=1e-12,atol=0)):
        raise ValueError('finite symmetric covariance and aligned errors required')
    try: lower=np.linalg.cholesky(c)
    except np.linalg.LinAlgError as error: raise ValueError('positive definite covariance required') from error
    ztrain=solve_triangular(lower[:n,:n],r[:n],lower=True,check_finite=False)
    conditioned=r[n:]-lower[n:,:n]@ztrain
    conditional_factor=lower[n:,n:]
    z=solve_triangular(conditional_factor,conditioned,lower=True,check_finite=False)
    return dict(training_innovations=ztrain,conditional_errors=conditioned,innovations=z,
                conditional_covariance=conditional_factor@conditional_factor.T)


def diagnostics(times,gps,coordinate_errors,primary_covariance,conservative_covariance):
    t=np.asarray(times,dtype=float); g=np.asarray(gps,dtype=float)
    error=np.asarray(coordinate_errors,dtype=float); layout=split(t); cut=layout['training_epochs']
    if (g.shape!=error.shape or g.shape!=(len(t),3) or not np.all(np.isfinite(g))
        or not np.all(np.isfinite(error)) or np.any(abs(g[:,0])>=math.pi/2)):
        raise ValueError('finite aligned nonpolar receiver/error coordinates required')
    metric=np.column_stack((1/(6378137.+g[:,2]),
                1/((6378137.+g[:,2])*np.cos(g[:,0])),np.ones(len(t))))
    if not np.all(metric>0): raise ValueError('invalid receiver height/metric')
    physical=error/metric
    p=conditional_errors(primary_covariance,error.ravel(),3*cut)
    c=conditional_errors(conservative_covariance,error.ravel(),3*cut)
    primary=np.concatenate((p['training_innovations'],p['innovations'])).reshape(-1,3)
    conservative=np.concatenate((c['training_innovations'],c['innovations'])).reshape(-1,3)
    result=dict(version=VERSION,split=layout,prospective_validation=False,
        prediction_receiver_positions_used_in_training=False,parameter_uncertainty_included=False,
        covariance_conditioning='C_PT C_TT^-1 applied to training residuals; Schur covariance',
        physical_metric='common reference radius 6378137 m plus receiver height; north/east/up',
        scientific_decision='abstain')
    for name,section in [('training',slice(0,cut)),('prediction',slice(cut,None))]:
        raw=physical[section]; white=primary[section]; generous=conservative[section]
        rms=np.sqrt(np.mean(raw*raw,axis=0))
        report=stats.summarize(t[section],raw,white,generous,{})
        report.update(horizontal_rms_m=float(math.hypot(*rms[:2])),vertical_rms_m=float(rms[2]),
            rms_neu_m=rms.tolist(),primary_conditional_cost=float(np.sum(white*white)),
            conservative_conditional_cost=float(np.sum(generous*generous)),
            prospective_validation=False,parameter_uncertainty_included=False)
        result[name]=report
    result['epoch_rows']=[]
    for i in range(len(t)):
        row=dict(epoch=i,time_s=float(t[i]),role='training' if i<cut else 'prediction')
        for j,axis in enumerate(('north','east','up')):
            row[axis+'_coordinate_error']=float(error[i,j])
            row[axis+'_direct_error_m']=float(physical[i,j])
            row[axis+'_primary_innovation']=float(primary[i,j])
            row[axis+'_conservative_innovation']=float(conservative[i,j])
        result['epoch_rows'].append(row)
    return result
