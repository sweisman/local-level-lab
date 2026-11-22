# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproducible checks for adaptive contrast directions and split prediction."""

import argparse
from pathlib import Path

import numpy as np

from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .split_contrast_prediction import prepare, predict, score
from .state_space_covariance import LinearInnovations
from .studies.artifacts import digest, encoded
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER + 'SPLIT_CONTRAST_PLAN.md'
FREEZE = FOLDER + 'split-contrast-freeze.json'
RESULT = FOLDER + 'split-contrast-result.json'
CHOICE, CUT, FUTURE, PARAMETERS, COUNT = 18, 36, 12, 6, 512
SEED = 20261118219


def build():
    generators = [np.random.default_rng(seed) for seed in np.random.SeedSequence(SEED).spawn(5)]
    layout, first_draws, second_draws, future_draws, extra_draws = generators
    early_design = layout.normal(size=(CHOICE, PARAMETERS))
    future_design = 10.0 * layout.normal(size=(FUTURE, PARAMETERS))
    design = np.vstack((early_design, early_design, future_design))
    operator = LinearInnovations((dict(transition=[[1.]], process_loading=[[0.]],
        observation=[[1.]], white_loading=[[1.]]) for _ in range(CUT + FUTURE)),
        epoch_count=CUT + FUTURE, state_dimension=1, observation_dimension=1,
        initial_loading=[[0.]], maximum_bytes=10000, design_is_fixed=True,
        error_distribution='gaussian')
    a = 1.7 * first_draws.normal(size=(COUNT, CHOICE))
    b = 1.7 * second_draws.normal(size=(COUNT, CUT - CHOICE))
    later = 1.7 * future_draws.normal(size=(COUNT, FUTURE))
    after_cut = 1.7 * extra_draws.normal(size=(COUNT, PARAMETERS)) @ future_design.T
    coefficient_map = np.linalg.pinv(early_design)
    choose, reuse = (window @ coefficient_map.T @ future_design.T for window in (a, b))
    counts = {case: dict(inside_contrast=0, inside_orthogonal=0, above_contrast=0)
              for case in ('disjoint_windows', 'reused_choice_data', 'extra_later_error')}
    for earlier, latter, shock, honest, adaptive in zip(
            np.hstack((a, b)), later, after_cut, choose, reuse, strict=True):
        calibrated = []
        for direction in (honest, adaptive):
            construction = prepare(operator, design, direction[:, None],
                                   choice_epochs=CHOICE, training_epochs=CUT)
            calibrated.append(predict(construction, earlier))
        for case, forecast, response in zip(counts,
                (calibrated[0], calibrated[1], calibrated[0]),
                (latter, latter, latter + shock), strict=True):
            result = score(forecast, response)
            if result['status'] != 'scored' or result['contrast_coordinates'] != 1:
                raise ValueError('fixed one-direction software experiment must be scorable')
            contrast, common = result['contrast_f'], result['orthogonal_f']
            low, high = result['contrast_reference']
            low_o, high_o = result['orthogonal_reference']
            counts[case]['inside_contrast'] += int(low <= contrast <= high)
            counts[case]['above_contrast'] += int(contrast > high)
            counts[case]['inside_orthogonal'] += int(low_o <= common <= high_o)
    split = counts['disjoint_windows']
    passed = (all(.91 * COUNT <= split[key] <= .99 * COUNT
                  for key in ('inside_contrast', 'inside_orthogonal'))
              and all(counts[key]['above_contrast'] >= .20 * COUNT
                      for key in ('reused_choice_data', 'extra_later_error')))
    return dict(cases=counts, histories_per_condition=COUNT, software_gate_passed=passed,
                observed_reads=0, native_calls=0, aircraft_calibrated=False,
                scientific_decision='abstain')


def run(root, action):
    own = Path(__file__).relative_to(root).as_posix()
    test = 'analysis/tests/test_split_contrast_prediction.py'
    config = encoded(dict(sources={p: digest((root / p).read_bytes()) for p in
        source_closure(root, (own, PLAN, test))},
        seed=SEED, choice=CHOICE, cut=CUT, later=FUTURE, parameters=PARAMETERS,
        histories=COUNT, affine_coefficient_evaluations=4*COUNT, scores=3*COUNT, native_calls=0,
        threads=1, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('same fixed split-contrast control required')
    report = dict(build(), freeze_sha256=digest(config))
    payload = encoded(report)
    _write_equal(root / RESULT, payload)
    return dict(cases=report['cases'], passed=report['software_gate_passed'], sha256=digest(payload))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
