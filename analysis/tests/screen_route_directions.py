# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed nominal direction/turn controls on documented paths; no flights or envelope search."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'analysis'),str(ROOT/'analysis/tests')]

import numpy as np
from lll import models
from lll.calib import RAD2DPH
from lll.design_geometry import geometry_kinematics,geometry_problem
from lll.inference import science_information
from lll.maneuvers import maneuver_mask,turn_motion_check
from lll.pairwise import GLOBE_DISC_PAIRS
from lll.policy import CANDIDATE_POLICY,heading_diversity
from lll.research_design import implementation_hash,realize,validate_turn_schedule
from lll.trajectory import smooth_track_spec


def reverse_motion(kin):
    """Counterfactual traversal of the same path backwards, never a measured return flight."""
    t=np.asarray(kin['t'])
    if len(t)<2 or not np.allclose(np.diff(t),1.): raise ValueError('requires one-second kinematics')
    result={k:np.asarray(v)[::-1].copy() for k,v in kin.items()}
    result['t']=t.copy()
    for key in ('v_n','v_e','vz','psi_dot'): result[key]*=-1.
    result['psi']=(result['psi']+np.pi+np.pi)%(2*np.pi)-np.pi
    return result


def review():
    start=time.monotonic(); inputs={}; routes=[]
    def read(relative):
        data=(ROOT/relative).read_bytes(); inputs[str(relative)]=hashlib.sha256(data).hexdigest()
        return json.loads(data)
    core=Path('docs/core-pipeline-20261006')
    proposal=read(core/'proposal.json')
    for item in proposal['config']['replay_inputs']:
        if item['mode']!='simulated_high_rate': continue
        relative=Path(item['path'])
        if relative.parent!=Path('trajectories') or relative.suffix!='.json': raise ValueError('undocumented trajectory path')
        spec=smooth_track_spec(read(core/relative))
        routes.append((spec['track_id'],spec,False))
    plan=read(Path('docs/extended-airline-pilot-20261006/plan.json'))
    spec=plan['manifest']['config']['trajectory_input']
    routes.extend([('extended-AUH-ORD',spec,False),('reversed-extended-path',spec,True)])
    cases=[]
    for name,spec,reversed_path in routes:
        design=realize(600902,'wind+bias_mixed',geometry='observed',trajectory_input=spec,turn_schedule=[])
        kin,duration=geometry_kinematics(design)
        if reversed_path: kin=reverse_motion(kin)
        mask=maneuver_mask(kin,buffer_s=120.)
        patterns={'no-turn':[], 'three-fixed':[20.,40.,60.] if duration<6000 else [25.,50.,85.],
                  'six-distributed':np.linspace(10.,duration/60.-10.,6).tolist()}
        for pattern,schedule in patterns.items():
            validate_turn_schedule(schedule,duration/60.)
            checks=[dict(minute=m,**turn_motion_check(mask,m*60.-1.,m*60.+25.)) for m in schedule]
            case=dict(route=name,trajectory_hash=spec['trajectory_hash'],counterfactual_reversed_path=reversed_path,
                pattern=pattern,schedule_minutes=schedule,turn_checks=checks,
                all_turns_safe=all(c['safe'] for c in checks),candidates=[])
            if not case['all_turns_safe']:
                cases.append({**case,'state':'blocked by motion mask'}); continue
            for crab in ('wind','wind_tas'):
                try:
                    p=geometry_problem(design,schedule,crab,kin=(kin,duration)); reports={}
                    for anchor,coefficients in models.EXPECTED_K.items():
                        z=np.zeros(p.npar); z[:3]=coefficients
                        _,J=p.prediction(z,True)
                        J,w=p.observation_information(z,J,np.full(len(p.y),(RAD2DPH/6.)**2))
                        reports[anchor]=science_information(J,w)['report']
                    fractions={pair:min(r['model_contrast_information'][pair]['pre_cutoff_retained_fraction']
                        for r in reports.values()) for pair in CANDIDATE_POLICY['contrasts']}
                    passing={pair:f>=CANDIDATE_POLICY['retention_threshold'] for pair,f in fractions.items()}
                    case['candidates'].append(dict(crab_model=crab,screened_minutes=float(p.bins['dt'].sum()/60.),
                        heading_diversity=heading_diversity(p.bins),mean_east_velocity_mps=float(np.mean(p.bins['v_e'])),
                        worst_nominal_pair_retention=fractions,nominal_pair_retention_pass=passing,
                        both_shape_retention_pass=all(passing[pair] for pair in GLOBE_DISC_PAIRS),anchors=reports))
                except (ValueError,np.linalg.LinAlgError) as exc:
                    case['candidates'].append(dict(crab_model=crab,failure=str(exc)))
            cases.append({**case,'state':'nominal controls evaluated'})
    return dict(scope='fixed direction/turn controls; assumed geometry and nominal tangents only',cases=cases,
        implementation_hash=implementation_hash(),input_sha256=inputs,
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),elapsed_s=time.monotonic()-start,
        additional_flight_attempts=0,error_rate_validated=False,
        limitations=['Five previously prepared 75-minute paths plus the 120-minute pilot path; not a search of all windows.',
            'The reversed path is counterfactual, not another observed flight; different directions are not independent trials.',
            'Zero wind/angle at three science anchors, physical TAS250, fixed6dph; no complete nuisance envelope.',
            'Dynamic bias and all other nuisance families remain; motion checks can block turns.',
            'Retention passes alone are not qualification: duration, headings, full preprocessing and recovered axes still matter.',
            'No noisy sensor replay, nonlinear analysis, bootstrap, power, threshold estimation or protocol recommendation.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    result=review()
    with args.output.open('x') as out: out.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(cases=len(result['cases']),safe=sum(c['all_turns_safe'] for c in result['cases']),
        candidates=sum(len(c['candidates']) for c in result['cases']),elapsed_s=result['elapsed_s'],
        shape_retention_passes=[dict(route=c['route'],pattern=c['pattern'],crab_model=v['crab_model'])
            for c in result['cases'] for v in c['candidates'] if v.get('both_shape_retention_pass')])))
