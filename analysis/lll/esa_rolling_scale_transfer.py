# SPDX-License-Identifier: AGPL-3.0-or-later
"""Same-flight transfer of whole-path error scale from sealed ESA forecasts."""

import argparse
from contextlib import ExitStack, closing
import gzip
import json
import math
from pathlib import Path

import numpy as np

from . import esa_rolling_origin_200_study as early_study
from . import esa_rolling_origin_400_study as late_study
from . import joint_score_abstention as rule
from .airquantumgrav_error_policy import reported_covariance
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FULL = rule.full
FOLDER = FULL.FOLDER
PLAN = FOLDER + 'ESA_ROLLING_SCALE_TRANSFER_PLAN.md'
FREEZE = FOLDER + 'esa-rolling-scale-transfer-freeze.json'
EARLIER = FOLDER + 'esa-rolling-scale-transfer-earlier.json'
RESULT = FOLDER + 'esa-rolling-scale-transfer-result.json'
EARLY_CUT = 200
COORDINATES = 3 * FULL.LATER


def transfer(earlier, later, *, coordinates):
    if (type(coordinates) is not int or coordinates < 1 or not math.isfinite(earlier)
            or earlier <= 0.0 or not math.isfinite(later) or later < 0.0):
        raise ValueError('finite nonnegative energies and a positive earlier scale required')
    ratio = later / earlier
    if not math.isfinite(ratio):
        raise ValueError('unrepresentable scale transfer')
    return dict(earlier_variance_multiplier=earlier / coordinates,
                later_variance_multiplier=later / coordinates,
                later_to_earlier_variance_ratio=ratio,
                later_rms_after_earlier_scaling=math.sqrt(ratio))


def _check_source(early, late):
    parents = [study.input('parent_identity') for study in (early, late)]
    if (parents[0] != parents[1] or parents[0]['source_id'] != 'esa-99f1530c3eda4318'
            or early.manifest['scope'] != early_study.SCOPE
            or late.manifest['scope'] != late_study.SCOPE
            or any(study.completion['state'] != 'complete'
                   or set(study.tasks) != set(late_study.LAWS)
                   for study in (early, late))):
        raise ValueError('two completed prefixes from the opened ESA flight required')
    return parents[0]


def _rows(study):
    return json.loads(gzip.decompress(study.input('training', raw=True)))


def _score(study, receiver_rows, cut):
    times = study.input('forecast_times')
    n = cut + FULL.LATER
    if len(times) != n or len(receiver_rows) != n or _rows(study) != receiver_rows[:cut]:
        raise ValueError('same receiver prefix and exact later support required')
    binding = study.input('saved-input-binding')
    earlier = receiver_rows[:cut]
    if [row['time_s'] - binding['time_origin_s'] for row in receiver_rows] != times:
        raise ValueError('receiver epochs differ from sealed forecast times')
    coords = FULL._coordinates(receiver_rows)
    metric = FULL._chart(coords, coords[0])
    fixed = np.broadcast_to(np.eye(3) * FULL.POLICY['receiver_white_std_m'], (n, 3, 3))
    loaded = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in earlier]))
    reported = np.concatenate((loaded, np.repeat(loaded[-1:], FULL.LATER, axis=0)))
    operators = {f'{name}/{weight}': make(times, loading)
                 for name, make in zip(rule.observed.LAWS, (FULL.operator, rule.reduced.no_snap_operator),
                                       strict=True)
                 for weight, loading in zip(FULL.WEIGHTS, (fixed, reported), strict=True)}
    by_law = {}
    for law in late_study.LAWS:
        receipt = study.envelope(law)['result']
        forecast = study.artifact(law, 'forecast.json')
        if (receipt['passed'] is not True or receipt['later_receiver_positions_used'] is not False
                or forecast['training_epochs'] != cut or forecast['prediction_epochs'] != FULL.LATER
                or forecast['times_s'] != times or np.shape(forecast['coordinates']) != (n, 3)
                or forecast['prediction_receiver_positions_used'] is not False):
            raise ValueError('unchanged earlier-only forecasting artifact required')
        path = FULL._chart(forecast['coordinates'], coords[0])
        errors = path - metric
        by_law[law] = {}
        for arm, operator in operators.items():
            conditioned = FULL.condition(operator, errors[:cut], path[cut:])
            score = rule.observed.joint_score(operator, cut,
                np.asarray(conditioned['center_m']) - metric[cut:], horizons=(FULL.LATER,))
            by_law[law][arm] = score[str(FULL.LATER)]['squared_standardized_error']
    return dict(scores=by_law, operators={arm: op.configuration for arm, op in operators.items()})


def _later_reports(root, frozen):
    raw = {path: (root / path).read_bytes() for path in frozen}
    if {path: digest(value) for path, value in raw.items()} != frozen:
        raise ValueError('sealed later score source changed')
    files = {path: json.loads(value) for path, value in raw.items()}
    observed = files[rule.observed.OBSERVED]
    if observed['recording'] != 187 or len(observed['settings']) != 4:
        raise ValueError('the four settings from the opened ESA flight are required')
    return files


def _matched_matrix(files, earlier):
    by_law = {name: {row['identity']: row for row in files[path]['rows']}
              for name, path in zip(rule.observed.LAWS, (FULL.RESULT, rule.reduced.RESULT), strict=True)}
    results = []
    for row, selected in zip(files[rule.observed.OBSERVED]['settings'],
                             files[FULL.RESULT]['matched_settings'], strict=True):
        law = row['imu_law']
        if (row['profile'], law, row['complete']) != (selected['profile'], selected['law'],
                                                      selected['complete']):
            raise ValueError('matched-model setting receipt differs')
        if row['complete'] is not True:
            results.append(dict(profile=row['profile'], imu_law=law, status='incomplete'))
            continue
        scores = {model: {f'{name}/{key}': value['scores'][model]
                          for name, arms in row['scores'].items() for key, value in arms.items()}
                  for model in FULL.MODELS}
        physical = {model: {f'{name}/{weight}': by_law[name][identity]['horizons'][
            str(FULL.LATER)]['ranges'][weight]['descriptive_accuracy_passed']
            for name in rule.observed.LAWS for weight in FULL.WEIGHTS}
            for model, identity in selected['primary'].items()}
        scales = {arm: q / COORDINATES for arm, q in earlier[law].items()}
        scaled = {model: {arm: q / scales[arm] for arm, q in arms.items()}
                  for model, arms in scores.items()}
        results.append(dict(profile=row['profile'], imu_law=law, status='complete',
            reference_check=rule.assess(scaled, epochs=FULL.LATER, physical=physical),
            specified_field_transfer={arm: transfer(earlier[law][arm], q, coordinates=COORDINATES)
                for arm, q in scores['sphere_rotating'].items()}))
    if sum(row['status'] == 'complete' for row in results) != 2:
        raise ValueError('exact two complete matched-model settings required')
    return results


def run(root, action):
    with ExitStack() as stack:
        store = stack.enter_context(closing(ArchiveStore(root)))
        early, late = [stack.enter_context(closing(ClosedStudy(root, 'data/' + ref.ID, store=store)))
                       for ref in (early_study, late_study)]
        parent_identity = _check_source(early, late)
        own = Path(__file__).relative_to(root).as_posix()
        required = (rule.observed.OBSERVED, FULL.RESULT, rule.reduced.RESULT)
        prior_seal = json.loads((root / rule.FREEZE).read_bytes())
        definition = encoded(dict(
            sources={p: digest((root / p).read_bytes()) for p in source_closure(
                root, (own, PLAN, 'analysis/tests/test_esa_rolling_scale_transfer.py'))},
            forecast_studies=[early.completion, late.completion], parent=parent_identity,
            later_inputs={path: prior_seal['inputs'][path] for path in required},
            threads=1, environment=runtime_environment(), operators=8, scores=16,
            fit_starts=0, native_calls=0, protected_reads=0))
        if action == 'freeze':
            _write_equal(root / FREEZE, definition)
            return dict(freeze_sha256=digest(definition))
        if (root / FREEZE).read_bytes() != definition:
            raise ValueError('scale transfer replay differs from frozen plan')
        if action == 'estimate':
            # The 400-fit training input contains every early scoring epoch
            # and stops before any later scoring epoch.
            earlier = _score(early, _rows(late)[:EARLY_CUT + FULL.LATER], EARLY_CUT)
            for arms in earlier['scores'].values():
                for energy in arms.values():
                    transfer(energy, energy, coordinates=COORDINATES)
            value = encoded(dict(**earlier, freeze_sha256=digest(definition),
                                 later_scores_opened=False, earlier_cut=EARLY_CUT))
            _write_equal(root / EARLIER, value)
            return dict(sha256=digest(value), earlier_scores=earlier['scores'])
        raw = (root / EARLIER).read_bytes()
        earlier = json.loads(raw)
        if earlier['freeze_sha256'] != digest(definition) or earlier['later_scores_opened'] is not False:
            raise ValueError('sealed earlier-only scale estimates required')
        files = _later_reports(root, json.loads(definition)['later_inputs'])
        parent = stack.enter_context(closing(ClosedStudy(root, FULL.PARENT, store=store)))
        if any(parent.completion[key] != parent_identity[key] for key in
               ('manifest_sha256', 'summary_sha256')):
            raise ValueError('sealed later scoring receiver source differs')
        records = _rows(parent)[:FULL.CUT + FULL.LATER]
        receiver_sha = digest(encoded(records[FULL.CUT:]))
        if any(files[path]['later_receiver_sha256'] != receiver_sha
               for path in (FULL.RESULT, rule.reduced.RESULT)):
            raise ValueError('matched comparisons must use the same later receiver rows')
        later = _score(late, records, FULL.CUT)
        matched = {law: {arm: transfer(earlier['scores'][law][arm], value, coordinates=COORDINATES)
                         for arm, value in arms.items()}
                   for law, arms in later['scores'].items()}
        matrix = _matched_matrix(files, earlier['scores'])
        value = encoded(dict(freeze_sha256=digest(definition), earlier_sha256=digest(raw),
            later=later, matched_zero_removal=matched, matched_model_reference=matrix,
            original_reads=0, new_fits=0, protected_reads=0, calibrated=False,
            scientific_decision='abstain'))
        _write_equal(root / RESULT, value)
        return dict(sha256=digest(value), matched_ratios={law: [
            row['later_to_earlier_variance_ratio'] for row in arms.values()]
            for law, arms in matched.items()}, provisional_shape=[row['reference_check']['shape']
            for row in matrix if row['status'] == 'complete'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'estimate', 'compare'))
    print(run(Path.cwd(), parser.parse_args().action))
