# SPDX-License-Identifier: AGPL-3.0-or-later
"""Unadjusted iMAR gyro rates inside a receiver-selected ground interval."""

import hashlib
import json
import math
from pathlib import Path

VERSION='esa-ground-imar-raw-rate-v1'
PLAN='docs/prediction-observed-development/GROUND_IMU_RATE_PLAN.md'
SELECTION='docs/prediction-observed-development/ground-receiver-control-result.json'
INVENTORY='docs/external-imu-data/esa-sample-report.json'
SOURCE='data/external-imu-survey-20261018/esa-sample/187_rqh01.txt'
DEG_PER_HOUR=180./math.pi*3600.


def coverage_overlap(receiver_first,receiver_last,imu_first,imu_last):
    if (not all(math.isfinite(v) for v in
                (receiver_first,receiver_last,imu_first,imu_last))
            or receiver_first>=receiver_last or imu_first>=imu_last):
        raise ValueError('ordered finite receiver and IMU coverage required')
    first=max(receiver_first,imu_first);last=min(receiver_last,imu_last)
    if last-first<600.:
        raise ValueError('at least ten minutes of receiver-selected IMU overlap required')
    return first,last


def summarize_rows(rows,*,first,last,min_samples=10000):
    if (not math.isfinite(first) or not math.isfinite(last) or first>=last
            or type(min_samples) is not int or min_samples<2):
        raise ValueError('fixed interval and minimum raw sample count required')
    count=0;total=[0.,0.,0.];square=[0.,0.,0.]
    halves=[dict(count=0,total=[0.,0.,0.]) for _ in range(2)]
    bins={};acc_total=0.;acc_square=0.;temp_total=0.
    temp_min=math.inf;temp_max=-math.inf;first_sample=None;last_sample=None
    first_line=None;last_line=None;previous=None;midpoint=(first+last)/2
    for row in rows:
        t=row['gps_time_s']
        if t<first:continue
        if t>last:break
        if previous is not None and (t<=previous or t-previous>1.5/300
                                     or row['gap_above_1p5_nominal_periods']):
            raise ValueError('IMU gap or non-increasing time inside selected interval')
        rate=row['angular_rate_rads'];acc=row['acceleration_mps2']
        temp=row['temperature_c']
        if (len(rate)!=3 or len(acc)!=3 or not all(math.isfinite(x) for x in (*rate,*acc,temp))):
            raise ValueError('complete finite raw channels required')
        if first_sample is None:first_sample=t;first_line=row.get('line_number')
        last_sample=t;last_line=row.get('line_number');previous=t;count+=1
        half=halves[int(t>=midpoint)];half['count']+=1
        minute=int((t-first)//60)
        bin_record=bins.setdefault(minute,dict(count=0,total=[0.,0.,0.]))
        bin_record['count']+=1
        for axis,value in enumerate(rate):
            total[axis]+=value;square[axis]+=value*value
            half['total'][axis]+=value;bin_record['total'][axis]+=value
        norm=math.sqrt(sum(value*value for value in acc))
        acc_total+=norm;acc_square+=norm*norm
        temp_total+=temp;temp_min=min(temp_min,temp);temp_max=max(temp_max,temp)
    if (count<min_samples or first_sample is None or first_sample-first>.01
            or last-last_sample>.01 or not all(half['count'] for half in halves)):
        raise ValueError('complete fixed IMU time support and both halves required')
    mean=[value/count for value in total]
    minutes=[dict(index=i,first_offset_s=i*60,count=bin_record['count'],
                  mean_rate_xyz_deg_per_hour=[DEG_PER_HOUR*v/bin_record['count']
                                              for v in bin_record['total']])
             for i,bin_record in sorted(bins.items())]
    return dict(samples=count,first_sample_time_s=first_sample,
        last_sample_time_s=last_sample,first_line_number=first_line,
        last_line_number=last_line,
        effective_rate_hz=(count-1)/(last_sample-first_sample),
        mean_rate_xyz_deg_per_hour=[DEG_PER_HOUR*v for v in mean],
        mean_rate_magnitude_deg_per_hour=DEG_PER_HOUR*math.sqrt(sum(v*v for v in mean)),
        centered_sample_rms_xyz_deg_per_hour=[
            DEG_PER_HOUR*math.sqrt(max(0.,square[i]/count-mean[i]*mean[i]))
            for i in range(3)],
        half_mean_rate_xyz_deg_per_hour=[[DEG_PER_HOUR*v/half['count']
                                          for v in half['total']] for half in halves],
        half_sample_counts=[half['count'] for half in halves],
        minute_means=minutes,acceleration_norm_mean_mps2=acc_total/count,
        acceleration_norm_rms_deviation_mps2=math.sqrt(
            max(0.,acc_square/count-(acc_total/count)**2)),
        temperature_mean_c=temp_total/count,temperature_range_c=[temp_min,temp_max],
        uses_model_prediction=False,earth_rate_subtracted=False,
        sensor_bias_estimated=False,scientific_decision='abstain')


def build(root):
    from .airquantumgrav import records
    root=Path(root).resolve();source=root/SOURCE
    inventory_path=root/INVENTORY;selection_path=root/SELECTION
    inventory=json.loads(inventory_path.read_bytes())
    selection=json.loads(selection_path.read_bytes())
    if (inventory.get('source_file')!=source.name
            or inventory.get('records')!=9168819
            or selection.get('source_file')!=
                'data/external-imu-survey-20261018/esa-sample/187_air1_ppp_2Hz_final.txt'
            or selection.get('selected_index_range')!=[0,7815]
            or selection.get('selection',{}).get('uses_position_for_selection') is not False
            or selection.get('uses_imu') is not False):
        raise ValueError('exact receiver-selected opened development interval required')
    source_hash=hashlib.sha256()
    with source.open('rb') as stream:
        while chunk:=stream.read(1024*1024):source_hash.update(chunk)
    if source_hash.hexdigest()!=inventory['source_sha256']:
        raise ValueError('original ESA IMU source hash changed')
    first,last=coverage_overlap(selection['stability']['first_time_s'],
        selection['stability']['last_time_s'],inventory['first_gps_sow_s'],
        inventory['last_gps_sow_s'])
    with source.open('rb') as stream:
        result=summarize_rows(records(stream),first=first,last=last)
    return dict(version=VERSION,source_file=SOURCE,
        source_sha256=inventory['source_sha256'],
        inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        selection_sha256=hashlib.sha256(selection_path.read_bytes()).hexdigest(),
        parser_sha256=hashlib.sha256(Path(__file__).with_name('airquantumgrav.py').read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        receiver_selection_time_s=[selection['stability']['first_time_s'],
                                   selection['stability']['last_time_s']],
        imu_overlap_time_s=[first,last],raw_imu=result,
        uses_model_fits=False,protected_group_reads=0,
        background_field_inferred=False,scientific_decision='abstain')


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    target=Path(args.output)
    if target.exists():raise ValueError('fresh raw rate result required')
    value=build(args.root)
    atomic(target,encoded(value))
    raw=value['raw_imu']
    print(json.dumps(dict(samples=raw['samples'],
        mean_rate_xyz_deg_per_hour=raw['mean_rate_xyz_deg_per_hour'],
        mean_rate_magnitude_deg_per_hour=raw['mean_rate_magnitude_deg_per_hour'])))


if __name__=='__main__':main()
