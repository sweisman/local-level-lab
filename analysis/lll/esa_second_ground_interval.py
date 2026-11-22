# SPDX-License-Identifier: AGPL-3.0-or-later
"""Find a second receiver-speed-selected ground interval without IMU input."""

import hashlib
import json
from pathlib import Path

VERSION='esa-second-ground-interval-v1'
PLAN='docs/prediction-observed-development/SECOND_GROUND_INTERVAL_PLAN.md'
FIRST='docs/prediction-observed-development/ground-receiver-control-result.json'
INVENTORY='docs/external-imu-data/esa-gnss-report.json'
SOURCE='data/external-imu-survey-20261018/esa-sample/187_air1_ppp_2Hz_final.txt'


def select_second(rows,*,first_stop,min_reports=600):
    from .esa_ground_receiver_control import select_run
    samples=list(rows)
    if (type(first_stop) is not int or first_stop<1 or first_stop>=len(samples)):
        raise ValueError('prior selected run must precede remaining reports')
    try:
        start,stop=select_run(samples[first_stop:],min_reports=min_reports)
    except ValueError as error:
        if str(error)=='no qualifying ground run in first fixed window':
            return None
        raise
    return first_stop+start,first_stop+stop


def build(root):
    from .airquantumgrav_receiver import records
    from .esa_ground_receiver_control import position_stability
    root=Path(root).resolve();source=root/SOURCE
    first_path=root/FIRST;inventory_path=root/INVENTORY
    first=json.loads(first_path.read_bytes())
    inventory=json.loads(inventory_path.read_bytes())
    if (inventory.get('source_file')!=source.name
            or inventory.get('epochs')!=64080
            or first.get('source_sha256')!=inventory.get('sha256')
            or first.get('selected_index_range')!=[0,7815]
            or first.get('selection',{}).get('uses_position_for_selection') is not False):
        raise ValueError('exact first speed-selected receiver control required')
    sha=hashlib.sha256()
    with source.open('rb') as stream:
        while chunk:=stream.read(1024*1024):sha.update(chunk)
    if sha.hexdigest()!=inventory['sha256']:
        raise ValueError('original receiver source hash changed')
    with source.open() as stream:
        rows=list(records(stream))
    if len(rows)!=inventory['epochs']:
        raise ValueError('full receiver count differs from inventory')
    selected=select_second(rows,first_stop=7815)
    result=None if selected is None else position_stability(rows[selected[0]:selected[1]])
    return dict(version=VERSION,source_file=SOURCE,source_sha256=inventory['sha256'],
        inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        first_control_sha256=hashlib.sha256(first_path.read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        searched_index_range=[7815,len(rows)],
        selected_index_range=None if selected is None else list(selected),
        result=result,uses_imu=False,uses_model_fits=False,protected_group_reads=0,
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
    if target.exists():raise ValueError('fresh later ground result required')
    value=build(args.root)
    atomic(target,encoded(value))
    print(json.dumps(dict(selected_index_range=value['selected_index_range'],
        selected_reports=None if value['result'] is None else value['result']['reports'])))


if __name__=='__main__':main()
