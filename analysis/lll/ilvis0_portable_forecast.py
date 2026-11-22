# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproduce one recorded forecast from the sealed isolated IMU8 fit."""

import argparse
from contextlib import closing
import json
from pathlib import Path
import re

from .ilvis0_portable_refit import (
    IDENTITY, PROJECT, RECOVERY_REQUEST, check_pins, isolated, local_pins, run, select_task,
)
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

PUBLIC = 'docs/ilvis0-matched-trial-observed-runtime'
STUDY = 'data/portable-imu8-forecast'
ADAPTER = 'analysis/lll/ilvis0_portable_forecast.py'
SCOPE = 'isolated fixed-parameter forecast reproduction'
WALL_S = 600


def forecast_task(tasks, expected):
    if not re.fullmatch('[a-f0-9]{64}', expected):
        raise ValueError('a frozen forecast digest is required')
    task, _ = select_task(tasks)
    segment = task['segment_id']
    limits = dict(native_calls=1, bound_calls=0, bound_steps=0,
                  packet_visits=task['full_packets']*(task['training_epochs']+task['scoring_epochs']))
    keys = ('recipe', task['input_key'], segment+'-training', segment+'-queries')
    return dict(task, native_kind='tangent', limits=limits, forecast_sha256=expected), keys


def prepare(extracted):
    from .studies.qualification import checked
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    root = extracted/'source-freeze'
    if (root/STUDY).exists():
        raise ValueError('the forecast allowance already exists')
    receipt = (PROJECT/PUBLIC/'refit-verification.json').read_bytes()
    verification = json.loads(receipt)
    pins = verification['toolchain']
    check_pins(pins, local_pins())
    checked(root, RECOVERY_REQUEST, sources=qualification_sources(root),
            environment=pins['environment'], required_tests=REQUIRED_TESTS,
            minimum_tests=len(REQUIRED_TESTS))
    with (closing(ClosedStudy(extracted.parent, extracted.name)) as historical,
          closing(ClosedStudy(PROJECT, PUBLIC+'/refit-evidence')) as refit):
        fit = refit.artifact(IDENTITY, 'fit.json', raw=True)
        compilation = refit.artifact(IDENTITY, 'compilation.json', raw=True)
        if (historical.completion != verification['reference'] or refit.completion != verification['refit']
                or historical.completion['manifest_sha256'] != pins['parent_manifest_sha256']
                or historical.manifest['environment'] != pins['environment']
                or fit != historical.artifact(IDENTITY, 'fit.json', raw=True)
                or compilation != historical.artifact(IDENTITY, 'compilation.json', raw=True)
                or json.loads(fit)['prediction_receiver_positions_used_in_training']):
            raise ValueError('the archived and reproduced training fits must agree exactly')
        reference = historical.artifact(IDENTITY, 'forecast.json', raw=True)
        task, keys = forecast_task(historical.tasks, digest(reference))
        sources = historical.manifest['sources']
        for name, sha in sources.items():
            if digest((root/name).read_bytes()) != sha:
                raise ValueError('restored source changed: '+name)
        materials = {name: historical.input(name, raw=True) for name in keys}
    materials.update(fit=fit, compilation=compilation, toolchain=encoded(pins),
        refit_verification=receipt, plan=(PROJECT/PUBLIC/'PORTABLE_FORECAST.md').read_bytes(),
        recovery_allowance=encoded(dict(max_attempts_per_task=2, max_technical_interruptions=1,
                                       maximum_wall_s=WALL_S, minimum_free_bytes=0)))
    inputs = {}
    for name, material in materials.items():
        path = STUDY+'-inputs/'+name
        atomic(root/path, material)
        inputs[name] = path
    support = (ADAPTER, 'analysis/lll/ilvis0_portable_refit.py')
    for name in support:
        atomic(root/name, (PROJECT/name).read_bytes())
    definition = dict(id=Path(STUDY).name, scope=SCOPE, adapter=ADAPTER, tasks=[task],
                      sources=sorted(set(sources).union(support)), inputs=inputs,
                      workers=1, threads=1, maximum_wall_s=WALL_S)
    path = root/(STUDY+'-inputs/definition.json')
    atomic(path, encoded(definition))
    manifest = isolated(root, 'studies', 'prepare', str(path))
    return dict(study=STUDY, limits=manifest['limits'])


def evaluate(task, context):
    from .ilvis0_forecast import native_forecast
    from .ilvis0_matched_observed_preflight import MAX_INTERVAL, load_training
    from .ilvis0_wide_tangent import load as load_wide, problem as widen

    if context.manifest['scope'] != SCOPE or task['identity'] != IDENTITY:
        raise ValueError('the single frozen forecast replay is required')
    check_pins(json.loads(context.input_path('toolchain').read_bytes()), local_pins())
    base, directory, motion, compilation = load_training(task, context)
    tangent, compilation['wide'] = load_wide(directory,
        expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
    original = json.loads(context.input_path('compilation').read_bytes())
    if any(metadata != original[name] for name, metadata in compilation.items()):
        raise ValueError('forecast native builds differ from the archived build')
    context.save('compilation.json', compilation)
    fit = json.loads(context.input_path('fit').read_bytes())
    prediction = native_forecast(widen(base, kernel=tangent), fit['normalized_parameters'],
        task['model'], **motion, maximum_interval_s=MAX_INTERVAL, reserve=context.charge,
        retain_training_difference=True)
    forecast = dict(coordinates=prediction['coordinates'].tolist(),
        query_times_s=motion['times'].tolist(), training_epochs=task['training_epochs'],
        later_positions_used=prediction['prediction_receiver_positions_used'],
        training_coordinate_difference=prediction['training_coordinate_difference'].tolist())
    context.save('forecast.json', forecast)
    return dict(passed=digest(encoded(forecast)) == task['forecast_sha256'],
        converged=fit['converged'], forecast_positions=task['scoring_epochs'],
        fit_starts=0, later_positions_used=forecast['later_positions_used'],
        scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run'))
    parser.add_argument('extracted', type=Path)
    parser.add_argument('--reserved-threads', type=int, default=0)
    args = parser.parse_args()
    extracted = args.extracted.resolve()
    result = (prepare(extracted) if args.action == 'prepare' else
              run(extracted, args.reserved_threads, study=STUDY, name='Isolated NASA IMU8 forecast'))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
