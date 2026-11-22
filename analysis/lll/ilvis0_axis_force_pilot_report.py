# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report shared axis-calibration proposals and their saved nonlinear checks."""

from contextlib import closing
import json
from pathlib import Path

from . import ilvis0_axis_force_pilot as pilot
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy

OUTPUT = pilot.SUPPORT.FOLDER+'axis-force-pilot-receipt.json'


def report(root):
    rows = []
    with closing(ClosedStudy(root, 'data/'+pilot.IDENTITY)) as study:
        if (study.manifest['scope'] != pilot.SCOPE or study.summary['total'] != pilot.TASKS
                or study.summary['completed'] != pilot.TASKS or any(study.summary['charged'].values())):
            raise ValueError('closed axis calibration trial required')
        for identity, task in study.tasks.items():
            envelope = study.envelope(identity)
            result = envelope['result']
            row = {key: task[key] for key in ('identity', 'imu_type', 'model', 'degree', 'box')}
            row.update(result)
            charged = f'artifacts/{identity}/charge.json' in envelope['artifacts']
            row['charged_proposals'] = int(charged)
            if charged:
                charge = study.artifact(identity, 'charge.json')
                if charge != dict(proposals=1, max_iterations=1000, max_seconds=2, navigation_fits=0):
                    raise ValueError('changed proposal reservation')
            if result['passed']:
                proposal = study.artifact(identity, 'training-proposal.json')
                if (not charged or not proposal['passed'] or proposal['iterations'] > 1000
                        or any(result[side]['cases'] != task['case_count'][side] for side in ('training', 'later'))
                        or result['navigation_fits']
                        or any(abs(x)>b+1e-12 for x,b in zip(proposal['correction'], task['coordinate_limits'], strict=True))):
                    raise ValueError('proposal or holdout no longer conforms to the freeze')
                row['proposal'] = proposal
            rows.append(row)
        return dict(completion=study.completion, rows=rows, tasks=len(rows),
            proposals=sum(row['charged_proposals'] for row in rows),
            navigation_fits=0, scientific_decision='abstain')


if __name__ == '__main__':
    root = Path.cwd()
    value = report(root)
    pilot.SUPPORT._write_equal(root/OUTPUT, encoded(value))
    print(json.dumps(dict(tasks=value['tasks'], proposals=value['proposals'],
        passed=sum(r['passed'] for r in value['rows']))))
