# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-pattern nominal geometry controls; no simulated IMU, fits or envelope search."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'analysis'), str(ROOT / 'analysis/tests')]

import numpy as np
from lll import models
from lll.calib import RAD2DPH
from lll.design_geometry import geometry_kinematics, geometry_problem
from lll.inference import science_information
from lll.maneuvers import maneuver_mask, turn_motion_check
from lll.policy import heading_diversity
from lll.research_design import implementation_hash, realize, validate_turn_schedule

PATTERNS = {
    'original-three':[25., 50., 85.],
    'distributed-six':[10., 30., 50., 70., 90., 110.],
    'middle-ten-minute-six':[25., 35., 45., 55., 65., 75.],
    'two-ten-minute-blocks':[15., 25., 35., 85., 95., 105.],
    'early-ten-minute-six':[5., 15., 25., 35., 45., 55.],
    'late-ten-minute-six':[55., 65., 75., 85., 95., 105.],
}


def review():
    started = time.monotonic()
    path = ROOT / 'docs/extended-airline-pilot-20261006/plan.json'
    plan = json.loads(path.read_text())
    config = plan['manifest']['config']
    design = realize(config['seed'], config['scenarios'][0], geometry='observed',
                     trajectory_input=config['trajectory_input'], turn_schedule=config['turn_schedule'])
    kin, duration = geometry_kinematics(design)
    mask = maneuver_mask(kin, buffer_s=120.)
    cases = []
    for name, schedule in PATTERNS.items():
        validate_turn_schedule(schedule, duration / 60)
        checks = [dict(minute=m, **turn_motion_check(mask, m * 60 - 1., m * 60 + 25.)) for m in schedule]
        result = dict(name=name, schedule_minutes=schedule, turn_checks=checks,
                      all_turns_safe=all(c['safe'] for c in checks))
        if not result['all_turns_safe']:
            cases.append({**result, 'state':'blocked by buffered aircraft-motion check'}); continue
        candidates = []
        for crab in ('wind','wind_tas'):
            problem = geometry_problem(design, schedule, crab, kin=(kin, duration))
            reports = {}
            for anchor, coefficients in models.EXPECTED_K.items():
                z = np.zeros(problem.npar); z[:3] = coefficients
                _, J = problem.prediction(z, True)
                J, weights = problem.observation_information(z, J, np.full(len(problem.y), (RAD2DPH / 6.) ** 2))
                reports[anchor] = science_information(J, weights)['report']
            candidate = dict(crab_model=crab, screened_minutes=float(problem.bins['dt'].sum() / 60),
                heading_diversity=heading_diversity(problem.bins), anchors=reports,
                worst_pre_cutoff_retention={pair:min(r['model_contrast_information'][pair]['pre_cutoff_retained_fraction']
                    for r in reports.values()) for pair in next(iter(reports.values()))['model_contrast_information']},
                all_nominal_contrasts_estimable=all(v['estimable'] for r in reports.values()
                                                   for v in r['model_contrast_information'].values()))
            candidates.append(candidate)
        cases.append({**result, 'state':'nominal geometry evaluated', 'candidates':candidates})
    return dict(scope='six fixed schedule controls on unchanged assumed route; nominal anchors only',
        implementation_hash=implementation_hash(), input_plan_implementation_hash=plan['manifest']['implementation_hash'],
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_sha256={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()},
        cases=cases, elapsed_s=time.monotonic() - started, authorized_additional_attempts=0,
        limitations=['Same dynamic bias, wind models and acceptance cutoff; no nuisance removal or weaker gate.',
            'Analytic motion/bins and known assumed mount; differs from saved full preprocessing.',
            'Zero nuisance state and zero forward offset at three anchors, fixed 6 dph noise with physical speed rows.',
            'No nuisance envelope, actual forward-reference recovery, noisy IMU/GNSS, bootstrap or power.',
            'These six patterns are diagnostic controls, not optimizer output or a recommended collection protocol.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open('x') as out: out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps([dict(name=c['name'], safe=c['all_turns_safe'],
        candidates=[{k:v[k] for k in ('crab_model','screened_minutes','worst_pre_cutoff_retention',
                                      'all_nominal_contrasts_estimable')} for v in c.get('candidates',[])]) for c in result['cases']]))
