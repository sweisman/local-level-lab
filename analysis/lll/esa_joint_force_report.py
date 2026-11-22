# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decompose the six sealed ESA force certificates without new bound calls."""

from contextlib import closing
from fractions import Fraction
from pathlib import Path


MANIFEST_SHA = 'a9ee4ce5ceeff698971d36b36676b3000df51fe08d40e4d2dd38c1bfed94d084'
RESULT = 'docs/prediction-observed-development/esa-joint-force-decomposition.json'


def report(root):
    import numpy as np
    from .esa_joint_force_support import FORCE_START, ID, INCREASE, MODELS, REMAINDERS
    from .esa_linked_training_support import projection_inputs
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_linked_training_support import split_support, training_upper
    from .ilvis0_saved_prediction_audit import endpoint
    from .state_space_directional_bound import adjoint_intervals
    from .studies.closed import ClosedStudy

    rows = []
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if study.completion['manifest_sha256'] != MANIFEST_SHA or not study.summary['passed']:
            raise ValueError('complete frozen joint force study required')

        def load(key):
            return study.input(key, raw=True)

        for model in MODELS:
            residual, raw_earlier, _, lower, upper, earlier, target, settings = projection_inputs(load, model)
            directions = study.input(model+'-directions')['rows']
            saved = study.artifact(model, 'joint-supports.json')
            if (saved['nominal_separation'] != settings['shape']['nominal']
                    or [row['unshared_earlier_norm'] for row in directions] != list(REMAINDERS)
                    or [row['unshared_earlier_norm'] for row in saved['rows']] != list(REMAINDERS)):
                raise ValueError('certificate grouping differs from the sealed inputs')
            for row, original in zip(saved['rows'], directions, strict=True):
                gamma = row['unshared_earlier_norm']
                direction = original['direction']
                multiplier = Fraction(original['multiplier'])
                lo, hi = adjoint_intervals(earlier, direction)
                projected = coefficients(lo, hi, np.ones(len(residual)), raw_earlier)
                training = tuple(zip(projected['lower'], projected['upper'], strict=True))
                constraint = training_upper(residual, direction, increase=INCREASE, unshared=gamma)
                cumulative = [multiplier*constraint]
                for stop in (27, 33, FORCE_START):
                    nonforce, force = split_support(training, target, lower, upper,
                                                     multiplier=multiplier, bound=constraint, shared_start=stop)
                    cumulative.append(nonforce)
                force_independent = sum(max(-a, b) for a, b in force)
                force_bound = min(force_independent, Fraction(row['force_bound']['upper']))
                cumulative.append(nonforce+force_bound)
                if (nonforce+force_independent != Fraction(original['exact_upper'])
                        or cumulative[-1] != Fraction(row['exact_coupled_upper'])):
                    raise ValueError('grouped terms do not reproduce both exact certificates')
                components = [cumulative[0]] + [b-a for a, b in zip(cumulative, cumulative[1:])]
                names = ('loss_allowance', 'physical', 'clock_lever', 'acceleration', 'force')
                rows.append(dict(model=model, earlier_unshared=gamma,
                                 combined=row['coupled_upper'],
                                 components={name: endpoint(value, True)
                                             for name, value in zip(names, components, strict=True)}))
    return dict(manifest_sha256=MANIFEST_SHA, rows=rows, fit_starts=0,
                new_bound_calls=0, scientific_decision='abstain')


if __name__ == '__main__':
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded

    root = Path.cwd()
    raw = encoded(report(root))
    _write_equal(root/RESULT, raw)
    print(digest(raw))
