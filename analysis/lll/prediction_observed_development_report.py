# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report a sealed ESA development forecast from saved evidence only."""

import argparse
import hashlib
from pathlib import Path

from . import prediction_observed_development_study as study


def audit(root, identity=study.IDENTITY):
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    smoke = identity == study.SMOKE_ID
    if identity not in (study.IDENTITY, study.SMOKE_ID):
        raise ValueError('declared observed-development or generated smoke identity required')
    task = study.smoke_task() if smoke else study.tasks()[0]
    scope = study.SMOKE_SCOPE if smoke else study.SCOPE
    group = study.SMOKE_GROUP if smoke else study.GROUP_ID
    training, prediction = (6, 3) if smoke else (800, 400)
    closed = ClosedStudy(root, 'data/'+identity)
    try:
        if (closed.completion['state'] not in ('complete', 'terminal') or
                closed.summary['total'] != 1 or
                closed.summary['completed'] != 1 or
                closed.manifest['scope'] != scope or
                closed.manifest['tasks'][0]['identity'] != task['identity']):
            raise ValueError('sealed observed-development study required')
        envelope = closed.envelope(task['identity'])
        result = envelope['result']
        metadata = dict(version='observed-development-report-v1',
                        study='data/'+identity,
                        input_type='generated' if smoke else 'observed',
                        reporter_sha256=hashlib.sha256(
                            (root/'analysis/lll/prediction_observed_development_report.py')
                            .read_bytes()).hexdigest(),
                        manifest_sha256=closed.completion['manifest_sha256'],
                        summary_sha256=closed.completion['summary_sha256'],
                        charged=closed.summary['charged'],
                        elapsed_s=closed.summary['elapsed_s'],
                        technical_passed=result['passed'],
                        training_epochs=training,
                        prediction_epochs=prediction,
                        physical_position_truth_available=False,
                        confidence_calibrated=False,
                        scientific_decision='abstain')
        if result['passed'] is False:
            return dict(metadata, error_type=result.get('error_type'),
                        reason=result.get('reason'))
        if (result['scientific_decision'] != 'abstain' or
                result['group_id'] != group or
                result['original_reads'] != 0 or result['protected_reads'] != 0 or
                result['training_epochs'] != training or
                result['prediction_epochs'] != prediction or
                result['physical_position_truth_available'] is not False):
            raise ValueError('sealed observed-development result differs from plan')
        score = closed.artifact(task['identity'], 'withheld-receiver-score.json')
        if (score['scientific_decision'] != 'abstain' or
                score['training_epochs'] != training or
                score['prediction_epochs'] != prediction or
                score['physical_position_truth_available'] is not False or
                score['physical_position_interval_scored'] is not False or
                score['receiver_values_used_for_training'] is not False):
            raise ValueError('receiver-only score differs from declared split')
        fits = {law: closed.artifact(task['identity'], law+'/fit.json')
                for law in ('increment', 'point')}
        return dict(metadata, fit={law: dict(converged=fit['converged'],
                                   evaluations=fit['evaluations'])
                         for law, fit in fits.items()},
                    receiver_interval_supported=result['receiver_interval_supported'],
                    receiver_interval_score=score['receiver_interval_score'],
                    candidate_receiver_sections=score['candidate_receiver_sections'])
    finally:
        closed.close()


def render(report):
    if report['technical_passed'] is False:
        return ('# Observed ESA development forecast\n\n'
                'The sealed one-recording development task did not pass its '
                'technical gate. Its charged work and failure are retained. '
                'No withheld-prediction or Earth-model conclusion follows.\n\n'
                f"Failure: {report.get('reason') or report.get('error_type') or 'unspecified'}\n")
    title = ('# Generated worker control' if report['input_type'] == 'generated'
             else '# Observed ESA development forecast')
    lines = [title, '',
             'The fixed candidate was fitted separately under two supplied IMU '
             f"error laws using {report['training_epochs']} earlier receiver positions. "
             'Both forecasts were saved before the '
             f"{report['prediction_epochs']} later receiver positions were opened.", '',
             '| Supplied error law | Fit converged | Evaluations | '
             'Withheld horizontal RMS | Withheld height RMS |',
             '|---|---|---:|---:|---:|']
    for law in ('increment', 'point'):
        fit = report['fit'][law]
        sections = report['candidate_receiver_sections'][law]
        later = sections.get('prediction') if isinstance(sections, dict) else None
        horizontal = later.get('horizontal_rms_m') if isinstance(later, dict) else None
        height = later.get('vertical_rms_m') if isinstance(later, dict) else None
        fmt = lambda value: f'{value:.3f} m' if isinstance(value, (int, float)) else 'unavailable'
        lines.append(f"| {law} | {'yes' if fit['converged'] else 'no'} | "
                     f"{fit['evaluations']} | {fmt(horizontal)} | {fmt(height)} |")
    lines += ['',
              'The interval result is '+('supported under the supplied laws.'
                  if report['receiver_interval_supported'] else 'unsupported; the analysis abstains.'),
              ('This is a generated software control, not evidence from an aircraft.'
               if report['input_type'] == 'generated' else
               'These are development results on one recording. The error laws '
               'are assumptions, the true physical aircraft path is unavailable, '
               'and this does not establish calibrated prediction coverage or an '
               'Earth-model decision.'), '']
    return '\n'.join(lines)


def publish(root):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    report = audit(root)
    output = root/'docs/prediction-observed-development'
    atomic(output/'report.json', encoded(report))
    atomic(output/'RESULT.md', render(report).encode())
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    report = publish(args.root)
    if report['technical_passed']:
        print('Observed development report saved; '
              f"receiver interval supported={report['receiver_interval_supported']}")
    else:
        print('Observed development report saved; '
              f"technical failure={report.get('reason') or report.get('error_type') or 'unspecified'}")


if __name__ == '__main__':
    main()
