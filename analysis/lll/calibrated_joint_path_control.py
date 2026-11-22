# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite independent-noise controls for the common-scale joint score."""

import argparse
from pathlib import Path

import numpy as np

from .calibrated_joint_path import prepare, score
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .state_space_covariance import LinearInnovations
from .studies.artifacts import digest, encoded
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'CALIBRATED_JOINT_SCORE_PLAN.md'
FREEZE = FOLDER+'calibrated-joint-score-freeze.json'
RESULT = FOLDER+'calibrated-joint-score-result.json'
CUT, LATER = 12, 8
COUNT = 1024
CASES = (('nominal', 20261118031, 1., 1.),
         ('common_variance_ninefold', 20261118032, 3., 1.),
         ('receiver_variance_jump', 20261118033, 1., 3.))


def _operator():
    return LinearInnovations((dict(transition=[[1.]], process_loading=[[.12]],
        observation=[[1.]], white_loading=[[.4]]) for _ in range(CUT+LATER)),
        epoch_count=CUT+LATER, state_dimension=1, observation_dimension=1,
        initial_loading=[[.2]], maximum_bytes=10000,
        design_is_fixed=True, error_distribution='gaussian')


def _histories(seed, common_amplitude, later_white_amplitude):
    walk_seed, white_seed = np.random.SeedSequence(seed).spawn(2)
    rw, white = np.random.default_rng(walk_seed), np.random.default_rng(white_seed)
    count = CUT+LATER
    walk = rw.normal(scale=.2,size=(COUNT,1))+np.cumsum(rw.normal(scale=.12,size=(COUNT,count)),axis=1)
    scatter = white.normal(scale=.4,size=(COUNT,count))
    scatter[:,CUT:] *= later_white_amplitude
    return common_amplitude*(walk+scatter)


def build():
    operator = _operator()
    t = np.linspace(-1.,1.,CUT+LATER)
    design = np.column_stack((np.ones_like(t), t+.2*t*t))
    truth = design @ [2.,-1.2]
    results = []
    for name,seed,common,later in CASES:
        counts = dict(fixed=0, estimated=0)
        learned_scale = []
        for history in truth+_histories(seed,common,later):
            forecast = prepare(operator,design,history[:CUT],training_epochs=CUT,parameter_scales=[1.,1.])
            answer = score(operator,forecast,history[CUT:])
            if answer['status'] != 'scored' or answer['estimated_scale_f_statistic'] is None:
                raise ValueError('all fixed identifiable histories must be scored')
            values = ((answer['fixed_scale_reference_band'],answer['squared_standardized_error']),
                      (answer['estimated_scale_reference_band'],answer['estimated_scale_f_statistic']))
            for key, (reference, value) in zip(counts, values, strict=True):
                counts[key] += int(reference[0] <= value <= reference[1])
            learned_scale.append(answer['training_variance_scale_estimate'])
        success = counts['estimated']/COUNT
        passed = success<=.85 if name=='receiver_variance_jump' else .925<=success<=.975
        results.append(dict(case=name, seed=seed, samples=COUNT, reference_inclusions=counts,
            median_earlier_variance_scale=float(np.median(learned_scale)), passed=passed))
    return dict(cases=results, software_gate_passed=all(row['passed'] for row in results),
                observed_reads=0, protected_reads=0, native_calls=0, aircraft_calibrated=False,
                scientific_decision='abstain')


def run(root,action):
    own = Path(__file__).relative_to(root).as_posix()
    test = 'analysis/tests/test_calibrated_joint_path.py'
    config = encoded(dict(sources={p:digest((root/p).read_bytes()) for p in source_closure(root,(own,PLAN,test))},
        cases=CASES, histories_per_case=COUNT, training_epochs=CUT, later_epochs=LATER,
        maximum_affine_fits=COUNT*len(CASES), threads=1, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root/FREEZE,config)
        return dict(freeze_sha256=digest(config))
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('unchanged common-scale control freeze required')
    report = dict(build(),freeze_sha256=digest(config))
    payload = encoded(report)
    _write_equal(root/RESULT,payload)
    return dict(cases=report['cases'], passed=report['software_gate_passed'], sha256=digest(payload))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','replay'))
    print(run(Path.cwd(),parser.parse_args().action))
