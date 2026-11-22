# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit every exact calibration step, its charge and its fixed later score."""

from contextlib import closing
import json
from pathlib import Path

from . import ilvis0_exact_axis_force_pilot as pilot
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy

OUTPUT = pilot.pilot.SUPPORT.FOLDER+'exact-axis-force-receipt.json'


def report(root):
    rows = []
    with closing(ClosedStudy(root, 'data/'+pilot.IDENTITY)) as study:
        if (study.manifest['scope'] != pilot.SCOPE or study.summary['total'] != pilot.TASKS
                or study.summary['completed'] != pilot.TASKS or any(study.summary['charged'].values())):
            raise ValueError('the closed fixed exact calibration study is required')
        for identity, task in study.tasks.items():
            envelope = study.envelope(identity)
            result, files = envelope['result'], envelope['artifacts']
            row = {key: task[key] for key in ('identity', 'imu_type', 'model', 'degree', 'box')}
            row.update(result)
            count = sum(f'artifacts/{identity}/charge-{i:02d}.json' in files
                        for i in range(1, task['trials']+1))
            row['charges'] = count
            audits = []
            for index in range(1, count+1):
                expected = dict(trials=1, index=index, maximum_iterations=pilot.solver.LP_ITERATIONS,
                                maximum_seconds=pilot.solver.LP_SECONDS)
                if study.artifact(identity, f'charge-{index:02d}.json') != expected:
                    raise ValueError('changed exact calibration trial charge')
                if f'artifacts/{identity}/trial-{index:02d}.json' in files:
                    audits.append(study.artifact(identity, f'trial-{index:02d}.json'))
            if result['passed']:
                final = study.artifact(identity, 'training-final.json')
                start = study.input(task['start_key'])
                point, current = start['correction'], final['initial_gap_mps2']
                accepted = 0
                for index, trial in enumerate(audits, 1):
                    if (not trial['solved'] or trial['iterations'] > pilot.solver.LP_ITERATIONS
                            or trial['index'] != index or trial['before_gap_mps2'] != current):
                        raise ValueError('invalid exact trial chain')
                    fresh = trial['exact_gap_mps2']
                    if trial['accepted'] != (fresh < current-pilot.solver.IMPROVEMENT_MPS2):
                        raise ValueError('trial does not follow the exact acceptance rule')
                    if trial['accepted']:
                        point, current = trial['point'], fresh
                        accepted += 1
                if (count != len(audits) or count != final['charged_trials']
                        or count != result['charged_trials'] or accepted != final['accepted_trials']
                        or accepted != result['accepted_trials'] or point != final['correction']
                        or current != final['gap_mps2'] or result['navigation_fits']
                        or abs(result['training']['maximum_gap_mps2']-current) > pilot.SCORE_TOL_MPS2
                        or abs(start['training']['maximum_gap_mps2']-final['initial_gap_mps2']) > pilot.SCORE_TOL_MPS2
                        or any(result[side]['cases'] != task['case_count'][side] for side in ('training', 'later'))
                        or any(abs(x)>b+1e-12 for x,b in zip(point, task['coordinate_limits'], strict=True))):
                    raise ValueError('invalid final calibration or held-out score')
                row['calibration'] = final
            rows.append(row)
        return dict(completion=study.completion, tasks=len(rows), rows=rows,
                    trials=sum(r['charges'] for r in rows),
                    navigation_fits=0, scientific_decision='abstain')


if __name__ == '__main__':
    root = Path.cwd()
    value = report(root)
    pilot.pilot.SUPPORT._write_equal(root/OUTPUT, encoded(value))
    print(json.dumps(dict(tasks=value['tasks'], trials=value['trials'],
        passed=sum(row['passed'] for row in value['rows']))))
