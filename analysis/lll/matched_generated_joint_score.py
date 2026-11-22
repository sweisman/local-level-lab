# SPDX-License-Identifier: AGPL-3.0-or-later
"""Joint predictive ranking of the three sealed fits on known-model histories."""

import argparse
from contextlib import closing
import json
from pathlib import Path

import numpy as np

from . import esa_changing_drift_transfer as full
from . import esa_no_snap_ablation as reduced
from . import matched_candidate_generated_study as parent
from .airquantumgrav_error_policy import build, reported_covariance
from .airquantumgrav_scoring import receiver_errors as coordinate_errors
from .airquantumgrav_weighted_controls import fixture_rows
from .esa_joint_path_score import joint_score
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .measurement_noise import receiver_errors
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = full.FOLDER+'MATCHED_GENERATED_JOINT_SCORE_PLAN.md'
FREEZE = full.FOLDER+'matched-generated-joint-score-freeze.json'
RESULT = full.FOLDER+'matched-generated-joint-score-result.json'
PRIOR = full.FOLDER+'matched-candidates-full-result.json'
CUT, FUTURE = 79, 40
LAWS = ('full', 'reduced')


def rank_models(scores):
    more, less, disc = (scores[key] for key in full.MODELS)
    globe = min(more, less)
    if disc < globe:
        return dict(shape='disc', preferred_model='flat_still')
    if disc == globe:
        return dict(shape='tie', preferred_model=None)
    preferred = 'sphere_rotating' if more < less else 'sphere_still' if less < more else None
    return dict(shape='globe', preferred_model=preferred)


def _later_reference(study, identity, training, times, comparison):
    truth = np.asarray(study.artifact(identity, 'scoring-observations.json')['coordinates'])
    noise = study.artifact(identity, 'noise-binding.json')
    clean = fixture_rows(truth[:CUT], times[:CUT])
    weights = build(clean, policy_id='reported-short-v1')
    if (weights.source_sha256 != noise['receiver_covariance_source_sha256']
            or noise['receiver_policy']['policy_id'] != 'reported-short-v1'):
        raise ValueError('original generated receiver noise binding changed')
    transforms = np.concatenate((weights.transforms, np.repeat(weights.transforms[-1:], FUTURE, axis=0)))
    generated_error = receiver_errors(times, weights.spec, seed=noise['settings']['seed'],
                                      maximum_epochs=len(times), transforms=transforms)
    regenerated = truth+generated_error
    if not np.allclose(full._coordinates(training), regenerated[:CUT], rtol=0., atol=[2e-13,2e-13,1e-7]):
        raise ValueError('original seeded GPS prefix does not reproduce')
    observed = regenerated[CUT:]
    for model in full.MODELS:
        diagnostic = study.artifact(identity, f'candidates/{model}/receiver-forecast-error-diagnostic.json')
        errors = coordinate_errors(diagnostic['fixed_parameters']['mean'], observed)
        horizontal = float(np.sqrt(np.mean(np.sum(errors[:, :2]**2, axis=1))))
        if not np.isclose(horizontal, comparison['receiver_target'][model]['point_horizontal_rms_m'],
                          rtol=1e-9, atol=1e-7):
            raise ValueError('original generated GPS score does not reproduce')
    return observed


def _case(study, identity):
    training = study.artifact(identity, 'training-receiver.json')
    binding = study.artifact(identity, 'input-binding.json')
    if (len(training) != CUT or digest(encoded(training)) != binding['earlier_receiver_sha256']
            or binding['same_measurements_for_all_candidates'] is not True):
        raise ValueError('same earlier receiver input required for every candidate')
    early = full._coordinates(training)
    gps = full._chart(early, early[0])
    paths = {model:study.artifact(identity, f'candidates/{model}/forecast.json') for model in full.MODELS}
    times = paths[full.MODELS[0]]['times_s']
    if (len(times) != CUT+FUTURE or any(row['times_s'] != times or row['training_epochs'] != CUT
            or row['prediction_epochs'] != FUTURE or row['prediction_receiver_positions_used'] is not False
            for row in paths.values())):
        raise ValueError('original forecast query support and no-later-data boundary required')
    cov = np.linalg.cholesky(np.asarray([reported_covariance(r) for r in training]))
    reported = np.concatenate((cov, np.repeat(cov[-1:], FUTURE, axis=0)))
    fixed = np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3))
    operators = {law:{key:make(times, weight) for key,weight in zip(full.WEIGHTS,(fixed,reported),strict=True)}
                 for law,make in zip(LAWS,(full.operator,reduced.no_snap_operator),strict=True)}
    centers = {}
    for model, row in paths.items():
        path = full._chart(row['coordinates'], early[0])
        centers[model] = {law:{key:full.condition(op,path[:CUT]-gps,path[CUT:])['center_m']
                              for key,op in weights.items()} for law,weights in operators.items()}
    forward_sha = digest(encoded(centers))
    comparison = study.artifact(identity, 'matched-comparison.json')
    if (comparison['input_binding'] != binding or comparison['later_observations_opened_after_all_bounds'] is not True
            or any(not comparison['convergence'][m] for m in full.MODELS)):
        raise ValueError('same closed three-candidate fits required')
    later = full._chart(_later_reference(study, identity, training, np.asarray(times), comparison), early[0])
    scores = {}
    for law, weights in operators.items():
        scores[law] = {}
        for key, op in weights.items():
            rows = {m:joint_score(op, CUT, np.asarray(centers[m][law][key])-later,
                                 horizons=(FUTURE,))[str(FUTURE)] for m in full.MODELS}
            scores[law][key] = dict(models=rows, **rank_models({m:r['squared_standardized_error']
                                                             for m,r in rows.items()}))
    return dict(identity=identity, scores=scores, earlier_only_centers_sha256=forward_sha)


def run(root, action):
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        prior_raw = (root/PRIOR).read_bytes()
        prior = json.loads(prior_raw)
        if (study.manifest['scope'] != parent.SCOPE or study.completion['state'] != 'complete'
                or study.completion['manifest_sha256'] != prior['manifest_sha256']
                or study.completion['summary_sha256'] != prior['summary_sha256']
                or prior['candidate_fits_converged'] != 36 or len(study.rows) != 12
                or set(prior['cases']) != set(study.tasks) or set(study.tasks) != set(study.rows)):
            raise ValueError('unchanged twelve-case generated source required')
        own = Path(__file__).relative_to(root).as_posix()
        test = 'analysis/tests/test_matched_generated_joint_score.py'
        config = encoded(dict(sources={p:digest((root/p).read_bytes()) for p in source_closure(root,(own,PLAN,test))},
            parent=study.completion, prior_sha256=digest(prior_raw), training_epochs=CUT, later_epochs=FUTURE,
            maximum_operators=48, maximum_scores=144, maximum_seeded_receiver_replays=12,
            threads=1, fit_starts=0, environment=runtime_environment()))
        if action == 'freeze':
            _write_equal(root/FREEZE, config)
            return dict(freeze_sha256=digest(config))
        if (root/FREEZE).read_bytes() != config:
            raise ValueError('unchanged joint known-model freeze required')
        results = []
        for identity in sorted(study.tasks):
            if study.envelope(identity)['result']['all_candidates_converged'] is not True:
                raise ValueError('closed generating case differs')
            row = _case(study, identity)
            results.append(dict(row, truth_model=study.tasks[identity]['payload']['truth_model']))
    raw = encoded(dict(freeze_sha256=digest(config), rows=results, new_fits=0, new_seeds=0,
                       original_reads=0, protected_reads=0, scientific_decision='abstain'))
    _write_equal(root/RESULT, raw)
    return dict(rows=len(results), sha256=digest(raw))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze','replay'))
    print(run(Path.cwd(), parser.parse_args().action))
