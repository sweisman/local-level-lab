# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conservative metadata-only split groups; not a physical-identity inference."""
from collections import defaultdict
from datetime import datetime,timedelta,timezone
import hashlib
import itertools


def _time(value):
    value=datetime.fromisoformat(value.replace('Z','+00:00'))
    if value.tzinfo is None:raise ValueError('timezone-qualified UTC interval required')
    return value.astimezone(timezone.utc)


def build(nasa,pairs,esa,policy):
    development=set(policy['development_files']);confirmation=set(policy['confirmation_files'])
    if development & confirmation:raise ValueError('development/confirmation policy overlap')
    records=[];intervals={};days={}
    for row in nasa:
        identity='ilvis0:'+row['segment_id'];start,end=_time(row['start_utc']),_time(row['end_utc'])
        if end<=start:raise ValueError('positive UTC interval required')
        day=start.date();last=(end-timedelta(microseconds=1)).date();covered=[]
        while day<=last:covered.append(day.isoformat());day+=timedelta(days=1)
        days[identity]=covered;intervals[identity]=(start,end)
        records.append(dict(record_id=identity,archive='ilvis0',filename=row['filename'],
            source_sha256=row['source_sha256'],start_utc=row['start_utc'],end_utc=row['end_utc'],
            imu_type=row.get('imu_type',''),mounting_configuration=row.get('mounting_epoch',''),
            shared_leg_id=row.get('shared_leg_id',''),role='retrospective_development',
            physical_instrument_id=None,installation_id=None,reported_flight_labels=[]))
    for row in esa:
        name=row['filename'];identity='esa:'+name
        if name not in development|confirmation:raise ValueError('unassigned ESA source: '+name)
        # Validate metadata dates without interpreting flight labels as physical identity.
        day=datetime.strptime(row['date'],'%Y-%m-%d').date().isoformat();days[identity]=[day]
        records.append(dict(record_id=identity,archive='esa',filename=name,
            source_sha256=row.get('local_sha256',''),date=day,
            reported_flight_labels=sorted(set(filter(None,row.get('flight_ids','').split(';')))),
            role='development' if name in development else 'protected_confirmation',
            physical_instrument_id=None,installation_id=None))
    records=sorted(records,key=lambda r:r['record_id']);by_id={r['record_id']:r for r in records}
    if len(by_id)!=len(records):raise ValueError('duplicate record identity')
    parent={identity:identity for identity in by_id};relations=[]
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def connect(a,b,kind,confidence):
        if a not in parent or b not in parent:raise ValueError('unknown relation endpoint')
        a,b=sorted((a,b));relations.append(dict(left=a,right=b,kind=kind,confidence=confidence))
        x,y=root(a),root(b)
        if x!=y:parent[max(x,y)]=min(x,y)
    for left,right in itertools.combinations(records,2):
        a,b=left['record_id'],right['record_id']
        if left['archive']!=right['archive']:continue
        if set(days[a]) & set(days[b]):connect(a,b,'same_utc_day','conservative grouping')
        if left['source_sha256'] and left['source_sha256']==right['source_sha256']:
            connect(a,b,'same_source_hash','recorded byte identity')
        if a in intervals and b in intervals and max(intervals[a][0],intervals[b][0])<min(intervals[a][1],intervals[b][1]):
            connect(a,b,'utc_overlap','recorded time overlap')
        if set(left['reported_flight_labels']) & set(right['reported_flight_labels']):
            connect(a,b,'shared_reported_flight_label','reported metadata')
    for row in pairs:
        a,b='ilvis0:'+row['left_segment_id'],'ilvis0:'+row['right_segment_id']
        if a not in by_id or b not in by_id:raise ValueError('unknown pair endpoint')
        if str(row.get('same_track_candidate','')).lower() in ('true','1'):
            connect(a,b,'candidate_shared_leg','candidate')
    members=defaultdict(list)
    for row in records:members[root(row['record_id'])].append(row)
    groups=[]
    for values in members.values():
        ids=sorted(v['record_id'] for v in values);roles={v['role'] for v in values}
        if 'development' in roles and 'protected_confirmation' in roles:
            raise ValueError('development and confirmation observations share a conservative group')
        identity=values[0]['archive']+'-'+hashlib.sha256('\n'.join(ids).encode()).hexdigest()[:16]
        group=dict(group_id=identity,archive=values[0]['archive'],role=next(iter(roles)),record_ids=ids,
            utc_dates=sorted({day for key in ids for day in days[key]}),
            reported_flight_labels=sorted({label for v in values for label in v['reported_flight_labels']}),
            identity_status='conservative split group; physical flight/installation not verified')
        groups.append(group)
        for value in values:value['group_id']=identity
    return dict(version='evidence-split-groups-v1',policy_version=policy['version'],records=records,
        groups=sorted(groups,key=lambda g:g['group_id']),
        relations=sorted(relations,key=lambda e:(e['left'],e['right'],e['kind'])),
        group_count_is_independent_flight_count=False)


def require_development(ledger,group_ids):
    """Guard for future development workers; does not open or authorize originals."""
    by_id={group['group_id']:group for group in ledger['groups']}
    for identity in group_ids:
        if identity not in by_id or by_id[identity]['role'] not in ('development','retrospective_development'):
            raise ValueError('group is not assigned to development: '+identity)
