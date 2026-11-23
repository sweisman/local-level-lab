# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check earlier-only forecast selection against the original ESA 400/120 report."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from .esa_rolling_origin_400_model_matrix import FIT_INPUT_KEYS, ID, SCOPE, tasks
from .esa_sealed_forecast_selection import score_after_seal
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_SCORING_SEAL_PLAN.md'
REPORT = FOLDER+'ESA_400_120_MODEL_MATRIX_RESULT.json'
REPORT_SHA = 'dd603cc6a72eb9b4b498bed0cecd996f66fa36f64c666b08a2bfb8d49d71a2d6'
FREEZE = FOLDER+'esa-scoring-seal-freeze.json'
RESULT = FOLDER+'esa-scoring-seal-result.json'
MANIFEST_SHA = 'd29ecef42b37a8fffe05dbff591cf24d0720129c3792f14cd1649803a141829d'
SUMMARY_SHA = 'eb84eca2721c84af306f684a9fa9ffc08c17ffd0087e530857bf58fe9bf35058'


def run(root, action):
    root = Path(root).resolve()
    task_list = tasks()
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if (study.completion['manifest_sha256'] != MANIFEST_SHA
                or study.completion['summary_sha256'] != SUMMARY_SHA
                or study.manifest['scope'] != SCOPE
                or set(study.manifest['inputs']) != set(FIT_INPUT_KEYS)):
            raise ValueError('original ESA development matrix and earlier-only input set required')
        times = study.input('forecast_times')
        if len(times) != 520:
            raise ValueError('exact development query support required')
        own = Path(__file__).relative_to(root).as_posix()
        sources = source_closure(root, (own, PLAN, 'analysis/tests/test_esa_sealed_forecast_selection.py'))
        freeze = encoded(dict(
            sources={name:digest((root/name).read_bytes()) for name in sources},
            archive=study.completion, forecast_times_sha256=digest(encoded(times)),
            report_sha256=REPORT_SHA, expected_tasks=len(task_list), maximum_reports=1,
            threads=1, new_fits=0, protected_reads=0, environment=runtime_environment()))
        if action == 'freeze':
            _write_equal(root/FREEZE, freeze)
            return dict(freeze_sha256=digest(freeze))
        if (root/FREEZE).read_bytes() != freeze:
            raise ValueError('unchanged archived matrix, report and source freeze required')

        def check_published_summary(selected):
            raw = (root/REPORT).read_bytes()
            if digest(raw) != REPORT_SHA:
                raise ValueError('the historical score summary differs from its receipt')
            report = json.loads(raw)
            settings = {(r['profile'], r['law']):r for r in report['settings']}
            records = {r['identity']:r for r in report['rows']}
            if len(settings) != len(selected):
                raise ValueError('original settings grid must still match')
            for row in selected:
                key = row['profile'], row['law']
                starts = {model:(None if primary is None else primary['start'])
                          for model, primary in row['primaries'].items()}
                if starts != settings[key]['primary_start']:
                    raise ValueError('training-only selection differs from the published result')
                for primary in row['primaries'].values():
                    if primary and primary['forecast_sha256'] != records[primary['identity']]['forecast_sha256']:
                        raise ValueError('selected forecast differs from the published hash')
            return selected

        selected = score_after_seal(study, tasks=task_list, times=times, training_epochs=400,
                                    score=check_published_summary)
    count = sum(primary is not None for row in selected for primary in row['primaries'].values())
    result = dict(starts_verified=len(task_list), settings=len(selected), verified_primaries=count,
                  sealed_before_summary=True, freeze_sha256=digest(freeze), primary_choices=selected,
                  new_fits=0, withheld_receiver_reads=0, protected_reads=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return {key:value for key, value in result.items() if key != 'primary_choices'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'check'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))


if __name__ == '__main__':
    main()
