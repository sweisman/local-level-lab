# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only verification of the six generated oracle forecasts."""


def check_case(task, result, saved, *, proof, historical, operations,
               construction, environment):
    """Recompute physical scores from sealed forecast and receiver artifacts."""
    import numpy as np
    from lll.airquantumgrav_observation_truth import start
    from lll.airquantumgrav_truth import truth, A, E2, DISC_RADIUS
    from lll.airquantumgrav_scoring import sections
    from lll.airquantumgrav_training_report import saved_position_errors
    from lll.noisy_realization_attribution import construction_limits
    from lll.studies.artifacts import encoded

    spec = task['payload']
    model, profile = spec['model'], spec['profile']
    removal = .35 if profile else 0.
    sign = -1 if profile else 1
    expected_times = [historical['query_start_s'] + i * historical['query_step_s']
                      for i in range(historical['queries'])]
    binding = saved['input-binding.json']
    forecast = saved['forecast.json']
    answer = saved['scoring-observations.json']
    scores = saved['scores.json']
    known = saved['known-corrections.json']
    compiled = saved['compilation.json']
    limits = construction_limits()
    arguments = dict(model=model, latitude_deg=spec['latitude_deg'],
                     pattern=historical['pattern'], removal=removal,
                     height_profile=historical['height_profile'],
                     gravity_model=historical['gravity_model'])
    original = start(truth(times=np.array([0.]), **arguments),
                     model=model, sign=sign)
    initial = {key: value.tolist() if hasattr(value, 'tolist') else value
               for key, value in original['initial'].items()}
    if (binding['parent_manifest_sha256'] != proof['parent_manifest_sha256']
            or binding['parent_summary_sha256'] != proof['parent_summary_sha256']
            or binding['full_array_sha256'] != spec['hashes']
            or binding['parent_identities'] != spec['parent_identities']
            or binding['original_reads'] != 0 or binding['protected_reads'] != 0
            or known['initial'] != initial
            or known['parameters'] != original['parameters']
            or known['gravity_mps2'] != original['gravity_mps2']
            or known['removal'] != removal
            or known['known_corrections_supplied_not_estimated'] is not True
            or compiled['source_sha256'] != environment['native_source_sha256']
            or compiled['compiler'] != environment['compilers']['cc']
            or forecast['times_s'] != expected_times
            or scores['times_s'] != expected_times
            or scores['training_epochs'] != 800
            or scores['prediction_epochs'] != 400
            or forecast['known_corrections_supplied_not_estimated'] is not True
            or forecast['prediction_receiver_positions_used'] is not False
            or forecast['continuous_propagation_without_gps_reset'] is not True
            or scores['score_reference'] != 'generated noiseless physical truth'
            or scores['later_receiver_noise_added'] is not False
            or operations != dict(value=1, tangent=0,
                                  packet_visits=task['limits']['packet_visits'])
            or construction != limits
            or result['native_calls'] != 1
            or result['constructed_intervals'] != limits['constructed_intervals']
            or result['generated_samples'] != limits['generated_samples']
            or result['noise_normal_variates'] != limits['noise_normal_variates']
            or result['original_reads'] != 0 or result['protected_reads'] != 0
            or result['technical_passed'] is not True
            or result['passed'] is not True
            or result['oracle_not_real_flight_estimator'] is not True
            or result['confidence_calibrated'] is not False
            or result['scientific_decision'] != 'abstain'):
        raise ValueError('oracle input, known correction, scope or charge changed')
    errors = np.asarray(saved_position_errors(
        forecast['coordinates'], answer, model=model,
        constants=dict(A=A, E2=E2, DISC_RADIUS=DISC_RADIUS)))
    if (errors.shape != (1200, 3)
            or not np.allclose(errors, np.asarray(scores['errors_neu_m']),
                               rtol=0, atol=1e-7)):
        raise ValueError('oracle saved physical errors differ')
    checked = sections(scores['errors_neu_m'], 800)
    if (any(encoded(checked[name]) != encoded(scores[name])
            or encoded(checked[name]) != encoded(result[name])
            for name in ('training', 'prediction'))
            or result['accuracy_all_sections'] != all(
                checked[name]['accuracy']['passed']
                for name in ('training', 'prediction'))):
        raise ValueError('oracle saved physical scores or accuracy labels differ')
    return dict(training=checked['training'], prediction=checked['prediction'],
                accurate=result['accuracy_all_sections'])


def inspect(root, prefix='data/noisy-realization-attribution-20261110'):
    """Require study closure, then verify hashes, charges and saved predictions."""
    from pathlib import Path
    from lll.studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, prefix)  # Refuse an open study before numerical imports.
    parent = None
    try:
        from lll.airquantumgrav_geographic_report import construction_counts
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_observed_hybrid_report import verify_qualification_report
        from lll.airquantumgrav_observed_report import verify_audit_environment
        from lll.noisy_realization_attribution import (
            SCOPE, collect_parent_bindings, comparison_rows,
            construction_limits, environment, qualification_sources,
            recipe, required_tests, tasks)
        from lll.studies.source_binding import verify

        design = study.input('recipe')
        proof = study.input('parent-proof')
        env = study.input('qualification-environment')
        request = study.input('qualification-request')
        declared = {row['identity']: row for row in tasks(proof['bindings'])}
        frozen = {identity: {key: value for key, value in task.items()
                             if key not in ('index', 'shard')}
                  for identity, task in study.tasks.items()}
        if (design != recipe() or proof != collect_parent_bindings(root)
                or study.manifest['scope'] != SCOPE or frozen != declared
                or request['environment'] != env
                or set(request['sources']) != set(qualification_sources(root))):
            raise ValueError('unchanged qualified six-stream oracle required')
        verify_audit_environment(env, environment())
        verify(root, declared=request['sources'],
               manifest=study.manifest['sources'])
        verify_qualification_report(study.input('qualification-report', raw=True),
                                    required_tests(),
                                    minimum_tests=len(required_tests()))
        parent = ClosedStudy(root, design['parent'])
        native = {}
        for shard in range(study.manifest['allocation']['workers']):
            assigned = {identity for identity, task in study.tasks.items()
                        if task['shard'] == shard}
            native.update(native_accounting(
                study.read(f'shards/{shard:03d}/charges/journal.sqlite', raw=True),
                study.completion['manifest_sha256'], assigned,
                per_call_visits=None))
        rows = []
        results = {}
        totals = {key: 0 for key in study.summary['charged']}
        for identity, task in study.tasks.items():
            row = dict(identity=identity, **task['payload'],
                       complete=False, accurate=False)
            if identity not in study.rows:
                rows.append(dict(row, reason='no sealed result'))
                continue
            envelope = study.envelope(identity)
            result = envelope['result']
            for path, sha in envelope['artifacts'].items():
                study.read(path, sha, raw=True)
            for key in totals:
                totals[key] += envelope['charged'][key]
            operations = native[identity]
            if (operations['tangent'] != 0
                    or operations['value'] != envelope['charged']['native_calls']
                    or operations['packet_visits'] !=
                    envelope['charged']['packet_visits']
                    or operations['value'] > task['limits']['native_calls']
                    or operations['packet_visits'] >
                    task['limits']['packet_visits']):
                raise ValueError('oracle native charges differ from sealed outcome')
            journal_path = 'artifacts/' + identity + '/construction.sqlite'
            construction = None
            if journal_path in envelope['artifacts']:
                construction = construction_counts(
                    study.read(journal_path,
                               envelope['artifacts'][journal_path], raw=True),
                    study.completion['manifest_sha256'], identity,
                    construction_limits(),
                    complete=result.get('technical_passed') is True)
            if result.get('technical_passed') is not True:
                rows.append(dict(row, reason=result.get('error',
                                                       'oracle task incomplete'),
                                 construction=construction,
                                 native=operations))
                continue
            names = ('input-binding.json', 'known-corrections.json',
                     'forecast.json', 'scoring-observations.json',
                     'scores.json', 'compilation.json')
            saved = {name: study.artifact(identity, name) for name in names}
            checked = check_case(
                task, result, saved, proof=proof,
                historical=proof['parent_recipe'],
                operations=operations, construction=construction,
                environment=dict(env, native_source_sha256=study.manifest[
                    'sources']['analysis/lll/ilvis0_native.c']))
            rows.append(dict(row, complete=True, **checked,
                             native=operations, construction=construction))
            results[identity] = result
        if totals != study.summary['charged']:
            raise ValueError('oracle whole-study charges differ')
        original = {identity: parent.envelope(identity)['result']
                    for item in proof['bindings']
                    for identity in item['parent_identities']}
        comparisons = (comparison_rows(proof['bindings'], original, results)
                       if len(results) == 6 else [])
        return dict(verified=True, qualified=len(comparisons) == 6,
                    total=6, complete=sum(row['complete'] for row in rows),
                    accurate=sum(row['accurate'] for row in rows),
                    rows=rows, comparisons=comparisons,
                    charged=totals, elapsed_s=study.summary['elapsed_s'],
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    parent_manifest_sha256=proof['parent_manifest_sha256'],
                    parent_summary_sha256=proof['parent_summary_sha256'],
                    native_calls_during_audit=0, original_reads=0,
                    protected_reads=0, confidence_calibrated=False,
                    scientific_decision='abstain')
    finally:
        if parent is not None:
            parent.close()
        study.close()


def render(report):
    """A compact public account of technical completion and physical errors."""
    if report.get('verified') is not True:
        raise ValueError('verified saved-result report required')
    lines = [
        '# What the same noisy IMU streams predict with known calibration',
        '',
        f"**{report['complete']}/{report['total']} oracle forecasts technically "
        f"complete; {report['accurate']} meet the existing physical accuracy screen.**",
        '',
        'This generated-data check uses six sensor streams. Four earlier fits of '
        'each stream shared the same noise path. The new calculation supplies '
        'the true starting state and calibration, then predicts the same later '
        'receiver positions. This is not aircraft evidence or an Earth-model vote.',
        '',
    ]
    if report['comparisons']:
        lines += [
            '| Generating candidate | Processing | Known-calibration later '
            'horizontal RMS | Earlier fitted range |',
            '|---|---|---:|---:|',
        ]
        for row in report['comparisons']:
            fitted = [fit['prediction']['horizontal_rms_m']
                      for fit in row['original_fits']]
            spread = f'{min(fitted):.3g}–{max(fitted):.3g} m'
            lines.append(
                f"| {row['model']} | {'Profiled' if row['profile'] else 'Zero'} "
                f"| {row['oracle_prediction']['horizontal_rms_m']:.3g} m "
                f'| {spread} |')
    else:
        lines += ['The six-way comparison is incomplete. Failed or missing '
                  'tasks remain in the sealed study record.']
    lines += [
        '',
        'Horizontal RMS is the typical horizontal prediction error over the '
        '400 later receiver epochs. The original fitted outcomes and failure '
        'labels have not been changed. A single synthetic noise seed cannot '
        'establish real-aircraft uncertainty or scientific significance.',
        '',
        '[Frozen plan](PLAN.md) · [Study index](../STUDIES.md)',
    ]
    return '\n'.join(lines) + '\n'


def publish(root, prefix='data/noisy-realization-attribution-20261110',
            output='docs/noisy-realization-attribution'):
    """Package a closed, independently audited study without recalculation."""
    import json
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic, digest, encoded, safe_path
    from lll.studies.publication import archive_publication

    root = Path(root).resolve()
    data = safe_path(root, prefix)
    public = safe_path(root, output)
    if (public / 'evidence-receipt.json').exists():
        raise ValueError('oracle publication already sealed')
    report = inspect(root, prefix)
    package(data, public, render(report),
            plan='docs/noisy-realization-attribution/PLAN.md')
    receipt = json.loads((public / 'evidence-receipt.json').read_bytes())
    for name, raw in [('verified-report.json', encoded(report)),
                      ('reporter.py', Path(__file__).read_bytes())]:
        name = 'artifacts/publication/' + name
        atomic(public / name, raw)
        receipt['artifacts'][name] = digest(raw)
    atomic(public / 'evidence-receipt.json', encoded(receipt))
    return dict(archive_publication(root, data, public), published=output,
                native_calls=0, original_reads=0, protected_reads=0)
