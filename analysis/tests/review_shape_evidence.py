# SPDX-License-Identifier: AGPL-3.0-or-later
"""Derive experimental shape preferences from preserved pair decisions; never refit."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))

from lll.pairwise import SHAPE_METHOD, shape_evidence
from lll.research_design import implementation_hash


def review(paths):
    campaigns=[]
    for path in paths:
        with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as stream:
            campaign=json.load(stream)
        if campaign.get('partition')!='development' or not campaign.get('manifest_hash'):
            raise ValueError('requires preserved, frozen development records')
        counts=defaultdict(lambda:dict(attempted=0,correct=0,incorrect=0,abstain=0,conflict=0,
            shape_without_three_model_winner=0,calibrated_pairwise_inputs=0))
        for row in campaign['records']:
            expected='disc' if row['truth']=='flat_still' else 'globe' if row['truth'] in ('sphere_rotating','sphere_still') else None
            if expected is None: raise ValueError('unknown generating model')
            shape=shape_evidence(row.get('pairwise') or {})
            count=counts[(row['truth'],row['scenario'])]; count['attempted']+=1
            count['abstain' if shape['preferred_family'] is None else 'correct' if shape['preferred_family']==expected else 'incorrect']+=1
            count['conflict']+=int(shape['conflicting_preferences'])
            count['shape_without_three_model_winner']+=int(shape['status']=='decision' and row.get('pairwise_three_model_winner') is None)
            count['calibrated_pairwise_inputs']+=int(shape['pairwise_thresholds_calibrated'])
        cells=[dict(truth=truth,scenario=scenario,**counts[truth,scenario]) for truth,scenario in sorted(counts)]
        totals={k:sum(c[k] for c in cells) for k in next(iter(counts.values()))}
        campaigns.append(dict(input_path=str(path.relative_to(ROOT)),input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            original_implementation_hash=campaign['implementation_hash'],original_manifest_hash=campaign['manifest_hash'],
            cells=cells,totals=totals))
    return dict(method=SHAPE_METHOD,implementation_hash=implementation_hash(),campaigns=campaigns,
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        additional_flight_attempts=0,error_rate_validated=False,
        limitations=['Uses stored pairwise eligibility, endpoint decisions and diagnostic thresholds; no new fits, gate repair or calibration.',
            'Historical synthetic routes and nuisance scenarios differ from current observed-airline profiles.',
            'Counts are descriptive; seeds shared across truths/scenarios are not independent null draws.',
            'The composite shape decision needs its own preregistered error budget and independent validation.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    paths=[ROOT/'docs'/f'development-1000-{day}'/'campaign.json.gz' for day in ('20261005','20261006')]
    result=review(paths)
    with args.output.open('x') as stream: stream.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps([dict(input=c['input_path'],**c['totals']) for c in result['campaigns']]))
