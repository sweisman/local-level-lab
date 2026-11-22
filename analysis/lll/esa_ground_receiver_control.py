# SPDX-License-Identifier: AGPL-3.0-or-later
"""Velocity-selected relative PPP stability on opened ESA ground reports."""

import hashlib
import json
from pathlib import Path

VERSION='esa-ground-receiver-control-v1'
PLAN='docs/prediction-observed-development/GROUND_RECEIVER_CONTROL_PLAN.md'
INVENTORY='docs/external-imu-data/esa-gnss-report.json'
FULL_AUDIT='docs/prediction-observed-development/full-receiver-consistency-result.json'
SOURCE='data/external-imu-survey-20261018/esa-sample/187_air1_ppp_2Hz_final.txt'
FIRST_WINDOW=8010


def select_run(rows,*,min_reports=600):
    import math
    samples=list(rows)
    if (type(min_reports) is not int or min_reports<2 or len(samples)<min_reports):
        raise ValueError('enough ordered reports for a ground run required')
    best=(0,0);start=None
    for i,row in enumerate(samples):
        t=row['time_s']
        if i and t<=samples[i-1]['time_s']:
            raise ValueError('strictly increasing receiver time required')
        h=math.hypot(row['north_mps'],row['east_mps'])
        acceptable=(math.isfinite(h) and math.isfinite(row['up_mps'])
                    and h<=.5 and abs(row['up_mps'])<=.2)
        if start is not None and (not acceptable or i and t-samples[i-1]['time_s']>1.):
            if i-start>best[1]-best[0]:best=(start,i)
            start=None
        if acceptable and start is None:start=i
    if start is not None and len(samples)-start>best[1]-best[0]:
        best=(start,len(samples))
    if best[1]-best[0]<min_reports:
        raise ValueError('no qualifying ground run in first fixed window')
    return best


def position_stability(rows,*,block_reports=120):
    import numpy as np
    from .models import WGS84_A,WGS84_E2
    samples=list(rows)
    if (type(block_reports) is not int or block_reports<2
            or len(samples)<block_reports*2):
        raise ValueError('at least two complete position blocks required')
    lat=np.radians([r['latitude_deg'] for r in samples])
    lon=np.unwrap(np.radians([r['longitude_deg'] for r in samples]))
    height=np.asarray([r['height_m'] for r in samples],float)
    speed=np.asarray([[r['north_mps'],r['east_mps'],r['up_mps']]
                      for r in samples],float)
    variances=np.asarray([r['position_variance_m2'] for r in samples],float)
    if (not all(np.all(np.isfinite(x)) for x in (lat,lon,height,speed,variances))
            or variances.shape!=(len(samples),3) or np.any(variances<0)
            or np.any(abs(lat)>=np.pi/2)):
        raise ValueError('finite nonpolar PPP coordinates and variances required')
    center_lat=float(np.median(lat));center_lon=float(np.median(lon))
    center_height=float(np.median(height));q=1-WGS84_E2*np.sin(center_lat)**2
    north=(WGS84_A*(1-WGS84_E2)/q**1.5+center_height)*(lat-center_lat)
    east=(WGS84_A/np.sqrt(q)+center_height)*np.cos(center_lat)*(lon-center_lon)
    position=np.column_stack((north,east,height-center_height))
    block_count=len(samples)//block_reports
    block_means=position[:block_count*block_reports].reshape(block_count,block_reports,3).mean(axis=1)
    horizontal=np.linalg.norm(speed[:,:2],axis=1)
    return dict(reports=len(samples),duration_s=samples[-1]['time_s']-samples[0]['time_s'],
        first_sequence=samples[0]['sequence'],last_sequence=samples[-1]['sequence'],
        first_time_s=samples[0]['time_s'],last_time_s=samples[-1]['time_s'],
        velocity_selected=True,latitude_center_deg=float(np.degrees(center_lat)),
        longitude_center_deg=float(np.degrees(center_lon)),height_center_m=center_height,
        ground_speed_median_mps=float(np.median(horizontal)),
        ground_speed_p95_mps=float(np.quantile(horizontal,.95)),
        absolute_up_speed_p95_mps=float(np.quantile(abs(speed[:,2]),.95)),
        reported_sd_median_neu_m=np.median(np.sqrt(variances),axis=0).tolist(),
        relative_rms_neu_m=np.sqrt(np.mean(position*position,axis=0)).tolist(),
        relative_p95_abs_neu_m=np.quantile(abs(position),.95,axis=0).tolist(),
        one_minute_block_mean_range_neu_m=np.ptp(block_means,axis=0).tolist(),
        first_to_last_displacement_neu_m=(position[-1]-position[0]).tolist(),
        block_reports=block_reports,complete_blocks=block_count,
        empirical_coverage_calibrated=False,absolute_position_known=False)


def build(root):
    from itertools import islice
    from .airquantumgrav_receiver import records
    root=Path(root).resolve();source=root/SOURCE
    inventory_path=root/INVENTORY;full_path=root/FULL_AUDIT
    inventory=json.loads(inventory_path.read_bytes())
    full=json.loads(full_path.read_bytes())
    if (inventory.get('source_file')!=source.name
            or full.get('source_sha256')!=inventory.get('sha256')
            or full.get('reports')!=64080
            or len(full.get('windows',[]))!=8
            or full['windows'][0].get('reports')!=FIRST_WINDOW):
        raise ValueError('exact prior full receiver audit required')
    source_hash=hashlib.sha256()
    with source.open('rb') as stream:
        while chunk:=stream.read(1024*1024):source_hash.update(chunk)
    if source_hash.hexdigest()!=inventory['sha256']:
        raise ValueError('opened ESA GNSS source hash changed')
    with source.open() as stream:
        first=list(islice(records(stream),FIRST_WINDOW))
    if (len(first)!=FIRST_WINDOW
            or first[0]['sequence']!=full['windows'][0]['first_sequence']
            or first[-1]['sequence']!=full['windows'][0]['last_sequence']
            or first[0]['time_s']!=full['windows'][0]['first_time_s']
            or first[-1]['time_s']!=full['windows'][0]['last_time_s']):
        raise ValueError('first receiver window differs from sealed full audit')
    start,stop=select_run(first)
    result=position_stability(first[start:stop])
    return dict(version=VERSION,source_file=SOURCE,source_sha256=inventory['sha256'],
        prior_audit_sha256=hashlib.sha256(full_path.read_bytes()).hexdigest(),
        inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_window_reports=FIRST_WINDOW,selected_index_range=[start,stop],
        selection=dict(max_horizontal_speed_mps=.5,max_abs_vertical_speed_mps=.2,
            max_adjacent_dt_s=1.,minimum_reports=600,longest_run_earliest_tie=True,
            uses_position_for_selection=False),
        stability=result,uses_imu=False,uses_model_fits=False,protected_group_reads=0,
        source_specific_aircraft_error_law_qualified=False,
        scientific_decision='abstain')


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    target=Path(args.output)
    if target.exists():raise ValueError('fresh ground receiver result required')
    value=build(args.root)
    atomic(target,encoded(value))
    print(json.dumps(dict(selected_reports=value['stability']['reports'],
        duration_s=value['stability']['duration_s'],
        relative_rms_neu_m=value['stability']['relative_rms_neu_m'],
        coverage_calibrated=value['stability']['empirical_coverage_calibrated'])))


if __name__=='__main__':main()
