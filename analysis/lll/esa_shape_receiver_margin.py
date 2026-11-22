# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounds and explicit tie witnesses for the fixed ESA matched-field shape score."""

from contextlib import closing
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

from .esa_shape_receiver_replay import EARLIER, FOLDER, LATER, PATHS, WITNESS, WITNESS_MANIFEST
from .esa_shape_receiver_replay import FREEZE as PRIOR_FREEZE, RESULT as PRIOR_RESULT
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


PLAN = FOLDER + 'ESA_SHAPE_RECEIVER_MARGIN_PLAN.md'
FREEZE = FOLDER + 'esa-shape-receiver-margin-freeze.json'
RESULT = FOLDER + 'esa-shape-receiver-margin-result.json'
PRIOR_SHA = '54a29bf629bff826e5b243f8b1e80353cd4604d6de7bb6bd40a95f9ed88cba77'
BLOCKS = 4
WITNESSES = ('original', 'gps_l1')


def acceleration_basis(times, cut, blocks):
    """Exact double integral of unit acceleration in successive time blocks."""
    time = [Fraction(float(t)) for t in times]
    if (not 0 < cut < len(time) or blocks < 2
            or any(left >= right for left, right in zip(time, time[1:]))):
        raise ValueError('strictly increasing earlier and later reports required')
    start = time[cut - 1]
    width = (time[-1] - start) / blocks
    knots = [start + width * index for index in range(blocks + 1)]
    return [[(max(0, t - left)**2 - max(0, t - right)**2) / 2
             if t > left else Fraction(0)
             for left, right in zip(knots, knots[1:])]
            for t in time]


def coefficient_enclosure(basis, lower, upper):
    """Apply the transpose of a nonnegative exact basis to interval weights."""
    low, high = [], []
    for col in zip(*basis, strict=True):
        if any(value < 0 for value in col):
            raise ValueError('the trajectory basis must have nonnegative entries')
        low.append([sum(weight * Fraction(float(row[axis])) for weight, row in
                        zip(col, lower, strict=True)) for axis in range(3)])
        high.append([sum(weight * Fraction(float(row[axis])) for weight, row in
                         zip(col, upper, strict=True)) for axis in range(3)])
    return low, high


def radius(margin, lower, upper):
    from .ilvis0_saved_prediction_audit import endpoint

    gain = sum(max(abs(Fraction(float(a))), abs(Fraction(float(b))))
               if not isinstance(a, Fraction) else max(abs(a), abs(b))
               for left, right in zip(lower, upper, strict=True)
               for a, b in zip(left, right, strict=True))
    if margin <= 0 or gain <= 0:
        raise ValueError('positive score margin and nonzero support required')
    return endpoint(Fraction(float(margin)) / gain, up=False)


def assess(operator, times, shape, scores):
    import numpy as np
    from .state_space_directional_bound import adjoint_intervals

    q = np.r_[np.zeros(3 * EARLIER), shape['direction']]
    lower, upper = [v.reshape(len(times), 3) for v in adjoint_intervals(operator, q)]
    basis = acceleration_basis(times, EARLIER, BLOCKS)
    basis_float = np.asarray(basis, dtype=float)
    lo_accel, hi_accel = coefficient_enclosure(basis, lower, upper)
    shapes = {
        'all_reports_coordinate_m': (lower, upper, lambda value: value),
        'later_reports_coordinate_m': (lower[EARLIER:], upper[EARLIER:],
                                      lambda value: np.pad(value, ((EARLIER, 0), (0, 0)))),
        'later_four_block_acceleration_mps2': (lo_accel, hi_accel,
                                               lambda value: basis_float @ value),
    }
    rows = {}
    for name, score in scores.items():
        margin = -score['signed_midpoint']
        rows[name] = dict(saved_signed_midpoint=-margin, families={})
        for family, (lo, hi, path) in shapes.items():
            bound = radius(margin, lo, hi)
            row = dict(required_peak_component_lower_bound=bound)
            if name in WITNESSES:
                midpoint = (np.asarray(lo, float) + np.asarray(hi, float)) / 2
                size = math.nextafter(bound * 1.000001, math.inf)
                change = path(np.sign(midpoint) * size)
                projected = float(q @ operator.whiten(change.ravel()))
                if not projected > margin or size > bound * 1.001:
                    raise ValueError('score crossing did not verify at the fixed witness tolerance')
                row.update(witness_peak_component=size, witness_score=-margin + projected,
                    witness_later_position_rms_m=float(np.linalg.norm(change[EARLIER:]) / math.sqrt(LATER)),
                    witness_later_peak_position_m=float(np.max(np.linalg.norm(change[EARLIER:], axis=1))))
            rows[name]['families'][family] = row
    return rows, float(np.max(upper - lower))


def run(root, action):
    from .ilvis0_control_shards import runtime_environment
    from .innovations_snapshot import restore
    from .studies.dependencies import source_closure

    prior_raw = (root / PRIOR_RESULT).read_bytes()
    if digest(prior_raw) != PRIOR_SHA:
        raise ValueError('same saved receiver scores required')
    prior = json.loads(prior_raw)
    prior_freeze_raw = (root / PRIOR_FREEZE).read_bytes()
    if prior['freeze_sha256'] != digest(prior_freeze_raw) or set(prior['scores']) != set(PATHS):
        raise ValueError('exact earlier score freeze and all eight paths required')
    with closing(ClosedStudy(root, 'data/' + WITNESS)) as study:
        if study.completion['manifest_sha256'] != WITNESS_MANIFEST or not study.summary['passed']:
            raise ValueError('closed forecast-direction witness required')
        shape = study.input('shape-direction')
        operator_bytes = study.input('later-operator', raw=True)
        times = study.input('forecast_times')
    upstream = json.loads(prior_freeze_raw)
    if (upstream['direction_sha256'] != digest(encoded(shape))
            or upstream['operator_sha256'] != digest(operator_bytes)
            or upstream['time_sha256'] != digest(encoded(times))
            or prior['nominal_separation'] != shape['nominal'] or len(times) != EARLIER + LATER):
        raise ValueError('unchanged matched-field score required')
    sources = source_closure(root, [Path(__file__).relative_to(root).as_posix(), PLAN,
                                   'analysis/tests/test_esa_shape_receiver_margin.py'])
    freeze = encoded(dict(
        sources={p: digest((root / p).read_bytes()) for p in sources},
        score_result_sha256=PRIOR_SHA, score_freeze_sha256=digest(prior_freeze_raw),
        witness_manifest_sha256=WITNESS_MANIFEST, environment=runtime_environment(), threads=1,
        later_acceleration_blocks=BLOCKS, adjoint_passes=1, maximum_forward_probes=6,
        fit_starts=0, forecast_propagations=0, protected_reads=0,
    ))
    target = root / FREEZE
    if action == 'freeze':
        if not target.exists():
            atomic(target, freeze)
        if target.read_bytes() != freeze:
            raise ValueError('existing receiver-margin freeze differs')
        print(digest(freeze))
        return
    if target.read_bytes() != freeze:
        raise ValueError('unchanged receiver-margin study required')
    operator = restore(operator_bytes, expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    rows, width = assess(operator, times, shape, prior['scores'])
    raw = encoded(dict(freeze_sha256=digest(freeze), receiver_paths=rows,
        maximum_adjoint_interval_width=width, calibrated=False, scientific_decision='abstain'))
    result = root / RESULT
    if not result.exists():
        atomic(result, raw)
    if result.read_bytes() != raw:
        raise ValueError('saved receiver-margin result differs')
    print(digest(raw))


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('freeze', 'calculate'):
        raise SystemExit('usage: python -m lll.esa_shape_receiver_margin {freeze,calculate}')
    run(Path.cwd(), sys.argv[1])
