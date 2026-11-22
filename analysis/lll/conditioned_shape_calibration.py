# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-loss constrained shape contrast in the conditioned forecast score."""

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
from .esa_calibration_contrast import BUDGETS, ID, RADIUS
from .esa_joint_path_score import _ranges
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_solver_position import physical_metric
from .matched_shape_drift import ESA_REPORT, REPORTS
from .matched_shape_metric import PAIR, REFERENCE, REFERENCE_SHA
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = full.FOLDER + 'CONDITIONED_SHAPE_CALIBRATION_PLAN.md'
FREEZE = full.FOLDER + 'conditioned-shape-calibration-freeze.json'
RESULT = full.FOLDER + 'conditioned-shape-calibration-result.json'
PARENT_SHA = 'b6090b845e20a82e617e05e4f00e97c342729dcecd2150a7ce4bd56e40bbb3ef'


def projected_direction(operator, times, difference, cut):
    count = len(times)-cut
    t = np.asarray(times[cut:], float)
    phase = 2. * (t-t[0])/(t[-1]-t[0])-1.
    smooth = np.kron(np.polynomial.legendre.legvander(phase, 2), np.eye(3))
    columns = np.zeros((3*len(times), 10))
    columns[3*cut:] = np.column_stack((np.asarray(difference).reshape(3*count), smooth))
    later = operator.whiten(columns)[3*cut:]
    basis, upper = np.linalg.qr(later[:, 1:], mode='reduced')
    if np.linalg.matrix_rank(upper) != 9:
        raise ValueError('all nine smooth directions must be retained')
    separation = later[:, 0] - basis @ (basis.T @ later[:, 0])
    norm = float(np.linalg.norm(separation))
    if not norm > 0.:
        raise ValueError('nonzero shape contrast required')
    return separation/norm, norm


def calibration_inputs(root, matrix, selected, times):
    found = {}
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if study.completion['manifest_sha256'] != PARENT_SHA or study.completion['state'] != 'complete':
            raise ValueError('exact completed calibration contrast study required')
        for model, identity in selected.items():
            fit = study.input(model+'-fit')
            tangent = study.artifact(model, 'full-tangent.json')
            local = fit['local_linearization']
            if (tangent['source_forecast_sha256'] != matrix[identity]['forecast_sha256']
                    or tangent['forecast_queries_s'] != times or tangent['weighting_applied'] is not False
                    or tangent['jacobian_shape'] != [3*len(times), 27]
                    or fit['normalized_parameters'] != tangent['normalized_parameters']
                    or local['normalized_parameters'] != tangent['normalized_parameters']
                    or local['active_parameters'] != tangent['active_parameters']):
                raise ValueError('exact forecast, earlier derivative and parameter point required')
            point = np.asarray(tangent['normalized_parameters'])
            found[model] = dict(jacobian=np.asarray(tangent['jacobian']),
                                earlier_jacobian=local['jacobian'], earlier_residual=local['residual'],
                                lower=np.maximum(-RADIUS, -1-point), upper=np.minimum(RADIUS, 1-point))
    return found


def compare(root, matrix, reference, saved):
    setting = next(row for row in reference['settings'] if row['complete'] and row['imu_law'] == 'increment')
    selected = {name: setting['selected'][name] for name in PAIR}
    rows = {row['identity']: row for row in matrix['rows']}
    with closing(ClosedStudy(root, 'data/'+matrix['study_id'])) as study:
        if (study.completion['manifest_sha256'] != matrix['fit_manifest_sha256']
                or study.completion['summary_sha256'] != matrix['fit_summary_sha256']):
            raise ValueError('exact original fit matrix required')
        times = study.input('forecast_times')
        earlier = json.loads(gzip.decompress(study.input('training', raw=True)))
    if len(earlier) != full.CUT or len(times) != full.CUT+full.LATER:
        raise ValueError('exact earlier/later split required')
    original = calibration_inputs(root, rows, selected, times)
    observed = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in earlier]))
    factors = (np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((observed, np.repeat(observed[-1:], full.LATER, axis=0))))
    results = []
    for law, maker, receipt in zip(('full', 'reduced'), (full.operator, reduced.no_snap_operator), saved, strict=True):
        centers = {row['identity']: row['ranges'] for row in receipt['rows'] if row['identity'] in selected.values()}
        metric = np.tile(physical_metric([receipt['anchor']])[0], len(times))
        for weight, factor in zip(full.WEIGHTS, factors, strict=True):
            operator = maker(times, factor)
            if operator.configuration != receipt['operator_configurations'][weight]:
                raise ValueError('exact original covariance required')
            a, b = (np.asarray(centers[selected[model]][weight]['center_m']) for model in PAIR)
            direction, nominal = projected_direction(operator, times, b-a, full.CUT)
            reference_value = setting['arms'][f'{law}/{weight}']['/'.join(PAIR)]['after_degrees'][2]['distance']
            if not math.isclose(nominal, reference_value, rel_tol=1e-9):
                raise ValueError('original projected separation did not replay')
            derivative = {model: operator.whiten(metric[:, None]*original[model]['jacobian'])[3*full.CUT:]
                          for model in PAIR}
            for budget in BUDGETS:
                bounds = {}
                for model, sign in zip(PAIR, (1, -1), strict=True):
                    item = original[model]
                    bounds[model] = support(item['earlier_jacobian'], item['earlier_residual'],
                                            sign*direction@derivative[model], item['lower'], item['upper'], budget=budget)
                closure = sum(item['upper_bound'] for item in bounds.values())
                results.append(dict(covariance=law, receiver_weight=weight, earlier_loss_allowance=budget,
                                    nominal=nominal, closure_upper=closure, lower_remaining=max(0., nominal-closure),
                                    support=bounds))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'calculate'))
    args = parser.parse_args()
    root = Path.cwd()
    inputs = {name: (root/name).read_bytes() for name in (ESA_REPORT, REFERENCE)}
    for source in (full, reduced):
        inputs.update({name: (root/name).read_bytes() for name in (source.FREEZE, source.RANGES, source.SEAL)})
    if digest(inputs[REFERENCE]) != REFERENCE_SHA or digest(inputs[ESA_REPORT]) != REPORTS[ESA_REPORT]:
        raise ValueError('exact released earlier-only forecasts required')
    saved = [_ranges(inputs, source) for source in (full, reduced)]
    names = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_conditioned_shape_calibration.py')
    config = encoded(dict(inputs={name: digest(raw) for name, raw in inputs.items()}, parent_manifest=PARENT_SHA,
                          sources={name: digest((root/name).read_bytes()) for name in source_closure(root, names)},
                          environment=runtime_environment(), threads=1, support_calls=16, solver_iterations_per_call=200,
                          later_position_reads=0, native_calls=0, fit_starts=0))
    if args.action == 'freeze':
        _write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('unchanged finite calibration sensitivity required')
    rows = compare(root, json.loads(inputs[ESA_REPORT]), json.loads(inputs[REFERENCE]), saved)
    result = encoded(dict(freeze_sha256=digest(config), rows=rows, fit_starts=0, protected_reads=0,
                          later_position_reads=0, affine_only=True, scientific_decision='abstain'))
    _write_equal(root/RESULT, result)
    print(json.dumps(dict(arms=len(rows), sha256=digest(result)), sort_keys=True))


if __name__ == '__main__':
    main()
