# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary rows from supplied bound reports and explicitly declared allowances.

This audits arithmetic and shape, not the provenance or validity of a native
bound report or an error law. Callers must check those prerequisites separately.
No future measurements enter this interface. Frozen short controls are unchanged.
"""
from fractions import Fraction as F
import math

from .ilvis0_saved_prediction_audit import endpoint
from .ilvis0_training_remainder_audit import scaled_design


def _rows(value,count,columns,name):
    if (not isinstance(value,(list,tuple)) or len(value)!=count
            or any(not isinstance(row,(list,tuple)) or len(row)!=columns
                   or any(type(v) not in (int,float) or not math.isfinite(v) for v in row)
                   for row in value)):
        raise ValueError('complete finite '+name+' required')
    return [[float(v) for v in row] for row in value]


def _validated(training,reports,maximum_epochs,parameter_counts=(78,)):
    region=training['region']; times=training['times_s']; n=len(times)
    if (not 1<=n<=maximum_epochs or any(type(t) not in (int,float) or not math.isfinite(t) for t in times)
            or times[0]<0. or any(b<=a for a,b in zip(times,times[1:]))
            or region['parameter_count'] not in parameter_counts or len(region['center'])!=region['parameter_count'] or len(reports)!=n
            or any(type(v) not in (int,float) or not math.isfinite(v) for v in region['center'])):
        raise ValueError('complete ordered training epochs and every declared coordinate required')
    nominal=_rows(training['nominal'],n,3,'native centers')
    observations=_rows(training['observations'],n,3,'training observations')
    design=_rows(region['design'],3*n,51,'saved training design')
    if len(training['jacobian'])!=n:
        raise ValueError('complete training Jacobians required')
    arithmetic=F(region['arithmetic_allowance'])
    if arithmetic<0:raise ValueError('nonnegative saved arithmetic allowance required')
    matrices=[]
    for epoch,report in enumerate(reports):
        if report['time_s']!=times[epoch] or report['center']!=nominal[epoch]:
            raise ValueError('training time or transferred native center changed')
        matrix=scaled_design(training['jacobian'][epoch],report,region['coordinate_scale'])
        if matrix!=design[3*epoch:3*epoch+3]:
            raise ValueError('training coefficient changed; no silent basis transfer')
        remainder=report['unshared_remainder']
        if (len(remainder)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or v<0.
                                   for v in remainder)):
            raise ValueError('complete nonnegative finite propagation remainder required')
        matrices.extend(matrix)
    return region,times,nominal,observations,matrices,arithmetic


def training_rows(training,reports,*,observation_allowance_m):
    region,times,nominal,observations,matrices,arithmetic=_validated(training,reports,256)
    noise=_rows(observation_allowance_m,len(times),3,'observation allowances')
    if any(v<0. for row in noise for v in row):
        raise ValueError('nonnegative observation allowances required')
    rows=[]; lower=[]; upper=[]
    for epoch,report in enumerate(reports):
        remainder=report['unshared_remainder'];matrix=matrices[3*epoch:3*epoch+3]
        for axis,row in enumerate(matrix):
            shift=sum((F(v)*F(c) for v,c in zip(row,region['center'][:51],strict=True)),F(0))
            delta=(F(observations[epoch][axis])-F(nominal[epoch][axis]))*F(region['coordinate_scale'][axis])
            radius=F(remainder[axis])*F(region['coordinate_scale'][axis])+F(noise[epoch][axis])+arithmetic
            rows.append(row+[0.]*27)
            lower.append(endpoint(shift+delta-radius,False))
            upper.append(endpoint(shift+delta+radius,True))
    return dict(design=rows+[[-v for v in row] for row in rows],upper=upper+[-v for v in lower],
        physical_parameter_count=27,parameter_count=78,original_expression_columns=51,
        observation_allowance_m=noise,arithmetic_allowance_m=float(arithmetic),new_rows=6*len(times),
        error_law_qualified=False,future_observations_used=False,scientific_decision='abstain')


def projected_training_rows(training,reports,*,weights,observation_allowance_m,source_binding):
    """Necessary inequalities for signed combinations of full native expressions.

    The supplied scalar allowances must cover these exact fixed rows in the same
    frame/units. This function checks expression/source binding and arithmetic;
    it does not qualify the native enclosures or their statistical error law.
    Unknown signed propagation remainders are bounded with absolute weights.
    """
    import hashlib
    import json
    region,times,nominal,observations,matrices,arithmetic=_validated(training,reports,100000,(51,78))
    parameters=region['parameter_count']
    keys={'source_id','reference_binding','normalized_center','lower','upper'}
    if (not isinstance(source_binding,dict) or set(source_binding)!=keys
            or training.get('source_binding')!=source_binding
            or any(not isinstance(source_binding[k],str) or not source_binding[k] for k in ('source_id','reference_binding'))):
        raise ValueError('explicit matching source, frame/clock/processing and basis binding required')
    for key in ('normalized_center','lower','upper'):
        _rows([source_binding[key]],1,27,'source calibration '+key)
    if (any(not a<=b<=c for a,b,c in zip(source_binding['lower'],source_binding['normalized_center'],source_binding['upper'],strict=True))
            or any(any(report.get(key)!=source_binding[key] for key in keys) for report in reports)):
        raise ValueError('all native reports must retain the same physical source box and basis')
    box=_rows([region['lower'],region['upper']],2,parameters,'full enclosure box')
    if any(not a<=c<=b for a,c,b in zip(box[0],region['center'],box[1],strict=True)):
        raise ValueError('full box must contain its saved center')
    if (region['center'][:27]!=source_binding['normalized_center']
            or any(not a<=b<=c<=d for a,b,c,d in zip(source_binding['lower'],box[0][:27],
                box[1][:27],source_binding['upper'],strict=True))):
        raise ValueError('source calibration box and reference must cover the full physical region')
    if not isinstance(weights,(tuple,list)) or not weights:raise ValueError('nonempty fixed signed weights required')
    w=_rows(weights,len(weights),3*len(times),'fixed signed weights')
    noise=_rows([observation_allowance_m],1,len(w),'summary observation allowances')[0]
    if any(v<0 for v in noise):raise ValueError('nonnegative summary error allowances required')
    matrices=[[F(v) for v in row] for row in matrices]
    delta=[];remainders=[]
    for epoch,report in enumerate(reports):
        for axis,scale in enumerate(region['coordinate_scale']):
            delta.append((F(observations[epoch][axis])-F(nominal[epoch][axis]))*F(scale))
            remainders.append(F(report['unshared_remainder'][axis])*F(scale)+arithmetic)
    rows=[];lower=[];upper=[];unshared=[];rounding=[]
    for values,allowance in zip(w,noise,strict=True):
        active=[(i,F(v)) for i,v in enumerate(values) if v]
        exact=[sum((v*matrices[i][k] for i,v in active),F(0)) for k in range(51)]
        row=list(map(float,exact))
        if not all(math.isfinite(v) for v in row):raise ValueError('finite projected coefficients required')
        roundoff=sum((abs(F(a)-b)*max(abs(F(lo)),abs(F(hi)))
            for a,b,lo,hi in zip(row,exact,box[0][:51],box[1][:51],strict=True)),F(0))
        shift=sum((a*F(c) for a,c in zip(exact,region['center'][:51],strict=True)),F(0))
        center=shift+sum((v*delta[i] for i,v in active),F(0))
        remainder=sum((abs(v)*remainders[i] for i,v in active),F(0))
        radius=F(allowance)+remainder+roundoff
        rows.append(row+[0.]*(parameters-51));lower.append(endpoint(center-radius,False));upper.append(endpoint(center+radius,True))
        unshared.append(endpoint(remainder,True));rounding.append(endpoint(roundoff,True))
    expression=dict(nominal=nominal,observations=observations,design=region['design'],
        unshared_remainders=[r['unshared_remainder'] for r in reports],arithmetic_allowance=region['arithmetic_allowance'],
        lower=box[0],upper=box[1],center=region['center'])
    expression_id=hashlib.sha256(json.dumps(expression,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    binding=dict(source=source_binding,times_s=times,coordinate_scale=region['coordinate_scale'],
        expression_sha256=expression_id,
        weights=w,expression_columns=51,physical_parameter_count=27,enclosure_parameter_count=parameters)
    raw=json.dumps(binding,sort_keys=True,separators=(',',':')).encode()
    identity=hashlib.sha256(raw).hexdigest();binding=json.loads(raw)
    return dict(design=rows+[[-v for v in row] for row in rows],upper=upper+[-v for v in lower],
        physical_parameter_count=27,parameter_count=parameters,original_expression_columns=51,new_rows=2*len(w),
        observation_allowance_m=noise,unshared_radius_m=unshared,coefficient_rounding_radius_m=rounding,
        projected_training_id=identity,binding=binding,error_law_qualified=False,
        future_observations_used=False,scientific_decision='abstain')
