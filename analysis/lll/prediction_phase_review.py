# SPDX-License-Identifier: AGPL-3.0-or-later
"""One bounded saved-fit review, without simulation, fitting or native loading."""
import csv
import io
import json
import time
from pathlib import Path

from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


def identities(study, seed):
    """Two processing cases, two starts, failing and preceding seed; one stop."""
    chosen = []
    for name, task in study.tasks.items():
        p = task['payload']; case = p['case']
        if name not in study.rows or p['draw_seed'] not in (seed - 1, seed):
            continue
        if case['law'] == 'increment' and (
                case['model'] == 'sphere_rotating' or
                (p['draw_seed'] == seed and case['model'] == 'flat_still'
                 and case['profile'] == 0 and case['start'] == 0)):
            chosen.append(name)
    if not chosen or len(chosen) > 24:
        raise ValueError('one nonempty selection of at most 24 saved records required')
    return sorted(chosen)


def read_selected(study, selected, *, maximum_wall_s=600):
    """Read only declared, hash-checked records; never invoke an evaluator."""
    if not selected or len(selected) > 24 or len(set(selected)) != len(selected):
        raise ValueError('one unique nonempty selection of at most 24 records required')
    if not 0 < maximum_wall_s <= 600:
        raise ValueError('review ceiling must not exceed 600 seconds')
    deadline = time.monotonic() + maximum_wall_s
    records = []
    for name in selected:
        if time.monotonic() >= deadline:
            raise TimeoutError('saved-results review allowance exhausted')
        envelope = study.envelope(name)
        fit_path = 'artifacts/' + name + '/fit.json'
        fit = study.artifact(name, 'fit.json') if fit_path in envelope['artifacts'] else None
        records.append(dict(identity=name, case=study.tasks[name]['payload'],
                            result=envelope['result'], fit=fit))
    return dict(version='prediction-phase-saved-review-v1', records=records,
                manifest_sha256=study.completion['manifest_sha256'],
                summary_sha256=study.completion['summary_sha256'],
                optimizer_starts=0, new_noise_draws=0, native_calls=0,
                maximum_wall_s=maximum_wall_s, numerical_threads=1)


def run(root, request_path):
    """Execute the predeclared selection once and preserve an immutable snapshot."""
    from .evidence_snapshot import create, publish, sha
    root = Path(root).resolve(); request_path = Path(request_path)
    request = json.loads((root / request_path).read_bytes())
    for name, expected in request['sources'].items():
        if sha(root / name) != expected:
            raise ValueError('review source changed after selection freeze')
    data = root / request['output']; data.mkdir(parents=True, exist_ok=True)
    # Charge this one review before inspecting any saved fit; no retries.
    with (data / 'review-start.json').open('xb') as f:
        f.write(encoded(dict(request_sha256=sha(root / request_path), reviews_charged=1)))
    study = ClosedStudy(root, request['study'])
    try:
        if (study.completion != request['completion'] or
                identities(study, request['failed_seed']) != request['identities']):
            raise ValueError('closed study or declared selection changed')
        report = read_selected(study, request['identities'])
        inputs = {request_path.as_posix(): sha(root / request_path)}
        for name in ('manifest.json', 'completion.json', 'summary.json', 'stop-request.json'):
            relative = request['study'] + '/' + name
            inputs[relative] = sha(root / relative)
        for name in request['identities']:
            row = study.rows[name]; relative = request['study'] + '/' + row['artifact']
            inputs[relative] = row['artifact_sha256']
            envelope = study.envelope(name)
            fit_path = 'artifacts/' + name + '/fit.json'
            if fit_path in envelope['artifacts']:
                inputs[request['study'] + '/' + fit_path] = envelope['artifacts'][fit_path]
        stream = io.StringIO(newline=''); writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['identity', 'numerical_pass', 'training_cost', 'error_type'])
        for record in report['records']:
            fit = record['fit'] or {}; result = record['result']
            writer.writerow([record['identity'], fit.get('converged', False),
                             fit.get('residual_sum_squares', ''), result.get('error_type', '')])
        create(root, data, version=report['version'], inputs=inputs, sources=request['sources'],
               outputs={'diagnosis.json': encoded(report), 'results.csv': stream.getvalue().encode(),
                        'review-start.json': (data / 'review-start.json').read_bytes()},
               summary=dict(records=len(report['records']), fitted_records=sum(r['fit'] is not None for r in report['records']),
                            optimizer_starts=0, new_noise_draws=0, native_calls=0, reviews_charged=1))
        publish(data, root / request['publication'])
        return report
    finally:
        study.close()


def publish_phase(root, prefix, *, qualification):
    """Package the unchanged audited phase with the manifest's relative plan key.

    The frozen publisher passes an absolute Path to a packager requiring a
    relative string. This reporting adapter changes no scientific dependency.
    """
    from .prediction_calibration_report import inspect, render, result_csv
    from .prediction_calibration_study import qualification_sources
    from .studies.qualification import checked
    from .studies.artifacts import atomic, safe_path
    from .studies.native_publication import include_native_caches
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_publication import publish as package, check
    root = Path(root).resolve(); data = safe_path(root, prefix)
    request, tests = checked(root, qualification, sources=qualification_sources(root),
        environment=environment(), minimum_tests=62, required_tests=[
            'test_handoff_rejects_unexecuted_calibration_draws',
            'test_calibration_adapter_metadata_loads_in_real_frozen_namespace',
            'test_validation_futility_stops_at_fifth_distinct_family_not_four'])
    report = inspect(root, prefix)
    if report['role'] != 'calibration' or report['calibration'] is not None:
        raise ValueError('this reporting adapter is limited to the stopped calibration')
    public = root / 'docs/prediction-calibration'
    if (public / 'evidence-receipt.json').exists():
        raise ValueError('immutable publication already exists')
    plan = 'docs/prediction-score-qualification/EXECUTION_PLAN.md'
    package(data, public, render(report), plan=plan)
    if report['native_assets']:
        include_native_caches(root, data, public,
            entries=[dict(path=k, sha256=v) for k, v in sorted(report['native_assets'].items())],
            maximum_bytes=64*1024**2)
    extras = {'results.csv': result_csv(report).encode(),
        'artifacts/publication/verified-report.json': encoded(report),
        'artifacts/publication/qualification-request.json': request,
        'artifacts/publication/qualification-report.xml': tests,
        'artifacts/publication/reporting-adapter.py': Path(__file__).read_bytes(),
        'stop-request.json': (data / 'stop-request.json').read_bytes()}
    for name in ('CALIBRATION_PLAN.md', 'CALIBRATION_TARGETS_PLAN.md', 'CAMPAIGN_SIZING.md'):
        extras[name] = f'# Related plan\n\nSee [{name}](../prediction-score-qualification/{name}).\n'.encode()
    receipt = json.loads((public / 'evidence-receipt.json').read_bytes())
    for name, raw in extras.items():
        atomic(public / name, raw); receipt['artifacts'][name] = digest(raw)
    atomic(public / 'evidence-receipt.json', encoded(receipt)); check(data, public)
    if encoded(inspect(root, public.relative_to(root).as_posix())) != encoded(report):
        raise ValueError('published replay differs from closed source')
    return dict(publication=public.relative_to(root).as_posix(),
                artifacts=len(receipt['artifacts']), returned=report['returned_outcomes'],
                numerical_passes=report['numerically_converged'], native_calls=0, optimizer_starts=0)
