# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare and verify an isolated refit from the recorded IMU8 trial package."""

import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .ilvis0_control_shards import runtime_environment
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy

PROJECT = Path(__file__).resolve().parents[2]
IDENTITY = '3df34ea39a6cbdbe15bb0f36-sphere_rotating'
STUDY = 'data/portable-imu8-control'
RECOVERY = STUDY + '-recovery'
MATERIALS = STUDY + '-inputs'
RECOVERY_REQUEST = MATERIALS + '/recovery.json'
PLAN = 'docs/ilvis0-matched-trial-observed-runtime/PORTABLE_REFIT.md'
WALL_S = 1200


def local_pins():
    executables = {'cc': shutil.which('cc'), 'c++': shutil.which('c++'),
                   'python': sys.executable}
    if any(path is None for path in executables.values()):
        raise ValueError('cc, c++ and the recorded Python executable are required')
    return dict(executables={name: digest(Path(path).read_bytes())
                             for name, path in executables.items()},
                environment=runtime_environment())


def check_pins(expected, actual):
    if actual['environment'] != expected['environment']:
        raise ValueError('numerical environment differs from the refit pin')
    if actual['executables'] != expected['executables']:
        raise ValueError('native toolchain or Python executable differs from the refit pin')


def select_task(tasks):
    task = tasks[IDENTITY]
    if task['limits']['native_calls'] != 61:
        raise ValueError('the original 61-call allowance is required')
    segment = task['segment_id']
    inputs = ('recipe', 'recovery', 'recovery_tests', 'qualification',
              'qualification_tests', task['input_key'], segment+'-queries',
              segment+'-training', IDENTITY+'-reference')
    return {name: value for name, value in task.items() if name not in ('index', 'shard')}, inputs


def prepare(extracted):
    from .studies.qualification import checked
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    root = extracted/'source-freeze'
    if (root/STUDY).exists():
        raise ValueError('the isolated allowance already exists')
    pin_path = Path(PLAN).with_name('portable-refit-toolchain.json')
    pin_bytes = (PROJECT/pin_path).read_bytes()
    pins = json.loads(pin_bytes)
    check_pins(pins, local_pins())
    with closing(ClosedStudy(extracted.parent, extracted.name)) as historical:
        if (historical.completion['manifest_sha256'] != pins['parent_manifest_sha256']
                or historical.manifest['environment'] != pins['environment']
                or historical.envelope(IDENTITY)['result']['passed'] is not True):
            raise ValueError('the pinned completed historical control is required')
        compilation = historical.artifact(IDENTITY, 'compilation.json')
        for name, executable in (('value', 'cc'), ('wide', 'c++')):
            version = subprocess.check_output([executable, '--version'], text=True).splitlines()[0]
            if version != compilation[name]['compiler']:
                raise ValueError('compiler version differs from the archived build')
        task, keys = select_task(historical.tasks)
        sources = historical.manifest['sources']
        for name, sha in sources.items():
            if digest((root/name).read_bytes()) != sha:
                raise ValueError('restored source changed: '+name)
        paths = {}
        for name in keys:
            path = MATERIALS+'/'+name
            atomic(root/path, historical.input(name, raw=True))
            paths[name] = path
        recovery = historical.input('recovery')
        for name, sha in recovery['sources'].items():
            if name not in sources:
                raw = (PROJECT/name).read_bytes()
                if digest(raw) != sha:
                    raise ValueError('recovery test differs from the sealed qualification')
                atomic(root/name, raw)
        atomic(root/recovery['report'], historical.input('recovery_tests', raw=True))
        atomic(root/RECOVERY_REQUEST, historical.input('recovery', raw=True))
        checked(root, RECOVERY_REQUEST, sources=qualification_sources(root),
                environment=pins['environment'], required_tests=REQUIRED_TESTS,
                minimum_tests=len(REQUIRED_TESTS))
        atomic(root/pin_path, pin_bytes)
        atomic(root/PLAN, (PROJECT/PLAN).read_bytes())
        status = 'analysis/status.py'
        atomic(root/status, (PROJECT/status).read_bytes())
        recovery_limit = MATERIALS+'/recovery-allowance.json'
        atomic(root/recovery_limit, encoded(dict(max_attempts_per_task=2,
            max_technical_interruptions=1, maximum_wall_s=WALL_S, minimum_free_bytes=0)))
        paths.update(toolchain=pin_path.as_posix(), plan=PLAN, recovery_allowance=recovery_limit)
        definition = dict(id=Path(STUDY).name, scope=historical.manifest['scope'],
                          adapter=historical.manifest['adapter'], tasks=[task],
                          sources=sorted(sources), inputs=paths, workers=1, threads=1,
                          maximum_wall_s=WALL_S)
    registry = root/'analysis/study-status.json'
    if not registry.exists():
        atomic(registry, encoded(dict(studies=[])))
    (root/'analysis/study-status.lock').touch(exist_ok=True)
    definition_path = root/MATERIALS/'definition.json'
    atomic(definition_path, encoded(definition))
    result = isolated(root, 'studies', 'prepare', str(definition_path))
    return dict(study=STUDY, limits=result['limits'], allocation=result['allocation'])


def isolated(root, module, *args):
    output = subprocess.check_output([sys.executable, '-m', 'lll.'+module, *args],
        cwd=root, env={**os.environ, 'PYTHONPATH': str(root/'analysis')})
    return json.loads(output)


def run(extracted, reserved, *, study=STUDY, name='Isolated NASA IMU8 refit'):
    from . import ilvis0_control_shards as runner
    from .compute_budget import allocation
    from .studies.active_allocation import other_threads, register
    from .studies.recovery import inspect

    root = extracted/'source-freeze'
    recovery = study+'-recovery'
    if root.is_relative_to(PROJECT/'data'):
        register(PROJECT, name=name, path=(root/study).relative_to(PROJECT).as_posix())
    allocation(workers=1, threads=1, reserved=reserved)
    manifest = json.loads((root/study/'manifest.json').read_bytes())
    frozen = {}
    for name in ('toolchain', 'recovery_allowance'):
        record = manifest['inputs'][name]
        raw = safe_path(root/study, record['path']).read_bytes()
        if digest(raw) != record['sha256']:
            raise ValueError('frozen refit input changed: '+name)
        frozen[name] = json.loads(raw)
    check_pins(frozen['toolchain'], local_pins())
    advice = inspect(root, study)
    if advice['state'] == 'owned':
        return dict(state='owned', study=study)
    if root.is_relative_to(PROJECT/'data'):
        reserved = max(reserved, other_threads(PROJECT, workers=1))
    prior_rows = runner.merge(root/study)['results'] if advice.get('interrupted_identities') else []
    if advice.get('interrupted_identities') == [IDENTITY] and not any(
            row['identity'] == IDENTITY and row['status'] == 'complete' for row in prior_rows):
        isolated(root, 'studies.task_resume', 'close-original', '--parent', study,
                 '--qualification-request', RECOVERY_REQUEST)
        advice = inspect(root, study)
    if advice['state'] == 'closed':
        with closing(ClosedStudy(root, study)) as refit:
            row = refit.rows.get(IDENTITY)
            interrupted = row is not None and row['status'] == 'interrupted'
        if not interrupted:
            return advice
        if not (root/recovery).exists():
            limit_args = [arg for name, value in frozen['recovery_allowance'].items()
                          for arg in ('--'+name.replace('_', '-'), str(value))]
            isolated(root, 'studies.task_resume', 'prepare', '--parent', study,
                     '--output', recovery, '--qualification-request', RECOVERY_REQUEST,
                     *limit_args)
        return isolated(root, 'studies.task_resume', 'resume', '--output', recovery)
    summary = isolated(root, 'studies', 'run', study, '--reserved-threads', str(reserved))
    return dict(state=summary['state'], completed=summary['completed'],
                total=summary['total'], passed=summary['passed'])


def check(extracted, study, *, report_terminal=False):
    from .ilvis0_control_shards import verify_completion

    root = extracted/'source-freeze'
    if study is None:
        study = RECOVERY+'/stage-000' if (root/RECOVERY/'completion.json').is_file() else STUDY
    verify_completion(safe_path(root, study))
    with (closing(ClosedStudy(extracted.parent, extracted.name)) as historical,
          closing(ClosedStudy(root, study)) as refit):
        envelope = refit.envelope(IDENTITY)
        passed = envelope['result']['passed'] is True
        if refit.summary['total'] != 1 or (not passed and not report_terminal):
            raise ValueError('one passing isolated control required; use --report-terminal to audit a stopped run')
        expected, keys = select_task(historical.tasks)
        if (select_task(refit.tasks)[0] != expected
                or refit.manifest['environment'] != historical.manifest['environment']
                or any(refit.manifest['sources'].get(name) != sha
                       for name, sha in historical.manifest['sources'].items())
                or any(refit.manifest['inputs'][name]['sha256']
                       != historical.manifest['inputs'][name]['sha256'] for name in keys)):
            raise ValueError('refit task, sources, environment or original inputs differ')
        names = ('fit.json', 'compilation.json')
        if passed:
            names += ('forecast.json',)
        for name in names:
            if historical.artifact(IDENTITY, name, raw=True) != refit.artifact(IDENTITY, name, raw=True):
                raise ValueError('the refit differs from the sealed reference: '+name)
        toolchain = refit.input('toolchain')
        if historical.completion['manifest_sha256'] != toolchain['parent_manifest_sha256']:
            raise ValueError('refit reference manifest changed')
        fit = refit.artifact(IDENTITY, 'fit.json')
        forecast = refit.artifact(IDENTITY, 'forecast.json') if passed else None
        if (fit['prediction_receiver_positions_used_in_training']
                or (forecast is not None and forecast['later_positions_used'])):
            raise ValueError('forecast used later receiver observations')
        return dict(identity=IDENTITY, reference=historical.completion, refit=refit.completion,
                    exact_artifacts=list(names), combined_check_passed=passed,
                    stop_reason=envelope['result'].get('reason'), toolchain=toolchain,
                    training_evaluations=fit['evaluations'],
                    training_epochs=expected['training_epochs'],
                    later_forecast_positions=(len(forecast['coordinates'])-forecast['training_epochs']
                                              if forecast is not None else 0),
                    native_calls=envelope['charged']['native_calls'], later_positions_used=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run', 'check'))
    parser.add_argument('extracted', type=Path)
    parser.add_argument('--study')
    parser.add_argument('--report-terminal', action='store_true')
    parser.add_argument('--reserved-threads', type=int, default=0)
    args = parser.parse_args()
    extracted = args.extracted.resolve()
    if args.action == 'prepare':
        result = prepare(extracted)
    elif args.action == 'run':
        result = run(extracted, args.reserved_threads)
    else:
        result = check(extracted, args.study, report_terminal=args.report_terminal)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
