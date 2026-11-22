# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test exact-objective calibration updates on the unchanged matched force windows."""

import argparse
from contextlib import closing
import gzip
import io
import json
from pathlib import Path

import numpy as np

from . import ilvis0_axis_force_pilot as pilot
from . import ilvis0_axis_force_pilot_report as prior_report
from . import ilvis0_exact_packet_calibration as solver
from .ilvis0_control_shards import _check_continue
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy

IDENTITY = 'ilvis0-exact-axis-force-v1-20261118'
ADAPTER = 'analysis/lll/ilvis0_exact_axis_force_pilot.py'
PLAN = pilot.SUPPORT.FOLDER+'EXACT_AXIS_FORCE_PLAN.md'
SCOPE = 'six bounded exact-objective calibration trials from each saved linear proposal'
TASKS = pilot.TASKS
SCORE_TOL_MPS2 = 1e-9


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/IDENTITY).exists():
        raise ValueError('inspect the existing exact calibration allowance')
    receipt = (root/prior_report.OUTPUT).read_bytes()
    earlier = json.loads(receipt)
    if earlier['tasks'] != TASKS or earlier['proposals'] != TASKS or earlier['navigation_fits']:
        raise ValueError('the complete archived linear calibration pilot is required')
    inputs = {'plan': PLAN}
    tasks = []

    def stage(key, raw):
        name = f'data/{IDENTITY}-inputs/{key}'
        pilot.SUPPORT._write_equal(root/name, raw)
        inputs[key] = name

    stage('parent-receipt.json', receipt)
    rows = {row['identity']: row for row in earlier['rows']}
    with closing(ClosedStudy(root, 'data/'+pilot.IDENTITY)) as study:
        if (study.completion != earlier['completion'] or study.completion['state'] != 'complete'
                or study.manifest['scope'] != pilot.SCOPE or not study.summary['passed']):
            raise ValueError('linear-pilot receipt no longer matches the sealed study')
        for identity, old in study.tasks.items():
            row, sealed = rows[identity], study.envelope(identity)['result']
            proposal = study.artifact(identity, 'training-proposal.json')
            if (not row['passed'] or row['proposal'] != proposal or not proposal['passed']
                    or any(row[side] != sealed[side] for side in ('training', 'later'))):
                raise ValueError('changed archived proposal or exact scores')
            for field in ('input_key', 'training_key', 'later_key'):
                key = old[field]
                if key not in inputs:
                    stage(key, study.input(key, raw=True))
            start_key = identity+'-start.json'
            stage(start_key, encoded(dict(correction=proposal['correction'],
                training=sealed['training'], later=sealed['later'], task_envelope_sha256=study.rows[identity]['artifact_sha256'])))
            tasks.append({**{k: v for k, v in old.items() if k not in ('index', 'shard')},
                          'start_key': start_key, 'trials': solver.MAX_TRIALS})
    if len(tasks) != TASKS or len(rows) != TASKS:
        raise ValueError('changed fixed calibration inventory')
    definition = dict(id=IDENTITY, scope=SCOPE, adapter=ADAPTER, inputs=inputs, tasks=tasks,
        workers=2, threads=1, maximum_wall_s=240.,
        sources=source_closure(root, (ADAPTER, PLAN, 'analysis/tests/test_ilvis0_exact_packet_calibration.py')))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study=IDENTITY, tasks=TASKS, maximum_trials=TASKS*solver.MAX_TRIALS,
                allocation=manifest['allocation'], parent_receipt_sha256=digest(receipt))


def evaluate(task, context):
    if (context.manifest['scope'] != SCOPE or task['trials'] != solver.MAX_TRIALS
            or task['coordinate_limits'] != pilot.LIMITS[task['box']]):
        raise ValueError('the original coordinates and finite exact-calibration settings are required')
    start = json.loads(context.input_path(task['start_key']).read_bytes())
    with np.load(io.BytesIO(gzip.decompress(context.input_path().read_bytes())), allow_pickle=False) as arrays:
        counts, elapsed, scale = arrays['counts'], arrays['elapsed'], float(arrays['scale'])
    if not 0 < len(counts) <= pilot.SUPPORT.MAX_PACKETS:
        raise ValueError('packet allowance exceeded')
    periods = (np.full(len(counts), .005), elapsed)
    training = pilot._side(context.input_path(task['training_key']).read_bytes(), periods)
    target = np.vstack([p for _, _, _, p in training])
    if len(target) != task['case_count']['training']:
        raise ValueError('changed earlier case count')
    context.save('exact-allowance.json', dict(initial_exact_evaluations=1, trials=task['trials'],
        maximum_exact_evaluations=task['trials']+3, navigation_fits=0))

    def assess(point):
        _check_continue(context.root, context.manifest)
        pairs = [solver.exact_terms(counts, dt, scale, slices, point, count_error=pilot.SUPPORT.COUNT_ERROR)
                 for dt, slices, _, _ in training]
        return np.vstack([pair[0] for pair in pairs]), np.vstack([pair[1] for pair in pairs])

    def reserve(index):
        _check_continue(context.root, context.manifest)
        context.save(f'charge-{index:02d}.json', dict(trials=1, index=index,
            maximum_iterations=solver.LP_ITERATIONS, maximum_seconds=solver.LP_SECONDS))

    def audit(trial):
        context.save(f'trial-{trial["index"]:02d}.json', trial)

    result = solver.refine(start['correction'], task['coordinate_limits'], target, assess,
        reserve=reserve, save=audit, trials=task['trials'])
    if abs(start['training']['maximum_gap_mps2']-result['initial_gap_mps2']) > SCORE_TOL_MPS2:
        raise ValueError('the exact initial objective does not match the sealed original score')
    point = result['correction']
    _check_continue(context.root, context.manifest)
    earlier = pilot._score(counts, scale, training, point)
    if abs(earlier['maximum_gap_mps2']-result['gap_mps2']) > SCORE_TOL_MPS2:
        raise ValueError('independent final packet score disagrees with the exact update objective')
    context.save('training-final.json', result)
    _check_continue(context.root, context.manifest)
    later = pilot._score(counts, scale, pilot._side(context.input_path(task['later_key']).read_bytes(), periods), point)
    if later['cases'] != task['case_count']['later']:
        raise ValueError('changed later case count')
    return dict(passed=result['stop_reason'] != 'linear_failure', training=earlier, later=later,
        original_training=start['training'], original_later=start['later'],
        navigation_fits=0, accepted_trials=result['accepted_trials'], charged_trials=result['charged_trials'],
        stop_reason=result['stop_reason'], scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare',))
    parser.parse_args()
    print(json.dumps(prepare(Path.cwd()), sort_keys=True))
