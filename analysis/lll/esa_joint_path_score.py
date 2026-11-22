# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay correlated scores for sealed observed and generated ESA forecasts."""

import argparse
from contextlib import closing
import gzip
import json
import math
from pathlib import Path

import numpy as np

from . import esa_changing_drift_transfer as full
from . import esa_no_snap_ablation as reduced
from . import esa_no_snap_generated_backcheck as generated_reduced
from . import esa_threshold_42_validation as generated
from .airquantumgrav_error_policy import reported_covariance
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = full.FOLDER+'ESA_JOINT_PATH_SCORE_PLAN.md'
FREEZE = full.FOLDER+'esa-joint-path-score-freeze.json'
OBSERVED = full.FOLDER+'esa-joint-path-score-observed.json'
GENERATED = full.FOLDER+'esa-joint-path-score-generated.json'
LAWS = ('full', 'reduced')


def joint_score(operator, cut, centered, *, horizons):
    """Proper joint log score under a fixed conditional covariance and mean.

    Centered innovations have a zero initial mean at the later boundary.
    The gains and innovation covariance are still those conditioned on the
    full earlier observation support. No updating changes the saved forecast.
    """
    d = operator.observation_dimension
    if (type(cut) is not int or cut < 1 or np.shape(centered) != (operator.epoch_count-cut, d)
            or any(type(n) is not int or not 1 <= n <= len(centered) for n in horizons)):
        raise ValueError('complete centered path and exact conditional horizon required')
    _, state = operator.apply_block(np.zeros(cut*d), first_epoch=0)
    white, _ = operator.apply_block(np.asarray(centered).ravel(), first_epoch=cut, state=state)
    earlier_determinant = operator.prefix(cut).log_determinant
    result = {}
    for n in horizons:
        part = white[:n*d]
        score = float(part@part)
        logdet = operator.prefix(cut+n).log_determinant-earlier_determinant
        result[str(n)] = dict(squared_standardized_error=score,
            standardized_rms=math.sqrt(score/len(part)), conditional_log_determinant=logdet,
            gaussian_negative_log_score=(score+logdet+len(part)*math.log(2.*math.pi))/2.,
            whitened_rms_neu_order=np.sqrt(np.mean(part.reshape(n, d)**2, axis=0)).tolist())
    return result


def _ranges(raw, module):
    sealed = json.loads(raw[module.SEAL])
    ranges = json.loads(gzip.decompress(raw[module.RANGES]))
    if (sealed != dict(freeze_sha256=digest(raw[module.FREEZE]), ranges_sha256=digest(raw[module.RANGES]),
                       later_receiver_reads=0) or ranges['freeze_sha256'] != sealed['freeze_sha256']
            or ranges['later_receiver_positions_used'] is not False or len(ranges['rows']) != 24):
        raise ValueError('verified earlier-only forecast range required')
    return ranges


def _matches(rows, prior):
    by_id = {r['identity']:r for r in rows}
    settings = []
    for setting in prior:
        results = {}
        if setting['complete']:
            ids = setting['primary']
            for law in LAWS:
                results[law] = {}
                for weight in full.WEIGHTS:
                    ranked = {model:by_id[identity]['scores'][law][weight]['120']['squared_standardized_error']
                              for model,identity in ids.items()}
                    rotating, still, disc = (ranked[m] for m in full.MODELS)
                    shape_gap = disc-min(rotating, still)
                    shape = 'globe' if shape_gap > 0. else 'disc' if shape_gap < 0. else 'tie'
                    results[law][weight] = dict(scores=ranked, descriptive_shape=shape,
                        disc_minus_globe_squared_error=shape_gap,
                        within_globe_squared_error_gap=still-rotating if shape=='globe' else None)
        settings.append(dict(profile=setting['profile'], imu_law=setting['law'], complete=setting['complete'],
                             scores=results))
    return settings


def _observed(raw, store, root, ranges):
    matrix = ClosedStudy(root, 'data/'+full.ID, store=store)
    parent = ClosedStudy(root, full.PARENT, store=store)
    prior_full, prior_reduced = (json.loads(raw[module.RESULT]) for module in (full, reduced))
    for scores, module in zip((prior_full, prior_reduced), (full, reduced), strict=True):
        if any(scores[key]!=value for key,value in json.loads(raw[module.SEAL]).items()):
            raise ValueError('saved scores must bind the same earlier range')
    settings = ('profile', 'law', 'complete', 'primary')
    signatures = [[tuple(r[key] for key in settings) for r in prior['matched_settings']]
                  for prior in (prior_full, prior_reduced)]
    if (json.loads(raw[full.FREEZE])['parents'] != [matrix.completion, parent.completion]
            or signatures[0] != signatures[1]
            or matrix.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'):
        raise ValueError('unchanged observed development parents required')
    early_rows = json.loads(gzip.decompress(matrix.input('training', raw=True)))
    times = matrix.input('forecast_times')
    fixed = np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times),3,3))
    earlier = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in early_rows]))
    reported = np.concatenate((earlier, np.repeat(earlier[-1:], full.LATER, axis=0)))
    models = {law:{weight:maker(times, values) for weight,values in zip(full.WEIGHTS, (fixed, reported), strict=True)}
              for law,maker in zip(LAWS, (full.operator, reduced.no_snap_operator), strict=True)}
    for law, data in zip(LAWS, ranges, strict=True):
        if ({key:v.configuration for key,v in models[law].items()} != data['operator_configurations']
                or data['anchor'] != ranges[0]['anchor']):
            raise ValueError('sealed covariance or earlier coordinate chart changed')
    source = json.loads(gzip.decompress(parent.input('training', raw=True)))
    later = source[full.CUT:full.CUT+full.LATER]
    if (source[:full.CUT] != early_rows or len(later) != full.LATER
            or digest(encoded(later)) != prior_full['later_receiver_sha256']
            or prior_full['later_receiver_sha256'] != prior_reduced['later_receiver_sha256']):
        raise ValueError('unchanged receiver scoring rows required')
    observed = full._chart(full._coordinates(later), ranges[0]['anchor'])
    records = []
    for left,right in zip(*(data['rows'] for data in ranges), strict=True):
        identity = left['identity']
        passed = left['passed']
        if (right['identity'] != identity or right['passed'] is not passed
                or matrix.rows[identity]['passed'] is not passed):
            raise ValueError('matched range identities changed')
        result = dict(identity=identity, model=left['model'], passed=passed)
        if passed:
            result['scores'] = {law:{weight:joint_score(models[law][weight], full.CUT,
                np.asarray(row['ranges'][weight]['center_m'])-observed, horizons=(60,120))
                for weight in full.WEIGHTS} for law,row in zip(LAWS, (left,right), strict=True)}
        records.append(result)
    return dict(rows=records, settings=_matches(records, prior_full['matched_settings']),
                recording=187, aircraft_coverage_established=False)


def _generated(raw, study):
    policy = generated.POLICY
    cut, later = policy['training_epochs'], policy['forecast_epochs']
    n = cut+later
    weights = np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (n,3,3))
    op = {law:make(np.arange(n, dtype=float), weights)
          for law,make in zip(LAWS, (full.operator, reduced.no_snap_operator), strict=True)}
    records = []
    prior = json.loads(raw[generated_reduced.RESULT])
    for task, old in zip(generated.tasks(), prior['rows'], strict=True):
        identity = task['identity']
        seed, vibration = (task['payload'][key] for key in ('seed', 'vibration'))
        if (old['seed'] != seed or old['vibration'] is not vibration or not study.rows[identity]['passed']):
            raise ValueError('unchanged generated case required')
        saved = study.artifact(identity, 'conditional-forecast.json')
        if (saved['later_receiver_positions_used'] is not False or saved['training_epochs'] != cut
                or saved['operator_configuration'] != op['full'].configuration):
            raise ValueError('original generated operator or split changed')
        alternative = full.condition(op['reduced'], saved['earlier_residual_neu_m'], np.zeros((later,3)))
        if digest(encoded(alternative)) != old['earlier_only_range_sha256']:
            raise ValueError('unchanged earlier-only generated ablation required')
        outcome = study.artifact(identity, 'outcome.json')
        residual = np.asarray(outcome['later_residual_neu_m'])
        if outcome['seed'] != seed or outcome['vibration'] is not vibration:
            raise ValueError('unchanged generated later scoring rows required')
        centers = (-np.asarray(saved['future_mean_neu_m']), np.asarray(alternative['center_m']))
        scores = {law:joint_score(op[law], cut, residual+center, horizons=(later,))[str(later)]
                  for law,center in zip(LAWS, centers, strict=True)}
        records.append(dict(seed=seed, vibration=vibration, scores=scores))
    return dict(rows=records, retrospective_generated_comparison=True)


def run(root, action):
    with closing(ArchiveStore(root)) as store:
        simulations = ClosedStudy(root, 'data/'+generated.ID, store=store)
        paths = (full.FREEZE, full.RANGES, full.SEAL, full.RESULT, reduced.FREEZE, reduced.RANGES,
                 reduced.SEAL, reduced.RESULT, generated_reduced.FREEZE, generated_reduced.RESULT)
        raw = {path:(root/path).read_bytes() for path in paths}
        prior = json.loads(raw[generated_reduced.FREEZE])
        if (prior['completion'] != simulations.completion or len(simulations.rows)!=256
                or json.loads(raw[generated_reduced.RESULT])['freeze_sha256'] != digest(raw[generated_reduced.FREEZE])):
            raise ValueError('unchanged generated cohort and ablation report required')
        ranges = [_ranges(raw, module) for module in (full, reduced)]
        own = Path(__file__).relative_to(root).as_posix()
        test = 'analysis/tests/test_esa_joint_path_score.py'
        config = encoded(dict(sources={p:digest((root/p).read_bytes()) for p in source_closure(root, (own, PLAN, test))},
            inputs={p:digest(b) for p,b in raw.items()}, operators=6, maximum_observed_evaluations=80,
            maximum_generated_evaluations=512, threads=1, fit_starts=0, environment=runtime_environment()))
        if action == 'freeze':
            _write_equal(root/FREEZE, config)
            return dict(freeze_sha256=digest(config))
        if (root/FREEZE).read_bytes() != config:
            raise ValueError('changed joint score freeze')
        if action == 'observed':
            result, output = _observed(raw, store, root, ranges), OBSERVED
        else:
            result, output = _generated(raw, simulations), GENERATED
    encoded_result = encoded(dict(result, freeze_sha256=digest(config), new_fits=0,
        new_simulations=0, original_reads=0, protected_reads=0, calibrated=False, scientific_decision='abstain'))
    _write_equal(root/output, encoded_result)
    return dict(rows=len(result['rows']), sha256=digest(encoded_result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'observed', 'generated'))
    print(run(Path.cwd(), parser.parse_args().action))
