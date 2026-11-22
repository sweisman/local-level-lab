# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare two speed-selected raw iMAR baselines from the opened ESA flight."""

import hashlib
import json
import math
from pathlib import Path

VERSION='esa-second-ground-imar-baseline-v1'
PLAN='docs/prediction-observed-development/SECOND_GROUND_IMU_PLAN.md'
SELECTION='docs/prediction-observed-development/second-ground-interval-result.json'
FIRST_SELECTION='docs/prediction-observed-development/ground-receiver-control-result.json'
FIRST_RAW='docs/prediction-observed-development/ground-imu-rate-result.json'
INVENTORY='docs/external-imu-data/esa-sample-report.json'
SOURCE='data/external-imu-survey-20261018/esa-sample/187_rqh01.txt'


def compare_vectors(first,second):
    if (len(first)!=3 or len(second)!=3 or
            not all(math.isfinite(v) for v in (*first,*second))):
        raise ValueError('two complete finite instrument-axis vectors required')
    difference=[b-a for a,b in zip(first,second)]
    first_norm=math.sqrt(sum(v*v for v in first))
    second_norm=math.sqrt(sum(v*v for v in second))
    return dict(first_magnitude_deg_per_hour=first_norm,
        second_magnitude_deg_per_hour=second_norm,
        magnitude_difference_deg_per_hour=second_norm-first_norm,
        component_difference_deg_per_hour=difference,
        vector_difference_magnitude_deg_per_hour=math.sqrt(
            sum(v*v for v in difference)))


def build(root):
    from .airquantumgrav import records
    from .esa_ground_imu_rate import coverage_overlap,summarize_rows
    root=Path(root).resolve();source=root/SOURCE
    inventory_path=root/INVENTORY;selection_path=root/SELECTION
    first_selection_path=root/FIRST_SELECTION;first_raw_path=root/FIRST_RAW
    inventory=json.loads(inventory_path.read_bytes())
    selected=json.loads(selection_path.read_bytes())
    first_selection=json.loads(first_selection_path.read_bytes())
    first_raw=json.loads(first_raw_path.read_bytes())
    if (inventory.get('source_file')!=source.name
            or inventory.get('records')!=9168819
            or selected.get('selected_index_range')!=[45253,48943]
            or selected.get('uses_imu') is not False
            or selected.get('first_control_sha256')!=hashlib.sha256(
                first_selection_path.read_bytes()).hexdigest()
            or first_raw.get('source_sha256')!=inventory.get('source_sha256')
            or first_raw.get('selection_sha256')!=hashlib.sha256(
                first_selection_path.read_bytes()).hexdigest()):
        raise ValueError('exact two receiver-selected development controls required')
    sha=hashlib.sha256()
    with source.open('rb') as stream:
        while chunk:=stream.read(1024*1024):sha.update(chunk)
    if sha.hexdigest()!=inventory['source_sha256']:
        raise ValueError('original iMAR source hash changed')
    second=selected['result']
    first,last=coverage_overlap(second['first_time_s'],second['last_time_s'],
        inventory['first_gps_sow_s'],inventory['last_gps_sow_s'])
    with source.open('rb') as stream:
        raw=summarize_rows(records(stream),first=first,last=last)
    comparison=compare_vectors(
        first_raw['raw_imu']['mean_rate_xyz_deg_per_hour'],
        raw['mean_rate_xyz_deg_per_hour'])
    return dict(version=VERSION,source_file=SOURCE,
        source_sha256=inventory['source_sha256'],
        inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        first_selection_sha256=hashlib.sha256(first_selection_path.read_bytes()).hexdigest(),
        second_selection_sha256=hashlib.sha256(selection_path.read_bytes()).hexdigest(),
        first_raw_sha256=hashlib.sha256(first_raw_path.read_bytes()).hexdigest(),
        parser_sha256=hashlib.sha256(Path(__file__).with_name('airquantumgrav.py').read_bytes()).hexdigest(),
        aggregator_sha256=hashlib.sha256(Path(__file__).with_name('esa_ground_imu_rate.py').read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        second_receiver_time_s=[second['first_time_s'],second['last_time_s']],
        second_imu_time_s=[first,last],
        latitude_difference_deg=second['latitude_center_deg']-
                                first_selection['stability']['latitude_center_deg'],
        first_mean_rate_xyz_deg_per_hour=first_raw['raw_imu']['mean_rate_xyz_deg_per_hour'],
        second_raw_imu=raw,comparison=comparison,
        same_aircraft_heading_established=False,sensor_bias_estimated=False,
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
    if target.exists():raise ValueError('fresh second raw baseline required')
    value=build(args.root)
    atomic(target,encoded(value))
    raw=value['second_raw_imu']
    print(json.dumps(dict(samples=raw['samples'],
        mean_rate_xyz_deg_per_hour=raw['mean_rate_xyz_deg_per_hour'],
        mean_rate_magnitude_deg_per_hour=raw['mean_rate_magnitude_deg_per_hour'],
        magnitude_difference_deg_per_hour=value['comparison']['magnitude_difference_deg_per_hour'])))


if __name__=='__main__':main()
