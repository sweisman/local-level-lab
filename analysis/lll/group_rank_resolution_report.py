# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit the usable reference resolution without selecting a decision cutoff."""

import argparse
from collections import Counter
from contextlib import closing
import json
from pathlib import Path

from . import matched_generated_joint_score as source
from .group_rank_calibration import minimum_draws
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FOLDER = source.full.FOLDER
PLAN = FOLDER + 'GROUP_RANK_RESOLUTION_PLAN.md'
FREEZE = FOLDER + 'group-rank-resolution-freeze.json'
RESULT = FOLDER + 'group-rank-resolution-result.json'
GROUP_LEDGER = 'docs/analysis-provenance/ledger.json'


def _counts(study, rows):
    identities = {row['identity']: row['truth_model'] for row in rows}
    if (len(rows) != 12 or len(identities) != 12
            or set(study.tasks) != set(identities) or set(study.rows) != set(identities)):
        raise ValueError('twelve complete declared source cases required')
    counts = Counter()
    for identity, model in identities.items():
        payload = study.tasks[identity]['payload']
        outcome = study.envelope(identity)['result']
        if (payload['truth_model'] != model or outcome['passed'] is not True
                or outcome['all_candidates_converged'] is not True):
            raise ValueError('whole-group generating law or fit status differs')
        counts[model, payload['latitude_deg'], payload['height_profile'], payload['law']] += 1
    per_model = Counter()
    scenarios = []
    for (model, latitude, motion, law), count in sorted(counts.items()):
        per_model[model] += count
        scenarios.append(dict(truth_model=model, latitude_deg=latitude, height_profile=motion,
                              imu_law=law, observed_saved_draws=count,
                              smallest_possible_p_value=1 / (count + 1)))
    if per_model != Counter(dict.fromkeys(source.full.MODELS, 4)) or len(scenarios) != 12:
        raise ValueError('unexpected generated calibration cells')
    return scenarios, dict(per_model)


def run(root, action):
    inputs = {path: (root / path).read_bytes() for path in (source.FREEZE, source.RESULT, GROUP_LEDGER)}
    parent, result, ledger = (json.loads(inputs[path]) for path in
                              (source.FREEZE, source.RESULT, GROUP_LEDGER))
    if (result['freeze_sha256'] != digest(inputs[source.FREEZE])
            or any(result[key] != 0 for key in ('new_fits', 'new_seeds', 'original_reads', 'protected_reads'))):
        raise ValueError('sealed generated joint scores required')
    own = Path(__file__).relative_to(root).as_posix()
    config = encoded(dict(inputs={p: digest(value) for p, value in inputs.items()},
        sources={p: digest((root / p).read_bytes()) for p in source_closure(
            root, (own, PLAN, 'analysis/tests/test_group_rank_calibration.py'))},
        maximum_generated_tasks=12, fit_starts=0, native_calls=0, protected_reads=0,
        thresholds_are_illustrative=True, threads=1, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('rank resolution replay differs from frozen plan')
    with closing(ClosedStudy(root, 'data/' + source.parent.ID)) as study:
        if study.completion != parent['parent']:
            raise ValueError('original generating study differs')
        scenarios, per_model = _counts(study, result['rows'])
    cohort = {row['group_id'] for row in ledger['groups']
              if row['archive'] == 'esa' and row['role'] == 'protected_confirmation'}
    if len(cohort) != 7:
        raise ValueError('current published confirmation cohort required')
    limits = [dict(required_groups=k, per_group_alpha=.05 / (len(cohort) - k + 1),
                   all_available=minimum_draws(len(cohort), k, alpha=.05),
                   one_unavailable=minimum_draws(len(cohort), k, alpha=.05, unavailable=1))
              for k in (1, 3, 5, 7)]
    output = encoded(dict(freeze_sha256=digest(config), scenarios=scenarios, draws_by_model=per_model,
        hypothetical_p_floor_if_pooled=.2, pooling_justified=False,
        illustrative_resolution=limits, candidate_p_values_estimated=False,
        fit_starts=0, protected_reads=0, scientific_decision='abstain'))
    _write_equal(root / RESULT, output)
    return dict(sha256=digest(output), scenarios=len(scenarios), illustrative_resolution=limits)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
