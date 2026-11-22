# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only eight-window internal consistency audit of opened ESA flight 187."""

import hashlib
import json
from pathlib import Path

VERSION='esa-full-receiver-consistency-v1'
PLAN='docs/prediction-observed-development/FULL_RECEIVER_CONSISTENCY_PLAN.md'
INVENTORY='docs/external-imu-data/esa-gnss-report.json'
SOURCE='data/external-imu-survey-20261018/esa-sample/187_air1_ppp_2Hz_final.txt'


def _sizes(count):
    if type(count) is not int or count<8*16:
        raise ValueError('eight complete receiver windows of at least 16 reports required')
    whole,extra=divmod(count,8)
    return [whole+(i<extra) for i in range(8)]


def windows(rows):
    samples=list(rows);sizes=_sizes(len(samples))
    if any(samples[i]['time_s']>=samples[i+1]['time_s'] or
           samples[i]['sequence']>=samples[i+1]['sequence']
           for i in range(len(samples)-1)):
        raise ValueError('strictly ordered receiver reports required')
    result=[];start=0
    for size in sizes:
        result.append(samples[start:start+size]);start+=size
    return result


def _window_summary(rows,index):
    import numpy as np
    from .esa_gnss_covariance_audit import audit_training
    detail=audit_training(rows)
    speed=np.asarray([[r['north_mps'],r['east_mps']] for r in rows],float)
    latitude=np.asarray([r['latitude_deg'] for r in rows],float)
    height=np.asarray([r['height_m'] for r in rows],float)
    return dict(window=index,reports=len(rows),first_sequence=rows[0]['sequence'],
        last_sequence=rows[-1]['sequence'],first_time_s=rows[0]['time_s'],
        last_time_s=rows[-1]['time_s'],
        duration_s=rows[-1]['time_s']-rows[0]['time_s'],
        latitude_range_deg=[float(np.min(latitude)),float(np.max(latitude))],
        height_median_m=float(np.median(height)),
        ground_speed_median_mps=float(np.median(np.linalg.norm(speed,axis=1))),
        position_sd_median_m=detail['position_diagonal_root_median'],
        velocity_sd_median_mps=detail['velocity_diagonal_root_median'],
        position_negative_eigenvalue_epochs=detail['position_negative_eigenvalue_epochs'],
        velocity_negative_eigenvalue_epochs=detail['velocity_negative_eigenvalue_epochs'],
        internal_contrast_rms_mps=detail['contrast_rms_mps'],
        internal_contrast_lag_correlations=detail['contrast_lag_correlations'])


def summarize(rows):
    groups=windows(rows)
    return dict(version=VERSION,reports=sum(map(len,groups)),
        windows=[_window_summary(group,i+1) for i,group in enumerate(groups)],
        uses_imu=False,uses_model_fits=False,protected_group_reads=0,
        empirical_position_coverage_calibrated=False,
        source_specific_aircraft_error_law_qualified=False,
        scientific_decision='abstain')


def build(root):
    from .airquantumgrav_receiver import records
    root=Path(root).resolve()
    inventory_path=root/INVENTORY;source=root/SOURCE
    inventory=json.loads(inventory_path.read_bytes())
    if (inventory.get('source_file')!=source.name
            or type(inventory.get('epochs')) is not int):
        raise ValueError('documented opened ESA receiver source required')
    source_hash=hashlib.sha256()
    with source.open('rb') as stream:
        while chunk:=stream.read(1024*1024):source_hash.update(chunk)
    if source_hash.hexdigest()!=inventory['sha256']:
        raise ValueError('receiver source differs from published inventory')
    sizes=_sizes(inventory['epochs']);remaining=iter(sizes)
    size=next(remaining);group=[];summaries=[];count=0;previous=None
    with source.open() as stream:
        for row in records(stream):
            if previous is not None and (row['time_s']<=previous['time_s']
                    or row['sequence']<=previous['sequence']):
                raise ValueError('full receiver stream is not strictly ordered')
            previous=row;group.append(row);count+=1
            if len(group)==size:
                summaries.append(_window_summary(group,len(summaries)+1));group=[]
                size=next(remaining,None)
                if size is None and count<inventory['epochs']:
                    raise ValueError('receiver has extra reports beyond inventory')
    if count!=inventory['epochs'] or group or len(summaries)!=8:
        raise ValueError('receiver report count differs from published inventory')
    return dict(version=VERSION,source_file=SOURCE,source_sha256=inventory['sha256'],
        inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reports=count,windows=summaries,uses_imu=False,uses_model_fits=False,
        protected_group_reads=0,empirical_position_coverage_calibrated=False,
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
    if target.exists():raise ValueError('fresh receiver-only result required')
    value=build(args.root)
    atomic(target,encoded(value))
    print(json.dumps(dict(reports=value['reports'],windows=len(value['windows']),
        uses_imu=value['uses_imu'],coverage_calibrated=value['empirical_position_coverage_calibrated'])))


if __name__=='__main__':main()
