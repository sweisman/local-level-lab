# SPDX-License-Identifier: AGPL-3.0-or-later
"""Paired earlier-only backcheck of the ESA ablation on sealed simulations."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

import numpy as np

from . import esa_changing_drift_transfer as transfer
from . import esa_no_snap_ablation as ablation
from . import esa_threshold_42_validation as generated
from .esa_threshold_42_report import summarize
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = transfer.FOLDER+'ESA_NO_SNAP_GENERATED_BACKCHECK_PLAN.md'
FREEZE = transfer.FOLDER+'esa-no-snap-generated-backcheck-freeze.json'
RESULT = transfer.FOLDER+'esa-no-snap-generated-backcheck-result.json'


def standardized_maximum(forecast, later):
    center, sigma = (np.asarray(forecast[k], float) for k in ('center_m', 'sigma_m'))
    later = np.asarray(later, float)
    if (center.shape != later.shape or sigma.shape != later.shape or not len(later)
            or later.shape[1:] != (3,) or np.any(sigma <= 0.)
            or any(not np.isfinite(v).all() for v in (later, center, sigma))
            or forecast['later_receiver_positions_used'] is not False):
        raise ValueError('finite scores for sealed earlier-only ranges required')
    # The range was constructed in residual space against a raw zero path.
    return float(np.max(abs(later+center)/sigma))


def _build(study, policy, prior):
    early, future = policy['training_epochs'], policy['forecast_epochs']
    epoch_count = early+future
    weights = np.broadcast_to(np.eye(3)*transfer.POLICY['receiver_white_std_m'], (epoch_count, 3, 3))
    op = ablation.no_snap_operator(np.arange(epoch_count, dtype=float), weights)
    threshold = policy['simultaneous_z']
    rows = []
    for task, original in zip(generated.tasks(), prior['rows'], strict=True):
        identity = task['identity']
        seed, vibration = (task['payload'][key] for key in ('seed','vibration'))
        if (study.rows[identity]['passed'] is not True or original['technical_pass'] is not True
                or original['seed'] != seed or original['vibration'] is not vibration):
            raise ValueError('unchanged original generated cohort required')
        saved = study.artifact(identity, 'conditional-forecast.json')
        if (saved['later_receiver_positions_used'] is not False or saved['training_epochs'] != early
                or saved['forecast_epochs'] != future):
            raise ValueError('unchanged generated training split required')
        ranges = transfer.condition(op, saved['earlier_residual_neu_m'], np.zeros((future, 3)))
        foresight_sha = digest(encoded(ranges))
        score = study.artifact(identity, 'outcome.json')
        if (score['seed'] != seed or score['vibration'] is not vibration or score['threshold_z'] != threshold
                or score['generated_case_policy_sha256'] != policy['generated_case_policy_sha256']):
            raise ValueError('changed generated scoring material')
        later = np.asarray(score['later_residual_neu_m'])
        original_forecast = dict(center_m=-np.asarray(saved['future_mean_neu_m']),
            sigma_m=saved['future_sigma_neu_m'], later_receiver_positions_used=False)
        baseline = standardized_maximum(original_forecast, later)
        if (not math.isclose(baseline, original['maximum_absolute_standardized_error'], rel_tol=1e-12)
                or not math.isclose(baseline, score['maximum_absolute_standardized_error'], rel_tol=1e-12)
                or (baseline <= threshold) != original['range_contained']):
            raise ValueError('saved generated scores do not reproduce')
        maximum = standardized_maximum(ranges, later)
        rows.append(dict(seed=seed, vibration=vibration, technical_pass=True,
            maximum_absolute_standardized_error=maximum, range_contained=maximum<=threshold,
            endpoint_half_width_m=float(np.median(ranges['sigma_m'][-1])*threshold),
            original_range_contained=original['range_contained'],
            original_maximum_absolute_standardized_error=baseline, earlier_only_range_sha256=foresight_sha))
    result = summarize(rows)
    result['same_gate_would_pass'] = result.pop('generated_gate_passed')
    for group in result['strata']:
        subset = [row for row in rows if row['vibration'] is group['vibration']]
        group.update(new_misses=sum(r['original_range_contained'] and not r['range_contained'] for r in subset),
                     corrected_misses=sum(not r['original_range_contained'] and r['range_contained'] for r in subset))
    return dict(result, rows=rows, qualified=False, original_reads=0, protected_reads=0, fit_starts=0,
                new_simulations=0, scientific_decision='abstain')


def run(root, action):
    with closing(ClosedStudy(root, 'data/'+generated.ID)) as study:
        prior_raw = (root/(generated.HERE+'/RESULT.json')).read_bytes()
        prior = json.loads(prior_raw)
        policy_raw = study.input('policy', raw=True)
        policy = json.loads(policy_raw)
        if (study.completion['state'] != 'complete' or prior['manifest_sha256'] != study.completion['manifest_sha256']
                or len(study.tasks) != len(study.rows) or len(study.rows) != len(generated.tasks())
                or prior['study_id'] != generated.ID or prior['generated_gate_passed'] is not True
                or prior['policy_sha256'] != digest(policy_raw) or policy != generated.POLICY):
            raise ValueError('verified original generated cohort required')
        own = Path(__file__).relative_to(root).as_posix()
        test = 'analysis/tests/test_esa_no_snap_generated_backcheck.py'
        config = encoded(dict(sources={p:digest((root/p).read_bytes()) for p in source_closure(root, (own, PLAN, test))},
            completion=study.completion, original_report_sha256=digest(prior_raw), policy_sha256=digest(policy_raw),
            snap_psd=0., histories=len(prior['rows']), operators=1, threshold=policy['simultaneous_z'],
            fit_starts=0, threads=1, new_simulations=0, environment=runtime_environment()))
        if action == 'freeze':
            _write_equal(root/FREEZE, config)
            return dict(freeze_sha256=digest(config))
        if (root/FREEZE).read_bytes() != config:
            raise ValueError('changed generated no-snap freeze')
        result = _build(study, policy, prior)
    content = encoded(dict(result, freeze_sha256=digest(config)))
    _write_equal(root/RESULT, content)
    return dict(strata=result['strata'], sha256=digest(content))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
