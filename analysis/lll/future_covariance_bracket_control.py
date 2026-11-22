# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent finite dense/simulation controls for the covariance bracket."""

import argparse
from pathlib import Path

import numpy as np

from .future_covariance_bracket import prepare, score
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .state_space_covariance import LinearInnovations
from .studies.artifacts import digest, encoded
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER + 'FUTURE_COVARIANCE_BRACKET_PLAN.md'
FREEZE = FOLDER + 'future-covariance-bracket-freeze.json'
RESULT = FOLDER + 'future-covariance-bracket-result.json'
CUT, LATER, D, COUNT = 9, 6, 3, 256
CASES = (('no_change', 20261118071, 0.),
         ('inside', 20261118072, .5),
         ('upper_limit', 20261118073, 1.),
         ('outside', 20261118074, 3.))
BASE_WHITE = np.array([[.4, 0., 0.], [.08, .35, 0.], [0., -.06, .3]])
EXTRA_WHITE = np.array([[.9, 0., 0.], [-.2, .7, 0.], [.1, .18, .55]])
EXTRA_WALK = np.array([[.12, 0., 0.], [0., .18, 0.], [.03, 0., .1]])


def _base():
    identity = np.eye(D)
    return LinearInnovations((dict(transition=identity, process_loading=.12 * identity,
        observation=identity, white_loading=BASE_WHITE) for _ in range(CUT + LATER)),
        epoch_count=CUT + LATER, state_dimension=D, observation_dimension=D,
        initial_loading=.2 * identity, maximum_bytes=20_000, design_is_fixed=True,
        error_distribution='gaussian')


def _data(seed, added_amplitude, design, white, walk):
    seeds = np.random.SeedSequence(seed).spawn(4)
    base_walk, base_white, extra_white, extra_walk = map(np.random.default_rng, seeds)
    n = CUT + LATER
    measurement = base_walk.normal(scale=.2, size=(COUNT, 1, D)) + np.cumsum(
        base_walk.normal(scale=.12, size=(COUNT, n, D)), axis=1)
    measurement += base_white.normal(size=(COUNT, n, D)) @ BASE_WHITE.T
    measurement[:, CUT:] += added_amplitude * (
        np.einsum('nij,rnj->rni', white, extra_white.normal(size=(COUNT, LATER, D)))
        + np.cumsum(np.einsum('nij,rnj->rni', walk,
                              extra_walk.normal(size=(COUNT, LATER, D))), axis=1))
    return (1.8 * measurement).reshape(COUNT, n * D) + design @ [2., -1.2]


def _exact_errors(data, design, white, walk, added_amplitude):
    n = CUT + LATER
    t = np.arange(1., n + 1)
    base = np.kron(.2**2 + .12**2 * np.minimum.outer(t, t), np.eye(D))
    base += np.kron(np.eye(n), BASE_WHITE @ BASE_WHITE.T)
    cut = CUT * D
    past, cross = base[:cut, :cut], base[cut:, :cut]
    influence = np.linalg.solve(past, cross.T).T
    p = design[:cut]
    precision_p = np.linalg.solve(past, p)
    vc = np.linalg.inv(p.T @ precision_p)
    c = design[cut:] - influence @ p
    mean = data[:, :cut] @ (influence + c @ vc @ precision_p.T).T
    conditional = base[cut:, cut:] - influence @ cross.T + c @ vc @ c.T
    cumulative = np.cumsum(walk @ np.swapaxes(walk, 1, 2), axis=0)
    for i in range(LATER):
        for j in range(LATER):
            a, b = slice(i * D, (i + 1) * D), slice(j * D, (j + 1) * D)
            conditional[a, b] += added_amplitude**2 * cumulative[min(i, j)]
        conditional[a, a] += added_amplitude**2 * white[i] @ white[i].T
    cholesky = np.linalg.cholesky(conditional)
    squared = np.linalg.solve(cholesky, (data[:, cut:] - mean).T)**2
    return squared.sum(axis=0)


def build():
    operator = _base()
    t = np.linspace(-1., 1., CUT + LATER)
    design = np.column_stack((np.tile([1., .4, -.2], len(t)),
                              np.kron(t + .2*t*t, [.2, -.6, 1.])))
    white = np.linspace(.7, 1.2, LATER)[:, None, None] * EXTRA_WHITE
    walk = np.linspace(1.2, .8, LATER)[:, None, None] * EXTRA_WALK
    wrong = np.zeros((LATER, D))
    wrong[:, 0] = 4.0 * (-1.0)**np.arange(LATER)
    rows = []
    for name, seed, amplitude in CASES:
        data = _data(seed, amplitude, design, white, walk)
        exact = _exact_errors(data, design, white, walk, amplitude)
        counts = dict(true_quadratic_bounded=0, base_inside=0, any_inside=0, all_inside=0,
                      above_reference=0, wrong_mean_rejected=0)
        for history, truth in zip(data, exact, strict=True):
            forecast = prepare(operator, design, history[:CUT*D], training_epochs=CUT,
                               parameter_scales=[1., 1.], future_white_loading=white,
                               future_walk_loading=walk, maximum_bytes=20_000)
            later = history[CUT*D:]
            out = score(forecast, later)
            if out['status'] != 'scored':
                raise ValueError('every fixed identifiable history must receive a score')
            qlo, qhi = out['quadratic_range']
            lo, hi = out['reference_band']
            tolerance = 1e-10 * (1 + truth)
            counts['true_quadratic_bounded'] += int(qlo - tolerance <= truth <= qhi + tolerance)
            counts['base_inside'] += int(lo <= out['pivot_range'][1] <= hi)
            counts['any_inside'] += int(out['any_covariance_inside_reference'])
            counts['all_inside'] += int(out['every_covariance_inside_reference'])
            counts['above_reference'] += int(out['every_covariance_above_reference'])
            if name == 'inside':
                counts['wrong_mean_rejected'] += int(score(forecast, later + wrong.ravel())[
                    'every_covariance_above_reference'])
        passed = (amplitude > 1.0 or (counts['true_quadratic_bounded'] == COUNT
                  and counts['any_inside'] >= .92 * COUNT))
        rows.append(dict(case=name, seed=seed, samples=COUNT,
                         extra_covariance_fraction=amplitude**2, counts=counts, passed=passed))
    return dict(cases=rows, software_gate_passed=all(row['passed'] for row in rows),
                aircraft_reads=0, native_calls=0, aircraft_calibrated=False,
                scientific_decision='abstain')


def run(root, action):
    own = Path(__file__).relative_to(root).as_posix()
    test = 'analysis/tests/test_future_covariance_bracket.py'
    config = encoded(dict(sources={p: digest((root / p).read_bytes())
        for p in source_closure(root, (own, PLAN, test))},
        cases=CASES, histories_per_case=COUNT, training_epochs=CUT, later_epochs=LATER,
        maximum_affine_fits=COUNT * len(CASES), maximum_scores=COUNT * (len(CASES) + 1),
        threads=1, aircraft_reads=0, native_calls=0, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('unchanged future-covariance control freeze required')
    result = dict(build(), freeze_sha256=digest(config))
    payload = encoded(result)
    _write_equal(root / RESULT, payload)
    return dict(cases=result['cases'], passed=result['software_gate_passed'],
                sha256=digest(payload))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
