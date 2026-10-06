# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded checks for nuisance-envelope counterexamples to one promising nominal control."""
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
from lll.design_envelope import envelope_assumptions, nuisance_states
from lll.design_geometry import geometry_kinematics, geometry_problem
from lll.inference import science_information
from lll.maneuvers import maneuver_mask, turn_motion_check
from lll.pairwise import GLOBE_DISC_PAIRS
from lll.policy import CANDIDATE_POLICY, heading_diversity
from lll.research_design import implementation_hash, realize
from screen_route_directions import reverse_motion


def review():
    started = time.monotonic()
    path = ROOT / 'docs/extended-airline-pilot-20261006/plan.json'
    raw = path.read_bytes()
    config = json.loads(raw)['manifest']['config']
    design = realize(600902, 'wind+bias_mixed', geometry='observed',
                     trajectory_input=config['trajectory_input'], turn_schedule=[])
    kin, duration = geometry_kinematics(design)
    kin = reverse_motion(kin)
    schedule = [10., 30., 50., 70., 90., 110.]
    mask = maneuver_mask(kin, buffer_s=120.)
    checks = [dict(minute=m, **turn_motion_check(mask, m*60.-1., m*60.+25.)) for m in schedule]
    if not all(c['safe'] for c in checks):
        raise ValueError('control no longer passes turn-motion checks')
    problem = geometry_problem(design, schedule, 'wind_tas', kin=(kin, duration))
    # Registered TAS-reference states only: an exact subset of the existing finite envelope.
    # Nominal mount epoch, noise6dph and offsets0/+3sigma/-3sigma are registered states too.
    states = [(label, values) for label, values in nuisance_states(problem)
              if np.allclose(values[2::3], 0., atol=1e-14, rtol=0.)]
    states.sort(key=lambda item: np.linalg.norm(item[1]))
    tested = []
    counterexample = None
    for label, values in states:
        for forward in (0., 3*problem.forward_sigma, -3*problem.forward_sigma):
            for anchor, coefficients in models.EXPECTED_K.items():
                z = np.zeros(problem.npar)
                z[:3] = coefficients
                z[problem.p:problem.p+problem.nc] = values
                z[-1] = forward
                _, jac = problem.prediction(z, True)
                jac, weights = problem.observation_information(z, jac,
                    np.full(len(problem.y), (RAD2DPH/6.)**2))
                report = science_information(jac, weights)['report']
                fractions = {pair: report['model_contrast_information'][pair]['pre_cutoff_retained_fraction']
                             for pair in GLOBE_DISC_PAIRS}
                state = dict(nuisance_state=label, nuisance_values=values.tolist(),
                             forward_offset_deg=float(np.degrees(forward)), anchor=anchor,
                             shape_retention=fractions, fitted_or_simulated_gyro=False)
                tested.append(state)
                if min(fractions.values()) < CANDIDATE_POLICY['retention_threshold']:
                    counterexample = state
                    break
            if counterexample is not None or len(tested) >= 30:
                break
        if counterexample is not None or len(tested) >= 30:
            break
    return dict(scope='bounded registered-state counterexample check, not full envelope or flight replay',
                state='nominal_pass_disproved_in_registered_subset' if counterexample else 'inconclusive_bounded_check',
                route='counterfactual reversed extended AUH-ORD path', schedule_minutes=schedule,
                counterfactual_reversed_path=True, turn_checks=checks,
                screened_minutes=float(problem.bins['dt'].sum()/60.), heading_diversity=heading_diversity(problem.bins),
                envelope_assumptions=envelope_assumptions(problem.settings),
                retention_threshold=CANDIDATE_POLICY['retention_threshold'],
                tested_states=tested, counterexample=counterexample, svd_evaluations=len(tested),
                maximum_svd_evaluations=30, additional_flight_attempts=0,
                implementation_hash=implementation_hash(),
                input_sha256={str(path.relative_to(ROOT)): hashlib.sha256(raw).hexdigest()},
                helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                elapsed_s=time.monotonic()-started,
                limitations=['A failing registered state disproves a universal pass; absence of failure in this subset proves nothing.',
                             'Assumed geometry and known axes; no forward-axis recovery or complete preprocessing.',
                             'Counterfactual reversed path is not an actual observed eastbound flight.',
                             'Existing physical-wind/TAS envelope and conditional speed assumptions remain provisional.',
                             'No nuisance directions removed, eligibility thresholds changed, fit, power or calibration performed.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review()
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('state', 'svd_evaluations', 'counterexample', 'elapsed_s')}))
