# SPDX-License-Identifier: AGPL-3.0-or-later
"""Observe existing propagation values without replacing any arithmetic."""
import inspect
import sys
import gzip
import json


def observe(*args,**kwargs):
    from lll import ilvis0_acceleration_native as native
    if sys.gettrace() is not None:raise ValueError('an existing trace must not be replaced')
    root=native.enclose.__code__;increment=native._increment.__code__
    action=native.relative.action.__code__;product=native.matrix_vector.__code__
    lines,first=inspect.getsourcelines(native.enclose)
    matches=[first+i for i,line in enumerate(lines) if line.lstrip().startswith('velocity=add(add(initial_velocity,')]
    if len(matches)!=1:raise ValueError('frozen propagation observation point changed')
    snapshot_line=matches[0];pending={};increments=[];records=[]
    def value(v):return dict(center=v.center.tolist(),change=float(v.change),remainder=float(v.remainder))
    def coordinates(v):return [value(x.value) for x in (v.latitude,v.longitude,v.height)]
    def local(frame,event,arg):
        code=frame.f_code
        if code==increment and event=='return' and arg is not None:
            row=pending.pop(id(frame),{});scope=frame.f_locals
            row.update(force_rest=value(scope['force_rest']),rhs=value(scope['rhs']),du=value(arg[2]),
                argument=value(scope['argument']),state_velocity=value(scope['state'].velocity))
            increments.append(row)
        elif code in (action,product) and event=='return' and arg is not None:
            parent=frame.f_back
            if parent is not None and parent.f_code==increment:
                row=pending.setdefault(id(parent),{})
                if code==action:row['reference_action']=value(arg)
                elif 'difference_action' not in row:row['difference_action']=value(arg)
                else:row['inverse_action']=value(arg)
        elif code==root and event=='line' and frame.f_lineno==snapshot_line:
            scope=frame.f_locals
            if len(increments)!=2:raise ValueError('both midpoint evaluations must be observed')
            records.append(dict(packet_index=scope['index'],start_s=float(scope['start']),
                end_s=float(scope['next_common'].center),increments=list(increments),
                residual_velocity=value(scope['u']),departures=coordinates(scope['departures']),
                unfactored_position=coordinates(scope['position'])))
            increments.clear()
        return local
    def dispatch(frame,event,arg):
        if frame.f_code in (root,increment):return local
        if frame.f_code in (action,product) and frame.f_back is not None and frame.f_back.f_code==increment:return local
        return None
    try:
        sys.settrace(dispatch);result=native.enclose(*args,**kwargs)
    finally:sys.settrace(None)
    if pending or increments or len(records)!=result.metadata['used_packet_count']:
        raise ValueError('incomplete propagation observation sequence')
    return result,records


def evaluate(task,context):
    import math
    from lll import ilvis0_acceleration_native as native
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_sharded_native import read,plain,compare_bound
    from lll.ilvis0_receipt_journal import durable_write
    bundle=read(context.input_path());case=read(context.input_path(task['payload']['case_key']))
    expected=bundle['expected'];config=case['configuration'];box=sector(4)
    reference=native.make_reference(config,case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center'])
    compare_bound(reference.report(),expected['reference'])
    context.charge(bound_calls=1,bound_steps=len(case['dt']))
    report,records=observe(config,case['theta'],case['dv'],case['dt'],time=expected['time_s'],
        lower=expected['lower'],upper=expected['upper'],reference=reference,maximum_seconds=180.)
    actual=plain(report.report());context.save('observed-bound.json',actual)
    compare_bound(actual,{key:expected[key] for key in actual})
    path=context.directory/'trace.json.gz'
    durable_write(path,gzip.compress(json.dumps(records,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0));context.note_file(path)
    increments=[item for row in records for item in row['increments']]
    scale=[6371000.,6371000.*math.cos(config['initial_c'][0]),1.]
    return dict(passed=True,identity=task['identity'],model=config['model'],profile=config['profile'],sector=4,
        observed_packets=len(records),observed_midpoint_evaluations=len(increments),exact_report_match=True,
        reference_action_max_remainder_mps2=max(row['reference_action']['remainder'] for row in increments),
        difference_action_max_remainder_mps2=max(row['difference_action']['remainder'] for row in increments),
        force_rest_max_remainder_mps2=max(row['force_rest']['remainder'] for row in increments),
        increment_max_remainder_mps=max(row['du']['remainder'] for row in increments),
        final_residual_velocity_remainder_mps=records[-1]['residual_velocity']['remainder'],
        final_departure_remainder_m=[v['remainder']*s for v,s in zip(records[-1]['departures'],scale)],
        position_remainder_m=[v*s for v,s in zip(actual['position_unshared_remainder'],scale)],
        bound_evaluations=1,native_evaluations=0,optimizer_starts=0,original_reads=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
