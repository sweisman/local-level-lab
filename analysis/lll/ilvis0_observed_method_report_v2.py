# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish the versioned observed method pilot from sealed results only."""

import hashlib
from pathlib import Path

from . import ilvis0_observed_method_report as shared
from .ilvis0_observed_method_pilot_v2 import ID

RECOVERY='data/'+ID+'-recovery'


def build(root='.'):
    root=Path(root).resolve()
    report=shared.build(root,study_id=ID,
        recovery=RECOVERY if (root/RECOVERY).exists() else None)
    shared_sha256=report.get('source_sha256')
    report.update(version='ilvis0-observed-method-report-v2',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        shared_report_sha256=shared_sha256)
    return report


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=build(root)
    output=root/'docs/prediction-group-transfer'
    atomic(output/'OBSERVED_METHOD_PILOT_V2_RESULT.md',
        shared.render(report,plan='OBSERVED_METHOD_PILOT_V2_PLAN.md',
                      task_file='observed-method-v2-tasks.csv').encode())
    atomic(output/'observed-method-v2-tasks.csv',shared.csv_bytes(report))
    atomic(output/'observed-method-v2-report.json',encoded(report))
    return report


if __name__=='__main__':
    result=publish()
    print('cuts within diagnostic scale:',
          result['method_agreement_within_diagnostic_scale'],'/',result['cuts'])
