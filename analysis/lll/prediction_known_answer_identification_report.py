# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and publish the closed known-answer identification trial."""
import json
import math
from pathlib import Path


def summarize_rows(rows, *, truth, seed_start, seed_count):
    if (not isinstance(rows, list) or len(rows) != seed_count or
            [row.get('seed') for row in rows] != list(range(seed_start, seed_start+seed_count))):
        raise ValueError('complete unique predetermined seeds required')
    statuses = ('provisional_minimum', 'equivalent_forecast', 'abstain')
    for row in rows:
        status = row['classification']['status']
        selected = row['selected_law']
        if (status not in statuses or (selected is None) != (status != 'provisional_minimum')
                or type(row['oracle_covered_epochs']) is not int
                or not 0 <= row['oracle_covered_epochs'] <= 10
                or not math.isfinite(row['oracle_mean_width_m'])
                or row['oracle_mean_width_m'] <= 0):
            raise ValueError('invalid saved history classification or oracle prediction')
        if selected is None:
            if row['selected_covered_epochs'] is not None or row['selected_mean_width_m'] is not None:
                raise ValueError('abstention cannot carry selected-law coverage')
        elif (type(row['selected_covered_epochs']) is not int or
              not 0 <= row['selected_covered_epochs'] <= 10 or
              not math.isfinite(row['selected_mean_width_m']) or
              row['selected_mean_width_m'] <= 0):
            raise ValueError('invalid selected-law withheld prediction')
    return dict(histories=len(rows),
                provisional_minimum=sum(row['classification']['status'] == 'provisional_minimum'
                                        for row in rows),
                equivalent_forecast=sum(row['classification']['status'] == 'equivalent_forecast'
                                        for row in rows),
                abstain=sum(row['classification']['status'] == 'abstain' for row in rows),
                truth_selected=sum(row['selected_law'] == truth for row in rows),
                wrong_selected=sum(row['selected_law'] not in (None, truth) for row in rows),
                oracle_covered_epochs=sum(row['oracle_covered_epochs'] for row in rows),
                selected_covered_epochs=sum(row['selected_covered_epochs'] or 0 for row in rows),
                selected_histories=sum(row['selected_law'] is not None for row in rows),
                oracle_mean_width_m=sum(row['oracle_mean_width_m'] for row in rows)/len(rows))


def build(root):
    """Recount sealed per-seed records and check source, input and charge hashes."""
    from lll.prediction_known_answer_identification_v2 import (
        IDENTITY, SCOPE, qualification_sources, require_first_failure,
        recipe, tasks)
    from lll.studies.artifacts import digest
    from lll.studies.closed import ClosedStudy
    from lll.studies.source_binding import verify as verify_sources
    root = Path(root).resolve()
    first = ClosedStudy(root, 'data/prediction-known-answer-identification-20261111')
    study = ClosedStudy(root, 'data/'+IDENTITY)
    try:
        require_first_failure(first.summary)
        if (study.completion['state'] != 'complete' or study.summary['passed'] is not True or
                len(study.rows) != 4 or
                study.summary['charged'] != dict(bound_calls=404, bound_steps=1624,
                                                  native_calls=0, packet_visits=0) or
                study.manifest['scope'] != SCOPE or study.input('recipe') != recipe() or
                study.input('first_failure')['summary_sha256'] != first.completion['summary_sha256'] or
                study.input('first_failure')['manifest_sha256'] != first.completion['manifest_sha256'] or
                set(study.tasks) != {task['identity'] for task in tasks()}):
            raise ValueError('unchanged complete second study and first failure required')
        source_proof = verify_sources(
            root, declared=study.input('qualification_request')['sources'],
            manifest=study.manifest['sources'])
        rows = []
        for task in tasks():
            identity = task['identity']
            if {key:value for key,value in study.tasks[identity].items()
                if key not in ('index', 'shard')} != task:
                raise ValueError('frozen task differs from declared task')
            result = study.envelope(identity)['result']
            histories = study.artifact(identity, 'histories.json')
            information = study.artifact(identity, 'training-information.json')
            summary = summarize_rows(
                histories, truth=task['payload']['truth'],
                seed_start=task['payload']['seed_start'],
                seed_count=task['payload']['seed_count'])
            expected = dict(histories=summary['histories'],
                            truth_selected=summary['truth_selected'],
                            wrong_selected=summary['wrong_selected'],
                            oracle_covered_epochs=summary['oracle_covered_epochs'],
                            selected_covered_epochs=summary['selected_covered_epochs'],
                            selected_histories=summary['selected_histories'],
                            information_rank=information['rank'])
            if (any(result.get(key) != value for key,value in expected.items()) or
                    result.get('status_counts') != dict(
                        provisional_minimum=summary['provisional_minimum'],
                        equivalent_forecast=summary['equivalent_forecast'],
                        abstain=summary['abstain']) or
                    result.get('scientific_decision') != 'abstain' or
                    result.get('scientific_detection') is not False or
                    any(row['classification'].get('later_observations_used') is not False
                        for row in histories)):
                raise ValueError('saved result and per-seed evidence differ')
            rows.append(dict(identity=identity, truth=task['payload']['truth'],
                             cadence_s=task['payload']['cadence_s'],
                             information_rank=information['rank'], **summary))
        total = dict(histories=sum(row['histories'] for row in rows),
                     abstain=sum(row['abstain'] for row in rows),
                     provisional_minimum=sum(row['provisional_minimum'] for row in rows),
                     truth_selected=sum(row['truth_selected'] for row in rows),
                     wrong_selected=sum(row['wrong_selected'] for row in rows),
                     oracle_covered_epochs=sum(row['oracle_covered_epochs'] for row in rows),
                     selected_covered_epochs=sum(row['selected_covered_epochs'] for row in rows),
                     selected_histories=sum(row['selected_histories'] for row in rows))
        return dict(verified=True, version='known-answer-identification-report-v1',
                    first_failure_summary_sha256=first.completion['summary_sha256'],
                    second_summary_sha256=study.completion['summary_sha256'],
                    source_proof=source_proof, source_sha256=digest(Path(__file__).read_bytes()),
                    charged=study.summary['charged'], rows=rows, total=total,
                    full_aircraft_qualification=False, calibrated_coverage=False,
                    scientific_detection=False)
    finally:
        study.close()
        first.close()


def render(report):
    if report.get('verified') is not True or report['total']['histories'] != 400:
        raise ValueError('verified complete report required')
    total = report['total']
    lines = ['# Known-answer error-law trial', '',
             '**400 of 400 generated histories completed.** This is a software',
             'diagnostic, not a flight result or a calibrated detection.', '',
             '| Generating error law | Sampling | Provisional single law | Correct | Wrong | Abstain | Oracle 95% coverage |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for row in report['rows']:
        lines.append(f"| {row['truth']} | {row['cadence_s']:g} s | "
                     f"{row['provisional_minimum']}/100 | {row['truth_selected']} | "
                     f"{row['wrong_selected']} | {row['abstain']} | "
                     f"{row['oracle_covered_epochs']}/1,000 |")
    lines += ['', f"Across all cases, {total['provisional_minimum']} histories selected"
              f" one law, {total['abstain']} abstained and "
              f"{total['wrong_selected']} selected the wrong candidate. "
              f"The correctly supplied law covered {total['oracle_covered_epochs']}/4,000 "
              'withheld receiver epochs with nominal 95% intervals. Local',
              'training-information rank was three in every task, yet individual',
              'short histories often could not choose one law. This is why rank',
              'alone cannot qualify uncertainty.', '',
              'The first allowance completed every calculation but failed its',
              'result-schema gate. Its 404 charged operations remain preserved.',
              'The corrected allowance separately completed and verified all four',
              'tasks. Its 404 charged operations and 1,624 steps are sealed.', '',
              'This trial learns only among three fixed error laws in a simplified',
              'linear model. It does not assess nonlinear aircraft fitting, actual',
              'sensor errors, receiver-coordinate adequacy or flight-level coverage.',
              'The next gate is a full known-answer aircraft prediction test.', '',
              '[Method and finite limits](PLAN.md) · [Correction receipt](PLAN_V2.md) · '
              '[Verified numbers](verified-report.json).', '']
    return '\n'.join(lines)


def publish(root):
    from lll.studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    report = build(root)
    target = root/'docs/prediction-known-answer-identification'
    atomic(target/'verified-report.json', encoded(report))
    atomic(target/'RESULT.md', render(report).encode())
    return dict(published=str(target.relative_to(root)), histories=400)


def verify(root):
    from lll.studies.artifacts import encoded
    root = Path(root).resolve()
    report = build(root)
    target = root/'docs/prediction-known-answer-identification'
    if ((target/'verified-report.json').read_bytes() != encoded(report) or
            (target/'RESULT.md').read_bytes() != render(report).encode()):
        raise ValueError('published known-answer report differs from sealed evidence')
    return dict(verified=True, histories=400)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('publish', 'verify'))
    parser.add_argument('--project', default='.')
    args = parser.parse_args()
    print(json.dumps(publish(args.project) if args.action == 'publish' else verify(args.project),
                     sort_keys=True))


if __name__ == '__main__':
    main()
