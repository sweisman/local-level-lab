# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read a sealed ESA continuation without fitting or native calculations."""

import argparse
import json


def summarize(closed, *, identity, group_id, training_epochs, prediction_epochs):
    """Verify the saved score's target, provenance and abstention limits."""
    if (closed.completion.get('state') != 'complete' or
            closed.summary.get('total') != 1 or
            closed.summary.get('completed') != 1):
        raise ValueError('closed one-task continuation required')
    rows = closed.summary.get('results')
    if (not isinstance(rows, list) or len(rows) != 1 or
            rows[0].get('identity') != identity or
            rows[0].get('status') != 'complete' or
            rows[0].get('passed') is not True):
        raise ValueError('passing sealed continuation result required')
    closed.envelope(identity)
    read = lambda name: closed.artifact(identity, name)
    technical = read('technical-summary.json')
    comparison = read('training-law-comparison.json')
    physical = read('union-simultaneous-bounded-physical.json')
    receiver = read('union-simultaneous-bounded-receiver.json')
    score = read('withheld-receiver-score.json')
    point_bound = read('point/simultaneous-bounded-receiver.json')
    point_diagnostic = read('point/receiver-error-diagnostic.json')
    if technical.get('refits') != 0:
        raise ValueError('continuation refit a saved candidate')
    if (technical.get('passed') is not True or
            technical.get('group_id') != group_id or
            technical.get('training_epochs') != training_epochs or
            technical.get('prediction_epochs') != prediction_epochs or
            technical.get('original_reads') != 0 or
            technical.get('protected_reads') != 0 or
            technical.get('confidence_calibrated') is not False or
            technical.get('scientific_decision') != 'abstain' or
            score.get('training_epochs') != training_epochs or
            score.get('prediction_epochs') != prediction_epochs or
            score.get('receiver_values_used_for_training') is not False or
            score.get('physical_position_truth_available') is not False or
            score.get('physical_position_interval_scored') is not False or
            score.get('confidence_calibrated') is not False or
            score.get('scientific_decision') != 'abstain' or
            point_bound.get('prediction_target') != 'receiver_measurement' or
            point_bound.get('training_epochs') != training_epochs or
            point_bound.get('prediction_epochs') != prediction_epochs or
            point_bound.get('later_observations_used') is not False or
            point_diagnostic.get('prediction_target') != 'receiver_measurement' or
            point_diagnostic.get('later_observations_used') is not False or
            physical.get('prediction_target') != 'physical_position' or
            receiver.get('prediction_target') != 'receiver_measurement' or
            technical.get('receiver_interval_supported') is not
                receiver.get('supported') or
            technical.get('receiver_interval_score') !=
                score.get('receiver_interval_score')):
        raise ValueError('saved score, interval and provenance disagree')
    supported = receiver['supported']
    if supported is True:
        if (comparison.get('status') == 'numerically_unqualified' or
                score.get('receiver_interval_score') is None or
                score.get('interval_reason') is not None):
            raise ValueError('supported interval lacks a scored receiver result')
    elif supported is False:
        if (not isinstance(receiver.get('reason'), str) or
                not receiver['reason'] or
                score.get('interval_reason') != receiver['reason'] or
                score.get('receiver_interval_score') is not None):
            raise ValueError('unsupported interval lacks a matching abstention')
    else:
        raise ValueError('explicit interval support required')
    return dict(
        group_id=group_id, training_epochs=training_epochs,
        prediction_epochs=prediction_epochs,
        receiver_interval_supported=supported,
        receiver_interval_score=score['receiver_interval_score'],
        interval_reason=score['interval_reason'],
        training_law_status=comparison.get('status'),
        original_reads=0, protected_reads=0, refits=0,
        confidence_calibrated=False, scientific_decision='abstain',
        manifest_sha256=closed.completion['manifest_sha256'],
        summary_sha256=closed.completion['summary_sha256'])


def report(root, study, *, smoke=False):
    from .studies.closed import ClosedStudy
    identity = 'generated-no-refit' if smoke else 'esa-187-no-refit'
    group_id = 'generated-worker-smoke' if smoke else 'esa-99f1530c3eda4318'
    training_epochs, prediction_epochs = (6, 3) if smoke else (800, 400)
    closed = ClosedStudy(root, 'data/'+study)
    try:
        return summarize(closed, identity=identity, group_id=group_id,
                         training_epochs=training_epochs,
                         prediction_epochs=prediction_epochs)
    finally:
        closed.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--study', required=True)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args(argv)
    print(json.dumps(report(args.root, args.study, smoke=args.smoke),
                     sort_keys=True))


if __name__ == '__main__':
    main()
