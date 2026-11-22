# SPDX-License-Identifier: AGPL-3.0-or-later
"""Convert the remaining conditional shape error allowance to coordinate units."""

import argparse
from contextlib import closing
import gzip
import json
import math
from pathlib import Path

import numpy as np

from . import esa_changing_drift_transfer as full, esa_no_snap_ablation as reduced
from .airquantumgrav_error_policy import reported_covariance
from .conditioned_shape_calibration import projected_direction
from .esa_joint_path_score import _ranges
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .matched_shape_drift import ESA_REPORT, REPORTS
from .matched_shape_metric import PAIR, REFERENCE, REFERENCE_SHA
from .shape_remainder_headroom import RESULT as HEADROOM
from .shape_remainder_witness import HEADROOM_SHA
from .state_space_directional_bound import adjoint_intervals, directional_bound
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = full.FOLDER + 'SHAPE_REMAINDER_METRES_PLAN.md'
FREEZE = full.FOLDER + 'shape-remainder-metres-freeze.json'
RESULT = full.FOLDER + 'shape-remainder-metres-result.json'
HEADROOM_LIMIT = 12.78


def compare(root, report, reference, saved):
    setting = next(row for row in reference['settings'] if row['complete'] and row['imu_law'] == 'increment')
    selected = [setting['selected'][model] for model in PAIR]
    with closing(ClosedStudy(root, 'data/'+report['study_id'])) as study:
        if (study.completion['manifest_sha256'] != report['fit_manifest_sha256']
                or study.completion['summary_sha256'] != report['fit_summary_sha256']):
            raise ValueError('exact original calibration fit matrix required')
        times = study.input('forecast_times')
        earlier = json.loads(gzip.decompress(study.input('training', raw=True)))
    if len(earlier) != full.CUT or len(times) != full.CUT+full.LATER:
        raise ValueError('the original 400/120 split is required')
    roots = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in earlier]))
    factors = (np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((roots, np.repeat(roots[-1:], full.LATER, axis=0))))
    results = []
    for law, maker, receipt in zip(('full', 'reduced'), (full.operator, reduced.no_snap_operator), saved, strict=True):
        rows = {row['identity']: row for row in receipt['rows']}
        for weight, factor in zip(full.WEIGHTS, factors, strict=True):
            operator = maker(times, factor)
            if operator.configuration != receipt['operator_configurations'][weight]:
                raise ValueError('the original working covariance is required')
            a, b = (np.asarray(rows[identity]['ranges'][weight]['center_m']) for identity in selected)
            direction, nominal = projected_direction(operator, times, b-a, full.CUT)
            expected = setting['arms'][f'{law}/{weight}']['/'.join(PAIR)]['after_degrees'][2]['distance']
            if not math.isclose(nominal, expected, rel_tol=1e-9):
                raise ValueError('original projected shape distance did not replay')
            weights = np.concatenate((np.zeros(3*full.CUT), direction))
            lower, upper = adjoint_intervals(operator, weights)
            midpoint = .5*(lower+upper)
            probe = .01*np.sin(np.arange(len(weights)))
            forward, adjoint = float(weights@operator.whiten(probe)), float(midpoint@probe)
            if not math.isclose(forward, adjoint, rel_tol=1e-8, abs_tol=1e-8):
                raise ValueError('forward and adjoint probes differ')
            total = directional_bound(lower, upper, np.ones(len(weights)))
            cut = 3*full.CUT
            training = directional_bound(lower[:cut], upper[:cut], np.ones(cut))
            forecast = directional_bound(lower[cut:], upper[cut:], np.ones(len(weights)-cut))
            results.append(dict(covariance=law, receiver_weight=weight, nominal=nominal,
                earlier_coefficient_sum_upper=training, later_coefficient_sum_upper=forecast,
                full_coefficient_sum_upper=total, maximum_coefficient_interval_width=float(np.max(upper-lower)),
                forward_adjoint_difference=abs(forward-adjoint),
                earlier_only_limit_m=math.nextafter(HEADROOM_LIMIT/(2*training), -math.inf),
                later_only_limit_m=math.nextafter(HEADROOM_LIMIT/(2*forecast), -math.inf),
                full_limit_m=math.nextafter(HEADROOM_LIMIT/(2*total), -math.inf)))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'calculate'))
    args = parser.parse_args()
    root = Path.cwd()
    inputs = {name: (root/name).read_bytes() for name in (ESA_REPORT, REFERENCE, HEADROOM)}
    expected = {ESA_REPORT: REPORTS[ESA_REPORT], REFERENCE: REFERENCE_SHA, HEADROOM: HEADROOM_SHA}
    if any(digest(raw) != expected[name] for name, raw in inputs.items()):
        raise ValueError('exact original forecast and headroom evidence required')
    headroom = json.loads(inputs[HEADROOM])
    checked = [row['later_projected_remainder_headroom'] for regime in headroom['rows'] for row in regime['rows']
               if row['assumed_earlier_remainder'] == .1]
    if len(checked) != 4 or min(checked) <= HEADROOM_LIMIT:
        raise ValueError('headroom under the additional assumption must cover all four covariances')
    for source in (full, reduced):
        inputs.update({name: (root/name).read_bytes() for name in (source.FREEZE, source.RANGES, source.SEAL)})
    saved = [_ranges(inputs, source) for source in (full, reduced)]
    names = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_state_space_directional_bound.py')
    config = encoded(dict(inputs={name: digest(raw) for name, raw in inputs.items()},
                          sources={name: digest((root/name).read_bytes()) for name in source_closure(root, names)},
                          environment=runtime_environment(), threads=1, adjoint_passes=4,
                          fit_starts=0, later_position_reads=0, minimum_projected_headroom=HEADROOM_LIMIT))
    if args.action == 'freeze':
        _write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('unchanged finite coordinate conversion required')
    rows = compare(root, json.loads(inputs[ESA_REPORT]), json.loads(inputs[REFERENCE]), saved)
    result = encoded(dict(freeze_sha256=digest(config), rows=rows, fit_starts=0, protected_reads=0,
                          later_position_reads=0, aircraft_remainder_certified=False, scientific_decision='abstain'))
    _write_equal(root/RESULT, result)
    print(json.dumps(dict(arms=len(rows), sha256=digest(result)), sort_keys=True))


if __name__ == '__main__':
    main()
