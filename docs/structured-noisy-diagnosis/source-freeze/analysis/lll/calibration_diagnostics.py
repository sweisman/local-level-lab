# SPDX-License-Identifier: AGPL-3.0-or-later
"""Scalar saved-fit diagnostics, with no solver, numerical imports or new truth."""
import ast
import math
from collections import defaultdict,Counter
from statistics import median

INTRINSIC=tuple(prefix+'_'+axis for prefix in ('gyro_bias','accel_bias','gyro_gain','accel_gain','lever')
    for axis in 'xyz')+('time_offset',)


def frozen_reference(source,sign):
    """Evaluate only the calibration fixture in trusted, hash-verified source.

    Other top-level code and trajectory generators are never executed. This is
    not a sandbox for untrusted uploads or a reference for fitted starting state.
    """
    if type(sign) is not int or sign not in (-1,1):raise ValueError('declared calibration sign required')
    try:
        functions=[v for v in ast.parse(source).body if isinstance(v,ast.FunctionDef) and v.name=='_parameters']
        if len(functions)!=1 or functions[0].decorator_list:raise ValueError('one plain calibration function required')
        module=ast.Module(body=functions,type_ignores=[])
        namespace={'math':math,'__builtins__':{'tuple':tuple,'zip':zip,'dict':dict}}
        exec(compile(module,'<verified-calibration-reference>','exec'),namespace)
        result=namespace['_parameters'](sign)
        if not isinstance(result,dict):raise ValueError('calibration mapping required')
        result={k:v for k,v in result.items() if k in INTRINSIC}
        if not result or any(type(v) not in (int,float) or not math.isfinite(v) for v in result.values()):
            raise ValueError('finite intrinsic calibration reference required')
        return result
    except (SyntaxError,NameError,TypeError,ValueError,KeyError) as error:
        raise ValueError('unsupported frozen calibration function') from error


def fit_parameters(fit,limits,*,profile,reference):
    from .ilvis0_saved_audit import parameter_rows,_units
    if (not isinstance(reference,dict) or not set(reference)<=set(INTRINSIC)
            or any(type(v) not in (int,float) or not math.isfinite(v) for v in reference.values())):
        raise ValueError('finite intrinsic reference only; no initializer-dependent coordinates')
    rows=parameter_rows(fit,limits,profile=profile);gradients=fit.get('gradient')
    if (not isinstance(gradients,list) or len(gradients)!=len(rows)
            or any(type(v) not in (int,float) or not math.isfinite(v) for v in gradients)):
        raise ValueError('finite gradient for every saved parameter required')
    result=[]
    for row,gradient in zip(rows,gradients):
        name=row['parameter'];ref=reference.get(name);factor=_units(name)[0]
        result.append(dict(row,gradient_normalized=gradient,
            outward_descent_gradient=(gradient if row['boundary']=='lower' else
                -gradient if row['boundary']=='upper' else None),
            reference_value=None if ref is None else ref*factor,
            reference_inside_bounds=None if ref is None else row['lower_limit']<=ref*factor<=row['upper_limit'],
            error_in_bound_units=None if ref is None else
                (fit['parameters'][name]-ref)/limits[name]))
    return result


def summarize(fits):
    groups=defaultdict(list)
    for fit in fits:
        for row in fit['parameters']:groups[row['parameter']].append(row)
    result=[]
    for name,rows in sorted(groups.items()):
        counts=Counter(r['boundary'] for r in rows)
        result.append(dict(parameter=name,unit=rows[0]['unit'],fits=len(rows),
            lower=counts['lower'],upper=counts['upper'],interior=counts['interior'],
            median_value=median(r['value'] for r in rows),
            reference_outside_bounds=sum(r['reference_inside_bounds'] is False for r in rows)))
    return result


def column_cosines(linear,*,pairs):
    """Uncentered column geometry in the saved normalized/whitened Jacobian.

    This is not posterior correlation or a new rank/convergence decision.
    """
    names=linear['active_parameters'];matrix=linear['jacobian']
    if (not names or len(set(names))!=len(names) or not matrix
            or any(len(row)!=len(names) or any(type(v) not in (int,float) or not math.isfinite(v) for v in row) for row in matrix)
            or any(a not in names or b not in names or a==b for a,b in pairs)):
        raise ValueError('complete finite saved Jacobian and declared distinct columns required')
    values=[]
    for a,b in pairs:
        x=[row[names.index(a)] for row in matrix];y=[row[names.index(b)] for row in matrix]
        nx=math.hypot(*x);ny=math.hypot(*y)
        cosine=None if not nx or not ny else max(-1.,min(1.,math.fsum(u/nx*v/ny for u,v in zip(x,y))))
        values.append(dict(parameter_a=a,parameter_b=b,cosine=cosine,
            column_a_norm=nx,column_b_norm=ny))
    return values
