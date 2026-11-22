# SPDX-License-Identifier: AGPL-3.0-or-later
"""Required nonlinear remainder bounds for one saved ESA shape contrast."""

import argparse
from contextlib import closing
import gzip
import json
import math
from pathlib import Path

import numpy as np

from . import esa_changing_drift_transfer as full, esa_no_snap_ablation as reduced
from .airquantumgrav_error_policy import reported_covariance
from .calibration_loss_support import support
from .conditioned_shape_calibration import PARENT_SHA, RESULT as AFFINE_RESULT
from .conditioned_shape_calibration import calibration_inputs, projected_direction
from .esa_joint_path_score import _ranges
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_solver_position import physical_metric
from .matched_shape_drift import ESA_REPORT, REPORTS
from .matched_shape_metric import PAIR, REFERENCE, REFERENCE_SHA
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = full.FOLDER + 'SHAPE_REMAINDER_HEADROOM_PLAN.md'
FREEZE = full.FOLDER + 'shape-remainder-headroom-freeze.json'
RESULT = full.FOLDER + 'shape-remainder-headroom-result.json'
AFFINE_SHA = 'cc7abb745499c2176ec3959846b0939d97255d025eb01faebd8ccc18a72cde75'
DELTAS = (0., .001, .01, .1, 1.)
LOSS_ALLOWANCE = .01


def expanded_loss_budget(residual, loss_allowance, delta):
    if not math.isfinite(delta) or delta < 0. or not math.isfinite(loss_allowance) or loss_allowance <= 0.:
        raise ValueError('finite nonnegative remainder and positive loss allowance required')
    norm = math.hypot(*residual, math.sqrt(loss_allowance))
    if not math.isfinite(norm):
        raise ValueError('finite earlier residual required')
    return loss_allowance + delta*(2.*norm + delta)


def box_support(objective, lower, upper):
    terms = np.maximum(np.multiply(objective, lower), np.multiply(objective, upper))
    return math.nextafter(math.fsum(np.nextafter(terms, np.inf)), math.inf)


def compare(root, report, reference, saved, original):
    setting = next(row for row in reference['settings'] if row['complete'] and row['imu_law'] == 'increment')
    selected = {model: setting['selected'][model] for model in PAIR}
    matrix = {row['identity']: row for row in report['rows']}
    with closing(ClosedStudy(root, 'data/'+report['study_id'])) as study:
        if (study.completion['manifest_sha256'] != report['fit_manifest_sha256']
                or study.completion['summary_sha256'] != report['fit_summary_sha256']):
            raise ValueError('exact original forecast matrix required')
        times = study.input('forecast_times')
        earlier = json.loads(gzip.decompress(study.input('training', raw=True)))
    if len(times) != full.CUT+full.LATER or len(earlier) != full.CUT:
        raise ValueError('unchanged 400/120 forecast support required')
    inputs = calibration_inputs(root, matrix, selected, times)
    observed = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in earlier]))
    factors = (np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((observed, np.repeat(observed[-1:], full.LATER, axis=0))))
    baseline = {(row['covariance'], row['receiver_weight']): row for row in original['rows']
                if row['earlier_loss_allowance'] == LOSS_ALLOWANCE}
    output = []
    for law, maker, receipt in zip(('full', 'reduced'), (full.operator, reduced.no_snap_operator), saved, strict=True):
        means = {row['identity']: row['ranges'] for row in receipt['rows'] if row['identity'] in selected.values()}
        metric = np.tile(physical_metric([receipt['anchor']])[0], len(times))
        for weight, factor in zip(full.WEIGHTS, factors, strict=True):
            covariance = maker(times, factor)
            if covariance.configuration != receipt['operator_configurations'][weight]:
                raise ValueError('original working covariance required')
            a, b = (np.asarray(means[selected[model]][weight]['center_m']) for model in PAIR)
            direction, nominal = projected_direction(covariance, times, b-a, full.CUT)
            read = baseline[law, weight]
            if not math.isclose(nominal, read['nominal'], rel_tol=1e-9):
                raise ValueError('nominal contrast differs from the archived bound')
            objectives = {model: sign*direction@covariance.whiten(metric[:, None]*inputs[model]['jacobian'])[3*full.CUT:]
                          for model, sign in zip(PAIR, (1, -1), strict=True)}
            box = math.fsum(box_support(objectives[model], inputs[model]['lower'], inputs[model]['upper']) for model in PAIR)
            rows = []
            for delta in DELTAS:
                reports = {}
                for model, item in inputs.items():
                    budget = expanded_loss_budget(item['earlier_residual'], LOSS_ALLOWANCE, delta)
                    result = support(item['earlier_jacobian'], item['earlier_residual'], objectives[model],
                                     item['lower'], item['upper'], budget=budget)
                    reports[model] = dict(result, expanded_loss_allowance=budget)
                closure = min(box, math.fsum(report['upper_bound'] for report in reports.values()))
                if delta == 0. and not math.isclose(closure, read['closure_upper'], rel_tol=1e-9):
                    raise ValueError('zero-remainder check did not reproduce the original')
                rows.append(dict(assumed_earlier_remainder=delta, closure_upper=closure,
                                 later_projected_remainder_headroom=max(0., nominal-closure), support=reports))
            output.append(dict(covariance=law, receiver_weight=weight, nominal=nominal,
                               box_only_closure_upper=box, box_only_signed_margin=nominal-box, rows=rows))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'calculate'))
    args = parser.parse_args()
    root = Path.cwd()
    inputs = {name: (root/name).read_bytes() for name in (ESA_REPORT, REFERENCE, AFFINE_RESULT)}
    expected = {ESA_REPORT: REPORTS[ESA_REPORT], REFERENCE: REFERENCE_SHA, AFFINE_RESULT: AFFINE_SHA}
    if any(digest(raw) != expected[name] for name, raw in inputs.items()):
        raise ValueError('exact released calibration and forecast reports required')
    for source in (full, reduced):
        inputs.update({name: (root/name).read_bytes() for name in (source.FREEZE, source.RANGES, source.SEAL)})
    saved = [_ranges(inputs, source) for source in (full, reduced)]
    names = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_shape_remainder_headroom.py')
    config = encoded(dict(inputs={name: digest(raw) for name, raw in inputs.items()}, parent_manifest=PARENT_SHA,
                          sources={name: digest((root/name).read_bytes()) for name in source_closure(root, names)},
                          environment=runtime_environment(), threads=1, cases=list(DELTAS), operators=4,
                          support_calls=40, solver_iterations_per_call=200, fit_starts=0, later_position_reads=0))
    if args.action == 'freeze':
        _write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('unchanged finite headroom calculation required')
    rows = compare(root, json.loads(inputs[ESA_REPORT]), json.loads(inputs[REFERENCE]), saved, json.loads(inputs[AFFINE_RESULT]))
    result = encoded(dict(freeze_sha256=digest(config), rows=rows, fit_starts=0, protected_reads=0,
                          later_position_reads=0, observed_remainder_certified=False, scientific_decision='abstain'))
    _write_equal(root/RESULT, result)
    print(json.dumps(dict(covariances=len(rows), sha256=digest(result)), sort_keys=True))


if __name__ == '__main__':
    main()
