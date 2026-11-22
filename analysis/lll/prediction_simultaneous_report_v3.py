# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish the runtime-qualified cohort from sealed results without fitting."""

from . import prediction_simultaneous_study_v3 as definition
from .prediction_simultaneous_report import publish


def main():
    report = publish(
        '.', study_id='data/' + definition.IDENTITY, definition=definition,
        directory='docs/prediction-simultaneous-law-family-v3')
    total = report['totals']
    print(f"{total['completed']}/96 audited; technical={total['technical']}; "
          f"coverage_gate={total['coverage_gate_passed']}")


if __name__ == '__main__':
    main()
