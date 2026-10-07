# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check same-instrument file continuity without repairing/interpolating data."""
from collections import defaultdict
import datetime as dt
import json
from pathlib import Path

from . import applanix as ap, ilvis0 as il
from .ilvis0_followup import (leap_seconds,read_context,timing_check,mapped_context,
                              screen_context,source_path,atomic_json)


def absolute_span(inspection):
    dates=sorted(inspection['gps']['dates'])
    weeks={dt.date.fromisoformat(d)-dt.timedelta(days=(dt.date.fromisoformat(d).weekday()+1)%7) for d in dates}
    if len(weeks)!=1:
        raise ValueError('ambiguous calendar week')
    base=dt.datetime.combine(weeks.pop(),dt.time(),tzinfo=dt.timezone.utc).timestamp()
    kinds={int(k)&15 for k in inspection['validation']['inventory']['time_types']}
    if len(kinds)!=1 or not kinds.issubset({1,2}):
        raise ValueError('unsupported or mixed timestamp basis')
    leap={leap_seconds(d) for d in dates}
    if len(leap)!=1:raise ValueError('leap transition')
    shift=leap.pop() if kinds=={1} else 0
    imu=inspection['imu']
    return base+imu['first_time_s']-shift,base+imu['last_time_s']-shift


def candidates(rows):
    grouped=defaultdict(list)
    for row in rows:grouped[row['configuration']].append(row)
    pairs=[];closest=[]
    for configuration,group in grouped.items():
        group.sort(key=lambda r:(r['start_epoch_s'],r['end_epoch_s']))
        for i,left in enumerate(group):
            for right in group[i+1:]:
                gap=right['start_epoch_s']-left['end_epoch_s']
                record=dict(configuration=configuration,left=left,right=right,gap_s=gap)
                if gap<=il.SCREEN_POLICY['maximum_context_gap_s']:pairs.append(record)
                else:closest.append(record);break
    return pairs,sorted(closest,key=lambda p:p['gap_s'])[:10]


def overlap_check(left,right):
    """Compare exact native timestamps and complete raw Group-4 packet bytes."""
    states=[dict(first=None,last=None,invalid_intervals=0),dict(first=None,last=None,invalid_intervals=0)]
    def checked(path,state):
        previous=None
        for frame in il.groups(path,4):
            row=ap.group4(frame)
            value=ap.increments(row,previous,True)
            if previous is not None and value['flags']:state['invalid_intervals']+=1
            state['first']=row if state['first'] is None else state['first']
            state['last']=row;previous=row
            yield frame
    a,b=iter(checked(left,states[0])),iter(checked(right,states[1]))
    x,y=next(a,None),next(b,None)
    matched=mismatched=missing=0
    previous_a=previous_b=None
    while x is not None and y is not None:
        tx,ty=ap.time_header(x)['time1_s'],ap.time_header(y)['time1_s']
        if tx==ty:
            matched+=1;mismatched+=x.packet!=y.packet
            previous_a,previous_b=tx,ty
            x,y=next(a,None),next(b,None)
        elif tx<ty:
            if previous_b is not None:missing+=1
            previous_a=tx;x=next(a,None)
        else:
            if previous_a is not None:missing+=1
            previous_b=ty;y=next(b,None)
    # Exhaust both strict iterators to check the entire remaining framing/checksum.
    for _ in a:pass
    for _ in b:pass
    last,first=states[0]['last'],states[1]['first']
    gap=first['time1_s']-last['time1_s'] if last and first else None
    expected=1/ap.RATE_HZ[first['rate_code']] if first and first['rate_code'] in ap.RATE_HZ else None
    same_basis=bool(last and first and all(last[k]==first[k] for k in ('imu_type','rate_code','time_types')))
    internally_continuous=not any(s['invalid_intervals'] for s in states)
    adjacent=bool(same_basis and internally_continuous and expected and .8*expected<=gap<=1.2*expected)
    return dict(exact_timestamp_matches=matched,packet_disagreements=mismatched,
                unmatched_in_overlap=missing,
                invalid_intervals=[s['invalid_intervals'] for s in states],native_boundary_gap_s=gap,
                continuous_adjacent_boundary_verified=adjacent,
                exact_overlap_verified=matched>0 and mismatched==0 and missing==0 and internally_continuous)


def merge_context(left,right,fields):
    """An exact duplicate contributes once; inconsistent overlap fails closed."""
    out=[];a=b=0
    while a<len(left) or b<len(right):
        if b==len(right) or (a<len(left) and left[a]['utc_week_s']<right[b]['utc_week_s']):
            row=left[a];a+=1
        elif a==len(left) or right[b]['utc_week_s']<left[a]['utc_week_s']:
            row=right[b];b+=1
        else:
            if any(left[a].get(k)!=right[b].get(k) for k in fields):
                raise ValueError('inconsistent overlapping context')
            row=left[a];a+=1;b+=1
        if out and row['utc_week_s']<=out[-1]['utc_week_s']:
            raise ValueError('nonmonotonic merged context')
        out.append(row)
    return out


def run(corpus,output):
    corpus=Path(corpus);records={}
    for line in (corpus/'records.jsonl').read_text().splitlines():
        row=json.loads(line);records[row['task_id']]=row
    inventory=[]
    for record in records.values():
        inspection=json.loads((corpus/record['task_id']/'decoded'/'inspection.json').read_text())
        start,end=absolute_span(inspection)
        key=json.dumps([sorted(inspection['versions']),sorted(inspection['imu']['types']),sorted(inspection['imu']['rate_codes'])])
        inventory.append(dict(record,configuration=key,start_epoch_s=start,end_epoch_s=end))
    pairs,closest=candidates(inventory)
    results=[]
    for pair in pairs:
        left,right=pair['left'],pair['right']
        if left['source_sha256']==right['source_sha256']:
            results.append(dict(left=left['filename'],right=right['filename'],state='byte_identical_duplicate',
                                extends_observed_interval=False));continue
        lp,rp=source_path(corpus,left),source_path(corpus,right)
        overlap=overlap_check(lp,rp)
        result=dict(left=left['filename'],right=right['filename'],overlap=overlap,
                    extends_observed_interval=right['end_epoch_s']>left['end_epoch_s'])
        if not (overlap['exact_overlap_verified'] or overlap['continuous_adjacent_boundary_verified']):
            results.append(dict(result,state='overlap_not_verified'));continue
        context=[]
        for path,record in ((lp,left),(rp,right)):
            nav,gga,zda,cross,_=read_context(path,record['source_sha256'])
            timing=timing_check(zda,cross)
            if not timing['accepted']:raise ValueError('unverified context timing')
            context.append(mapped_context(nav,gga,timing))
        nav_fields=['utc_week_s','time_types','alignment_status']+list(ap.NAV_FIELDS)
        gps_fields=['utc_week_s','latitude_deg','longitude_deg','fix_quality','orthometric_height_m','geoid_separation_m']
        try:
            navigation=merge_context(context[0][0],context[1][0],nav_fields)
            fixes=merge_context(context[0][1],context[1][1],gps_fields)
            screen=screen_context(navigation,fixes)
            result.update(state='verified_union',union_screen=screen,
                          unique_navigation_samples=len(navigation),unique_gps_fixes=len(fixes),
                          gained_observed_tail_seconds=max(0,right['end_epoch_s']-left['end_epoch_s']),
                          gyro_samples_not_exported=True)
        except ValueError as error:result.update(state='context_overlap_not_verified',reason=str(error))
        results.append(result)
    report=dict(files= len(inventory),configurations=len({r['configuration'] for r in inventory}),
                pairs_with_overlap_or_near_adjacency=len(pairs),pair_checks=results,
                closest_separated_pairs=[dict(left=p['left']['filename'],right=p['right']['filename'],gap_s=p['gap_s']) for p in closest],
                original_corpus_modified=False,interpolation_or_gap_repair=False,
                source_sha256={str(p):il.sha256(p) for p in (Path(__file__),Path(ap.__file__),Path(il.__file__))})
    atomic_json(output,report)
    return report


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',type=Path,default=Path('data/ilvis0-ready'))
    parser.add_argument('--output',type=Path,default=Path('docs/ilvis0-followup-20261007/file-continuity.json'))
    args=parser.parse_args();report=run(args.corpus,args.output)
    print(json.dumps({k:v for k,v in report.items() if k not in ('closest_separated_pairs','source_sha256')},indent=2))
