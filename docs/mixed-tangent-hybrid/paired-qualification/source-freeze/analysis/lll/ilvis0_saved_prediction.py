# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-epoch prediction reductions; no observations, integration or fitting."""
import math


def _metrics(rows):
    count=len(rows)
    if not count:raise ValueError('nonempty saved error section required')
    rms=lambda values:math.sqrt(math.fsum(v*v for v in values)/count)
    n=[r['north'] for r in rows];e=[r['east'] for r in rows];u=[r['up'] for r in rows]
    horizontal=[math.hypot(a,b) for a,b in zip(n,e)]
    return dict(count=count,start_time_s=rows[0]['time'],end_time_s=rows[-1]['time'],duration_s=rows[-1]['time']-rows[0]['time'],
        north_rms_m=rms(n),east_rms_m=rms(e),vertical_rms_m=rms(u),horizontal_rms_m=rms(horizontal),
        final_horizontal_m=horizontal[-1],final_signed_up_m=u[-1],maximum_horizontal_m=max(horizontal),
        maximum_absolute_up_m=max(abs(x) for x in u),
        mean_north_m=math.fsum(n)/count,mean_east_m=math.fsum(e)/count,mean_up_m=math.fsum(u)/count)


def summarize(rows,*,training_epochs,prediction_epochs,section_seconds=30.):
    if (type(training_epochs) is not int or type(prediction_epochs) is not int or min(training_epochs,prediction_epochs)<1
            or not math.isfinite(section_seconds) or section_seconds<=0. or len(rows)!=training_epochs+prediction_epochs):
        raise ValueError('complete saved split and finite positive section size required')
    parsed=[]
    for index,row in enumerate(rows):
        try:
            epoch=int(row['epoch']);time=float(row['time_s'])
            values=[float(row[axis+'_direct_error_m']) for axis in ('north','east','up')]
        except (KeyError,ValueError,TypeError) as error:raise ValueError('valid saved epoch/time/direct-error fields required') from error
        role='training' if index<training_epochs else 'prediction'
        if (epoch!=index or row.get('role')!=role or not math.isfinite(time) or not all(math.isfinite(v) for v in values)
                or (parsed and time<=parsed[-1]['time'])):
            raise ValueError('saved grid, roles or finite errors disagree')
        parsed.append(dict(time=time,north=values[0],east=values[1],up=values[2]))
    future=parsed[training_epochs:];origin=future[0]['time'];groups={}
    for row in future:
        section=int(math.floor((row['time']-origin)/section_seconds));groups.setdefault(section,[]).append(row)
    sections=[dict(_metrics(group),section=index,elapsed_start_s=group[0]['time']-origin,elapsed_end_s=group[-1]['time']-origin)
        for index,group in sorted(groups.items())]
    return dict(training=_metrics(parsed[:training_epochs]),prediction=_metrics(future),sections=sections,
        grid=[row['time'] for row in parsed],scientific_decision='abstain',new_optimizer_starts=0,new_native_calls=0)


def check_rms(result,*,horizontal,vertical=None):
    checks=[(result['horizontal_rms_m'],float(horizontal))]
    if vertical is not None:checks.append((result['vertical_rms_m'],float(vertical)))
    if any(not math.isfinite(saved) or not math.isclose(actual,saved,rel_tol=1e-9,abs_tol=1e-8) for actual,saved in checks):
        raise ValueError('saved epoch RMS disagrees with original published ledger')
    return True
