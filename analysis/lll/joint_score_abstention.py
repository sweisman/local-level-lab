# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conservative research rule for joint forecast adequacy and abstention."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from scipy.stats import chi2

from . import esa_changing_drift_transfer as full
from . import esa_joint_path_score as observed
from . import esa_no_snap_ablation as reduced
from . import matched_generated_joint_score as development
from . import matched_one_sided_geometry_study as routes
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = full.FOLDER+'JOINT_SCORE_ABSTENTION_PLAN.md'
FREEZE = full.FOLDER+'joint-score-abstention-freeze.json'
RESULT = full.FOLDER+'joint-score-abstention-result.json'
ROUTE_RESULT = full.FOLDER+'matched-one-sided-geometry-result.json'
ARMS = tuple(f'{law}/{weight}' for law in observed.LAWS for weight in full.WEIGHTS)
CENTRAL_MASS = .95


def assess(scores, *, epochs, physical=None):
    """Keep each candidate that is compatible under any declared error law."""
    if type(epochs) is not int or epochs < 1:
        raise ValueError('complete later epoch count required')
    dof = 3*epochs
    tail = (1.-CENTRAL_MASS)/2.
    lower, upper = (float(v) for v in chi2.ppf((tail, 1.-tail), dof))
    result = dict(shape='abstain', field='abstain', shape_reason='incomplete',
                  reference_dof=dof, reference_band=[lower, upper],
                  compatible_models=[], adequate_models=[], by_model={})
    if set(scores) != set(full.MODELS) or any(set(arms) != set(ARMS) for arms in scores.values()):
        return result
    if physical is not None and (set(physical) != set(full.MODELS)
            or any(set(arms) != set(ARMS) or any(type(v) is not bool for v in arms.values())
                   for arms in physical.values())):
        raise ValueError('the same fixed position-accuracy screen must cover all candidates and arms')
    for model in full.MODELS:
        arms = scores[model]
        if any(type(v) not in (int,float) or not math.isfinite(v) or v < 0. for v in arms.values()):
            raise ValueError('finite nonnegative squared standardized error required')
        compatible = [a for a in ARMS if arms[a] <= upper]
        adequate = [a for a in compatible if arms[a] >= lower and (physical is None or physical[model][a])]
        if compatible:
            result['compatible_models'].append(model)
        if adequate:
            result['adequate_models'].append(model)
        result['by_model'][model] = dict(compatible_arms=compatible, adequate_arms=adequate)
    rotating, still, disc = full.MODELS
    stands = set(result['compatible_models'])
    adequate = set(result['adequate_models'])
    globe = stands & {rotating,still}
    if not stands:
        result['shape_reason'] = 'no_compatible_candidate'
    elif globe and disc in stands:
        result['shape_reason'] = 'both_families_compatible'
    elif not adequate:
        result['shape_reason'] = 'no_adequate_candidate'
    elif not globe:
        result.update(shape='disc', shape_reason='one_compatible_family')
    else:
        result.update(shape='globe', shape_reason='one_compatible_family')
        if len(globe)==1:
            result['field'] = 'specified' if rotating in globe else 'zero'
    return result


def _generated(sources):
    answer = []
    for row in sources:
        energies = {model:{f'{law}/{key}':arm['models'][model]['squared_standardized_error']
                           for law,by_law in row['scores'].items() for key,arm in by_law.items()}
                    for model in full.MODELS}
        truth = row['truth_model']
        verdict = assess(energies, epochs=development.FUTURE)
        truth_shape = 'disc' if truth == 'flat_still' else 'globe'
        answer.append(dict(identity=row['identity'], truth_model=truth, truth_shape=truth_shape,
                           scores=energies, **verdict))
    return answer


def _observed(prior, full_scores, reduced_scores):
    results = []
    files = {law:{r['identity']:r for r in receipt['rows']}
             for law,receipt in zip(observed.LAWS, (full_scores,reduced_scores), strict=True)}
    for setting, primary in zip(prior['settings'], full_scores['matched_settings'], strict=True):
        if (setting['complete'],setting['profile'],setting['imu_law']) != (
                primary['complete'],primary['profile'],primary['law']):
            raise ValueError('same frozen earlier-selected starts required')
        energies, physical = {}, {}
        if setting['complete']:
            for m, identity in primary['primary'].items():
                energies[m] = {f'{law}/{key}':arm['scores'][m] for law,by_law in setting['scores'].items()
                               for key,arm in by_law.items()}
                physical[m] = {f'{law}/{key}':files[law][identity]['horizons']['120']['ranges'][key][
                               'descriptive_accuracy_passed'] for law in observed.LAWS for key in full.WEIGHTS}
        results.append(dict(profile=setting['profile'], imu_law=setting['imu_law'],
            **assess(energies, epochs=full.LATER, physical=physical)))
    return results


def run(root, action):
    with closing(ClosedStudy(root,'data/'+routes.ID)) as study:
        paths = (development.RESULT, observed.OBSERVED, full.RESULT, reduced.RESULT, ROUTE_RESULT)
        raw = {p:(root/p).read_bytes() for p in paths}
        saved = {p:json.loads(v) for p,v in raw.items()}
        route_report = saved[ROUTE_RESULT]
        if (study.manifest['scope'] != routes.SCOPE or study.completion['state'] != 'complete'
                or route_report['manifest_sha256'] != study.completion['manifest_sha256']
                or route_report['summary_sha256'] != study.completion['summary_sha256']
                or route_report['candidate_fits_converged'] != 6 or len(study.rows) != 2
                or set(study.tasks) != set(study.rows) or set(study.rows) != set(route_report['cases'])
                or len({r['payload']['seed'] for r in study.tasks.values()}) != 1
                or {r['payload']['truth_model'] for r in study.tasks.values()} != {'sphere_rotating'}):
            raise ValueError('exact separate paired route controls required')
        own = Path(__file__).relative_to(root).as_posix()
        test = 'analysis/tests/test_joint_score_abstention.py'
        config = encoded(dict(sources={p:digest((root/p).read_bytes()) for p in source_closure(root,(own,PLAN,test))},
            inputs={p:digest(v) for p,v in raw.items()}, route_completion=study.completion,
            central_reference_mass=CENTRAL_MASS, maximum_new_operators=8, maximum_joint_evaluations=24,
            maximum_seeded_receiver_reconstructions=2, threads=1, fit_starts=0, environment=runtime_environment()))
        if action == 'freeze':
            _write_equal(root/FREEZE, config)
            return dict(freeze_sha256=digest(config))
        if (root/FREEZE).read_bytes() != config:
            raise ValueError('changed predeclared decision rule freeze')
        initial = saved[development.RESULT]['rows']
        if len(initial)!=12 or len(saved[observed.OBSERVED]['settings'])!=4:
            raise ValueError('unchanged development denominators required')
        control = [dict(development._case(study, identity),truth_model=study.tasks[identity]['payload']['truth_model'])
                   for identity in sorted(study.tasks)]
        result = dict(development=_generated(initial), paired_routes=_generated(control),
            observed=_observed(saved[observed.OBSERVED], saved[full.RESULT], saved[reduced.RESULT]),
            freeze_sha256=digest(config), new_fits=0, new_seeds=0, original_reads=0, protected_reads=0,
            calibrated=False, scientific_decision='abstain')
    payload = encoded(result)
    _write_equal(root/RESULT, payload)
    return dict(sha256=digest(payload), cases={key:len(result[key]) for key in ('development','paired_routes','observed')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','replay'))
    print(run(Path.cwd(),parser.parse_args().action))
