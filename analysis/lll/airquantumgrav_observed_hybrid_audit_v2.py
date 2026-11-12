# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent saved-result audit for the ESA paired tangent study."""


FORECAST_TOLERANCE_M = 0.01


def qualified_sources(root, request, manifest):
    """Verify the qualified closure and the runtime's separately frozen files."""
    from lll.airquantumgrav_observed_hybrid import qualification_sources
    from lll.studies.source_binding import verify

    declared = request.get('sources')
    if not isinstance(declared, dict) or set(declared) != set(qualification_sources(root)):
        raise ValueError('qualified paired-study source enumeration differs')
    return verify(root, declared=declared, manifest=manifest['sources'])


def substitution_qualified(rows, primary_checks, *, returned):
    """Require every pair and every distinct primary-selection group."""
    if (returned != 24 or len(rows) != 24 or len(primary_checks) != 12
            or any(row.get('passed') is not True for row in rows)
            or any(row.get('same') is not True for row in primary_checks)):
        return False
    groups = [(row['model'], row['profile'], row['policy_id'])
              for row in primary_checks]
    return len(set(groups)) == 12


def inspect(root, prefix='data/esa-observed-hybrid-pilot-20261110', *, study=None):
    """Replay saved fits and comparisons without fitting or reading originals."""
    from pathlib import Path
    from lll.studies.closed import ClosedStudy

    root = Path(root).resolve()
    if study is None:
        study = ClosedStudy(root, prefix)  # Reject an open study before numerical imports.
    elif study.root != root:
        raise ValueError('combined study belongs to another project')
    baseline = None
    try:
        import gzip
        import io
        import json
        import math
        import numpy as np
        from lll.airquantumgrav_inventory import environment
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_observed_hybrid import (
            PARENTS, SCOPE, parent_proof, recipe, required_tests, tasks)
        from lll.airquantumgrav_observed_hybrid_report import (
            compare_pair, verify_compilation, verify_qualification_report)
        from lll.airquantumgrav_observed_report import verify_audit_environment
        from lll.airquantumgrav_observed_wide_report import verify_compilation as verify_wide
        from lll.airquantumgrav_scoring import receiver_errors, sections
        from lll.ilvis0_wide_observed import SOURCES, bind
        from lll.prediction_audit import complete_prediction
        from lll.studies.artifacts import digest, encoded

        r = study.input('recipe')
        env = study.input('qualification-environment')
        request = study.input('qualification-request')
        verify_audit_environment(env, environment())
        source_proof = qualified_sources(root, request, study.manifest)
        verify_qualification_report(study.input('qualification-report', raw=True),
                                    required_tests(), minimum_tests=60)
        layout = study.input('layout')
        declared = {task['identity']: task for task in tasks(layout)}
        frozen = {identity: {key: value for key, value in task.items()
                             if key not in ('index', 'shard')}
                  for identity, task in study.tasks.items()}
        if (r != recipe(maximum_wall_s=r['maximum_wall_s'])
                or study.manifest['scope'] != SCOPE
                or request['environment'] != env
                or study.input('parent-proof') != parent_proof(root)
                or frozen != declared):
            raise ValueError('unchanged paired study, parents and finite tasks required')
        baseline = ClosedStudy(root, PARENTS['wide'][0])
        copied = [key for key in baseline.manifest['inputs']
                  if key not in ('recipe', 'qualification-request',
                                 'qualification-report', 'qualification-environment',
                                 'protocol-binding')]
        if any(study.input(key, raw=True) != baseline.input(key, raw=True)
               for key in copied):
            raise ValueError('prepared measurements, selection or split differ')
        _, protocol = bind(expected_sources={
            name: study.manifest['sources']['analysis/lll/' + name]
            for name in SOURCES})
        if protocol != study.input('protocol-binding'):
            raise ValueError('current frozen observed protocol differs')
        training = json.loads(gzip.decompress(study.input('training', raw=True)))
        scoring = json.loads(gzip.decompress(study.input('scoring', raw=True)))
        query = study.input('query-layout')
        times = query['times_s']
        cut = query['training_epochs']
        if (cut != 800 or len(times) != 1200 or len(training) != cut
                or len(scoring) != len(times)
                or encoded(training) != encoded(scoring[:cut])):
            raise ValueError('complete unchanged earlier/later receiver split required')
        with np.load(io.BytesIO(study.input('interval', raw=True)),
                     allow_pickle=False) as archive:
            arrays = {key: archive[key] for key in ('theta', 'dv', 'dt')}
        n = layout['native_packets']
        prefix_packets = layout['training_prefix_packets']
        if (n != 360028 or arrays['theta'].shape != (n, 3)
                or arrays['dv'].shape != (n, 3) or arrays['dt'].shape != (n,)
                or prefix_packets != int(np.searchsorted(
                    np.cumsum(arrays['dt']), times[cut-1] + r['limits']['time_offset'],
                    side='left')) + 1):
            raise ValueError('unchanged IMU packet and training support required')
        hashes = {key: digest(value[:prefix_packets].astype('<f8', copy=False).tobytes())
                  for key, value in arrays.items()}
        gps = np.array([[math.radians(row['latitude_deg']),
                         math.radians(row['longitude_deg']), row['height_m']]
                        for row in scoring])
        anchor = training[0]['height_m']
        weights = study.input('working-errors')
        source = 'analysis/lll/ilvis0_tangent.cpp'
        original = study.read('source-freeze/' + source,
                              study.manifest['sources'][source], raw=True)
        if hasattr(study, 'native_by_identity'):
            native = study.native_by_identity(native_accounting)
        else:
            native = {}
            for shard in range(study.manifest['allocation']['workers']):
                identities = {identity for identity, task in study.tasks.items()
                              if task['shard'] == shard}
                native.update(native_accounting(
                    study.read(f'shards/{shard:03d}/charges/journal.sqlite', raw=True),
                    study.completion['manifest_sha256'], identities,
                    per_call_visits=None))
        rows = []
        charged = {key: 0 for key in study.summary['charged']}
        for identity, task in study.tasks.items():
            if identity not in study.rows:
                rows.append(dict(identity=identity, **task['payload'],
                                 returned=False, passed=False,
                                 reason='no sealed result'))
                continue
            expected_input_hashes = ({key: value['sha256']
                for key, value in study.origin_manifest(identity)['inputs'].items()}
                if hasattr(study, 'origin_manifest') else
                {key: value['sha256'] for key, value in study.manifest['inputs'].items()})
            envelope = study.envelope(identity)
            for path, sha in envelope['artifacts'].items():
                if hasattr(study, 'read_artifact'):
                    study.read_artifact(identity, path, sha, raw=True)
                else:
                    study.read(path, sha, raw=True)
            for key in charged:
                charged[key] += envelope['charged'][key]
            operations = native[identity]
            if (operations['value'] != 0
                    or operations['tangent'] != envelope['charged']['native_calls']
                    or operations['packet_visits'] != envelope['charged']['packet_visits']):
                raise ValueError('whole-case native charge record differs')
            result = envelope['result']
            row = dict(identity=identity, **task['payload'], returned=True,
                       passed=bool(result.get('passed')),
                       charged_native_calls=operations['tangent'])
            if (result.get('original_reads', 0) != 0
                    or result.get('protected_reads', 0) != 0
                    or result.get('scientific_decision', 'abstain') != 'abstain'):
                raise ValueError('development-only evidence scope required')
            if not all(name in result for name in ('wide', 'hybrid', 'comparison')):
                row['reason'] = result.get('error', result.get('reason',
                                             'paired calculation incomplete'))
                rows.append(row)
                continue
            checks = {}
            expected_calls = 0
            expected_visits = 0
            for variant in ('wide', 'hybrid'):
                part = result[variant]
                fit = study.artifact(identity, variant + '-fit.json')
                forecast = study.artifact(identity, variant + '-forecast.json')
                earlier = study.artifact(identity, variant + '-training-observations.json')
                binding = study.artifact(identity, variant + '-input-binding.json')
                saved_scores = study.artifact(identity, variant + '-scores.json')
                compilation = study.artifact(identity, variant + '-compilation.json')
                if study.artifact(identity, 'protocol-binding.json') != protocol:
                    raise ValueError('case protocol binding differs')
                if variant == 'wide':
                    verify_wide(meta=compilation, raw=original,
                                sources=study.manifest['sources'],
                                environment=env, anchor=anchor)
                else:
                    verify_compilation(compilation, original_source=original,
                                       sources=study.manifest['sources'],
                                       environment=env, anchor=anchor)
                spec = task['payload']
                active = [name + '_' + axis
                          for name in ('attitude', 'velocity', 'position',
                                       'gyro_bias', 'accel_bias', 'gyro_gain',
                                       'accel_gain', 'lever') for axis in 'xyz']
                active += ['gravity_delta', 'time_offset']
                if spec['profile']:
                    active.append('earth_removal')
                weight = weights[spec['policy_id']]
                visits = fit['evaluations'] * prefix_packets * cut + n * len(times)
                expected = dict(active=active,
                                maximum_evaluations=r['maximum_evaluations'],
                                times=times, cut=cut,
                                training_coordinates=gps[:cut].tolist(),
                                prefix_packets=prefix_packets,
                                prefix_sha256=hashes,
                                configuration=weight['configuration'],
                                descriptor=weight['descriptor'],
                                weight_sha256=weight['training_source_sha256'],
                                time_origin_s=query['time_origin_gps_sow_s'],
                                group=study.input('context')['group_id'],
                                layout=layout, input_sha256=expected_input_hashes,
                                packet_visits=visits)
                own_operations = dict(value=0, tangent=fit['evaluations'] + 1,
                                      packet_visits=visits)
                complete_prediction(spec=spec, result=part, fit=fit,
                                    forecast=forecast, earlier=earlier,
                                    binding=binding, operations=own_operations,
                                    expected=expected)
                errors = receiver_errors(forecast['coordinates'], gps)
                scores = sections(errors, cut)
                if (saved_scores['times_s'] != times
                        or saved_scores['receiver_coordinates'] != gps.tolist()
                        or not np.array_equal(np.asarray(saved_scores['errors_neu_m']), errors)
                        or any(encoded(saved_scores[key]) != encoded(value)
                               or encoded(part[key]) != encoded(value)
                               for key, value in scores.items())
                        or part['accuracy_all_sections'] != all(
                            value['accuracy']['passed'] for value in scores.values())):
                    raise ValueError('saved receiver scores or adequacy labels differ')
                checks[variant] = dict(passed=part['passed'],
                                       accuracy_all_sections=part['accuracy_all_sections'],
                                       training_cost=part['training_cost'],
                                       later_total_rms_m=scores['prediction']['total_rms_m'])
                expected_calls += own_operations['tangent']
                expected_visits += visits
            if (expected_calls != operations['tangent']
                    or expected_visits != operations['packet_visits']):
                raise ValueError('paired charges do not add to native journal')
            if result['wide']['passed'] and result['hybrid']['passed']:
                comparison = compare_pair(
                    result['wide'], result['hybrid'],
                    study.artifact(identity, 'wide-fit.json'),
                    study.artifact(identity, 'hybrid-fit.json'),
                    study.artifact(identity, 'wide-forecast.json'),
                    study.artifact(identity, 'hybrid-forecast.json'),
                    tolerance_m=FORECAST_TOLERANCE_M)
            else:
                comparison = dict(passed=False,
                                  reason='at least one matched numerical fit did not qualify')
            if (encoded(comparison) != encoded(result['comparison'])
                    or encoded(comparison) != encoded(study.artifact(identity, 'comparison.json'))
                    or result['passed'] != comparison['passed']):
                raise ValueError('paired saved comparison differs from independent replay')
            row.update(wide=checks['wide'], hybrid=checks['hybrid'],
                       comparison=comparison)
            rows.append(row)
        if charged != study.summary['charged']:
            raise ValueError('whole-study resource charges differ')
        primary_checks = []
        for model in r['models']:
            for profile in r['profiles']:
                for policy in r['policies']:
                    identities = [f'{model}-{int(profile)}-{policy}-{start}'
                                  for start in range(r['starts'])]
                    if all(identity in study.rows and all(
                            study.envelope(identity)['result'].get(variant, {}).get('passed')
                            for variant in ('wide', 'hybrid')) for identity in identities):
                        selected = [min(identities, key=lambda identity: (
                            study.envelope(identity)['result'][variant]['training_cost'],
                            study.tasks[identity]['payload']['start']))
                            for variant in ('wide', 'hybrid')]
                        primary_checks.append(dict(model=model, profile=profile,
                                                   policy_id=policy,
                                                   same=selected[0] == selected[1],
                                                   wide=selected[0], hybrid=selected[1]))
        qualified = substitution_qualified(rows, primary_checks,
                                           returned=len(study.rows))
        return dict(verified=True, qualified=qualified,
                    total=24, returned=len(study.rows),
                    passed=sum(row['passed'] for row in rows),
                    errors=sum(not row['passed'] for row in rows),
                    charged=charged, rows=rows,
                    primary_checks=primary_checks,
                    historical_wide_qualified_starts=22,
                    historical_wide_deadline_failures=2,
                    source_proof=source_proof,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    audit_source_sha256=digest((root / 'analysis/lll/airquantumgrav_observed_hybrid_audit_v2.py').read_bytes()),
                    original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        if baseline is not None:
            baseline.close()
        study.close()


def pair_rows(report):
    """Flatten key fields from every sealed outcome for a readable case table."""
    result = []
    for row in report['rows']:
        wide = row.get('wide') or {}
        hybrid = row.get('hybrid') or {}
        comparison = row.get('comparison') or {}
        result.append(dict(
            identity=row['identity'], model=row.get('model'),
            profile=row.get('profile'), policy_id=row.get('policy_id'),
            start=row.get('start'), returned=row['returned'],
            passed=row['passed'],
            wide_passed=wide.get('passed'),
            hybrid_passed=hybrid.get('passed'),
            wide_training_cost=wide.get('training_cost'),
            hybrid_training_cost=hybrid.get('training_cost'),
            wide_later_rms_m=wide.get('later_total_rms_m'),
            hybrid_later_rms_m=hybrid.get('later_total_rms_m'),
            maximum_position_difference_m=comparison.get('maximum_position_difference_m'),
            training_cost_difference=comparison.get('training_cost_difference'),
            reason=row.get('reason') or comparison.get('reason') or ''))
    return result


def render(report):
    """Summarize the independently replayed study without promoting its result."""
    if (not isinstance(report, dict) or report.get('verified') is not True
            or report.get('total') != 24 or len(report.get('rows', ())) != 24
            or report.get('passed', -1) + report.get('errors', -1) != 24
            or report.get('returned', -1) > 24):
        raise ValueError('complete verified 24-pair audit required')
    qualified = report['qualified'] is True
    if qualified != substitution_qualified(
            report['rows'], report.get('primary_checks', ()),
            returned=report['returned']):
        raise ValueError('qualified label contradicts paired or primary results')
    status = 'qualified' if qualified else 'did not qualify'
    lines = [
        '# ESA paired tangent check', '',
        f"**{report['passed']}/24 pairs passed; the substitution {status}.**", '',
        'Both variants used the same prepared development measurements and the '
        'same current fitting source. The tangent calculation was the only '
        'within-pair change.', '',
        f"The historical pilot had {report['historical_wide_qualified_starts']} "
        'earlier qualified wide starts and '
        f"{report['historical_wide_deadline_failures']} deadline failures. "
        'Its older fitting source makes those outcomes historical context, '
        'not the paired reference.', '',
    ]
    failures = [row for row in report['rows'] if not row['passed']]
    if failures:
        lines += ['## Failed or incomplete pairs', '', '| Case | Reason |',
                  '|---|---|']
        for row in failures:
            reason = row.get('reason') or row.get('comparison', {}).get('reason') or 'audit gate failed'
            lines.append(f"| {row['identity']} | {reason} |")
        lines.append('')
    checks = report.get('primary_checks', ())
    lines += [f"Training-cost primary starts agree in {sum(row['same'] for row in checks)}/{len(checks)} "
              'complete start groups.', '',
              'This software-method check is not an Earth-model detection, '
              'independent flight replication or calibrated uncertainty result.', '',
              '[All 24 case outcomes](pair-results.csv) · '
              '[Frozen plan](PLAN.md) · [Audit plan](AUDIT_PLAN.md).', '']
    return '\n'.join(lines)


def publish(root, prefix='data/esa-observed-hybrid-pilot-20261110',
            output='docs/esa-observed-hybrid'):
    """Publish a closed, independently replayed study without fitting."""
    import csv
    import io
    import json
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic, digest, encoded, safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.publication import archive_publication

    root = Path(root).resolve()
    data = safe_path(root, prefix)
    public = safe_path(root, output)
    if (public / 'evidence-receipt.json').exists():
        raise ValueError('paired ESA publication already sealed')
    report = inspect(root, prefix)
    study = ClosedStudy(root, prefix)
    try:
        plan_hash = study.manifest['sources']['docs/esa-observed-hybrid/PLAN.md']
    finally:
        study.close()
    if digest((public / 'PLAN.md').read_bytes()) != plan_hash:
        raise ValueError('preserved paired plan differs')
    rows = pair_rows(report)
    if len(rows) != 24:
        raise ValueError('all 24 case outcomes required')
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    package(data, public, render(report), plan='docs/esa-observed-hybrid/PLAN.md')
    receipt = json.loads((public / 'evidence-receipt.json').read_bytes())
    for name, raw in (
            ('artifacts/publication/verified-report.json', encoded(report)),
            ('artifacts/publication/reporter.py', Path(__file__).read_bytes()),
            ('pair-results.csv', stream.getvalue().encode())):
        atomic(public / name, raw)
        receipt['artifacts'][name] = digest(raw)
    receipt['artifacts']['AUDIT_PLAN.md'] = digest((public / 'AUDIT_PLAN.md').read_bytes())
    atomic(public / 'evidence-receipt.json', encoded(receipt))
    return dict(archive_publication(root, data, public),
                published=output, original_reads=0, native_calls=0)
