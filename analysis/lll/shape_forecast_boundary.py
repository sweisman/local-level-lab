# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure same-field forecast separation after dropping early later reports."""

import argparse
from contextlib import closing
import gzip
import json
import math
from pathlib import Path

import numpy as np

from . import esa_changing_drift_transfer as full, esa_no_snap_ablation as reduced
from .airquantumgrav_error_policy import reported_covariance
from .esa_joint_path_score import _ranges
from .esa_scored_path_shape import project_residual
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .matched_shape_drift import ESA_REPORT, REPORTS
from .matched_shape_metric import PAIR, REFERENCE, REFERENCE_SHA
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = full.FOLDER + 'SHAPE_FORECAST_BOUNDARY_PLAN.md'
FREEZE = full.FOLDER + 'shape-forecast-boundary-freeze.json'
RESULT = full.FOLDER + 'shape-forecast-boundary-result.json'
OMIT = (0, 1, 5, 10, 20)


def conditional_factor(operator, cut):
    dimension = operator.observation_dimension
    remaining = (operator.epoch_count-cut)*dimension
    if not 0 < cut < operator.epoch_count or not 0 < remaining <= 512:
        raise ValueError('a supported earlier/later split is required')
    training = np.zeros((cut*dimension, remaining))
    _, state = operator.apply_block(training, first_epoch=0, inverse=True)
    return operator.apply_block(np.eye(remaining), first_epoch=cut, state=state, inverse=True)[0]


def marginal_factor(lower, omitted_coordinates):
    if not 0 <= omitted_coordinates < len(lower):
        raise ValueError('at least one retained coordinate is required')
    if omitted_coordinates == 0:
        return lower
    # Orthogonal triangularization avoids squaring the covariance condition number.
    upper = np.linalg.qr(lower[omitted_coordinates:].T, mode='r')
    return upper.T * np.sign(np.diag(upper))


def compare(root, report, reference, saved):
    with closing(ClosedStudy(root, 'data/'+report['study_id'])) as study:
        if (study.completion['manifest_sha256'] != report['fit_manifest_sha256']
                or study.completion['summary_sha256'] != report['fit_summary_sha256']):
            raise ValueError('exact completed ESA matrix required')
        times = study.input('forecast_times')
        earlier = json.loads(gzip.decompress(study.input('training', raw=True)))
    if len(times) != full.CUT + full.LATER or len(earlier) != full.CUT:
        raise ValueError('original 400/120 split required')
    observed = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in earlier]))
    factors = (np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((observed, np.repeat(observed[-1:], full.LATER, axis=0))))
    settings = [row for row in reference['settings'] if row['complete']]
    if len(settings) != 2:
        raise ValueError('both original complete settings required')
    results = []
    for law, maker, receipt in zip(('full', 'reduced'), (full.operator, reduced.no_snap_operator), saved, strict=True):
        rows = {row['identity']: row for row in receipt['rows']}
        for weight, factor in zip(full.WEIGHTS, factors, strict=True):
            operator = maker(times, factor)
            if operator.configuration != receipt['operator_configurations'][weight]:
                raise ValueError('unchanged earlier covariance choice required')
            root = conditional_factor(operator, full.CUT)
            marginals = [marginal_factor(root, 3*cut) for cut in OMIT]
            for setting in settings:
                primary = setting['selected']
                centers = [np.asarray(rows[primary[name]]['ranges'][weight]['center_m']) for name in PAIR]
                difference = centers[1]-centers[0]
                values = [project_residual(times[full.CUT+cut:], times[full.CUT-1], difference[cut:], lower)['residual_energy']
                          for cut, lower in zip(OMIT, marginals, strict=True)]
                baseline = setting['arms'][f'{law}/{weight}']['/'.join(PAIR)]['after_degrees'][2]['squared_distance']
                if (not math.isclose(values[0], baseline, rel_tol=1e-8)
                        or np.any(np.diff(values) > 1e-8*baseline)):
                    raise ValueError('original separation or marginal monotonicity did not verify')
                results.append(dict(covariance=law, receiver_weight=weight, imu_law=setting['imu_law'],
                                    omitted_reports=list(OMIT), squared_distances=values))
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
        raise ValueError('exact released ESA reports required')
    saved = [_ranges(inputs, source) for source in (full, reduced)]
    names = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_shape_forecast_boundary.py')
    config = encoded(dict(inputs={name: digest(raw) for name, raw in inputs.items()},
                          sources={name: digest((root/name).read_bytes()) for name in source_closure(root, names)},
                          environment=runtime_environment(), threads=1, operators=4, projections=40,
                          omitted_reports=list(OMIT), later_position_reads=0, fit_starts=0))
    if args.action == 'freeze':
        _write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('unchanged finite boundary check required')
    rows = compare(root, json.loads(inputs[ESA_REPORT]), json.loads(inputs[REFERENCE]), saved)
    output = encoded(dict(freeze_sha256=digest(config), rows=rows, protected_reads=0,
                          later_position_reads=0, trajectory_fits=0, scientific_decision='abstain'))
    _write_equal(root/RESULT, output)
    print(json.dumps(dict(arms=len(rows), sha256=digest(output)), sort_keys=True))


if __name__ == '__main__':
    main()
