# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit of the selective-tangent ESA development substitution."""


def compare_pair(reference, candidate, reference_fit, candidate_fit,
                 reference_forecast, candidate_forecast, *, tolerance_m):
    import math
    import numpy as np
    from lll.airquantumgrav_scoring import receiver_errors

    if reference.get('passed') is not True:
        raise ValueError('qualified reference start required')
    if not math.isfinite(tolerance_m) or tolerance_m <= 0:
        raise ValueError('positive fixed physical tolerance required')
    spec = ('model', 'profile', 'policy_id', 'start')
    same_case = all(reference.get(key) == candidate.get(key) for key in spec)
    old_columns = reference_fit.get('active_parameters')
    new_columns = candidate_fit.get('active_parameters')
    columns_retained = (isinstance(old_columns, list)
                        and len(old_columns) == len(set(old_columns))
                        and old_columns == new_columns
                        and candidate.get('all_columns_retained') is True)
    old_coordinates = reference_forecast['coordinates']
    new_coordinates = candidate_forecast['coordinates']
    same_times = (reference_forecast['times_s'] == candidate_forecast['times_s']
                  and len(old_coordinates) == len(new_coordinates))
    if same_times:
        delta = receiver_errors(new_coordinates, old_coordinates)
        maximum = float(np.max(np.linalg.norm(delta, axis=1)))
    else:
        maximum = float('inf')
    same_decisions = all(reference.get(key) == candidate.get(key)
                         for key in ('passed', 'converged',
                                     'accuracy_all_sections', 'all_columns_retained'))
    isolated = (reference_forecast.get('prediction_receiver_positions_used') is False
                and candidate_forecast.get('prediction_receiver_positions_used') is False)
    cost_difference = abs(float(candidate_fit['residual_sum_squares'])
                          - float(reference_fit['residual_sum_squares']))
    passed = (same_case and same_times and same_decisions and columns_retained
              and isolated and maximum <= tolerance_m
              and math.isfinite(cost_difference)
              and candidate_fit.get('converged') == reference_fit.get('converged'))
    return dict(passed=passed, same_case=same_case, same_times=same_times,
                same_decisions=same_decisions, all_columns_retained=columns_retained,
                later_positions_isolated=isolated,
                maximum_position_difference_m=maximum,
                training_cost_difference=cost_difference)


def verify_compilation(meta, *, original_source, sources, environment, anchor):
    import hashlib
    from lll.ilvis0_hybrid_tangent import derive as hybrid_derive, FAST_COLUMNS, WIDE_COLUMNS, VERSION
    from lll.ilvis0_wide_tangent import derive as wide_derive
    from lll.studies.artifacts import digest

    sha = sources['analysis/lll/ilvis0_tangent.cpp']
    wide = wide_derive(original_source, expected_sha256=sha)
    hybrid = hybrid_derive(wide, expected_sha256=hashlib.sha256(wide).hexdigest())
    value, tangent = meta['value'], meta['tangent']
    if (digest(original_source) != sha
            or value['source_sha256'] != sources['analysis/lll/ilvis0_native.c']
            or value['compiler'] != environment['compilers']['cc']
            or tangent['compiler'] != environment['compilers']['c++']
            or tangent['version'] != VERSION
            or tangent['source_sha256'] != digest(hybrid)
            or tangent['original_source_sha256'] != sha
            or tangent['shared_loader_source_sha256'] != sources['analysis/lll/ilvis0_wide_tangent.py']
            or tangent['shared_loader_unchanged'] is not True
            or tangent['wide_derivative_columns'] != list(WIDE_COLUMNS)
            or tangent['fast_derivative_columns'] != list(FAST_COLUMNS)
            or tangent['production_method_changed'] is not False
            or value['gravity_anchor_height_m'] != anchor
            or tangent['gravity_anchor_height_m'] != anchor):
        raise ValueError('compiled selective tangent or source binding differs')


def verify_qualification_report(raw, required_tests, *, minimum_tests):
    import xml.etree.ElementTree as ET

    tree = ET.fromstring(raw)
    suites = list(tree.iter('testsuite'))
    cases = list(tree.iter('testcase'))
    names = [case.attrib['name'] for case in cases]
    identities = [(case.attrib.get('classname', ''), case.attrib['name'])
                  for case in cases]
    failed = (any(node.tag in ('failure', 'error', 'skipped')
                  for case in cases for node in case.iter())
              or any(int(suite.attrib.get(key, 0))
                     for suite in suites
                     for key in ('errors', 'failures', 'skipped')))
    if (not suites or failed or len(cases) < minimum_tests
            or len(set(identities)) != len(cases)
            or not set(required_tests) <= set(names)):
        raise ValueError('complete source-bound passing tests required')


def inspect(root, prefix='data/esa-observed-hybrid-pilot-20261110'):
    from pathlib import Path
    from lll.studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, prefix)  # Require closure before numerical imports.
    baseline = None
    try:
        import gzip
        import json
        from lll.airquantumgrav_inventory import environment
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_observed_hybrid import (
            PARENTS, SCOPE, parent_proof, qualification_sources,
            recipe, required_tests, tasks)
        from lll.airquantumgrav_observed_report import verify_audit_environment
        from lll.airquantumgrav_observed_wide_report import verify_compilation as verify_wide
        from lll.ilvis0_wide_observed import SOURCES, bind
        from lll.studies.artifacts import encoded
        from lll.studies.source_binding import verify

        r = study.input('recipe')
        env = study.input('qualification-environment')
        verify_audit_environment(env, environment())
        if (r != recipe(maximum_wall_s=r['maximum_wall_s'])
                or study.manifest['scope'] != SCOPE
                or study.input('parent-proof') != parent_proof(root)
                or set(study.tasks) != {case['identity']
                                      for case in tasks(study.input('layout'))}):
            raise ValueError('unchanged closed selective-tangent study required')
        declared = study.input('qualification-request')['sources']
        if set(declared) != set(qualification_sources(root)):
            raise ValueError('qualified source enumeration changed')
        verify(root, declared=declared, manifest=study.manifest['sources'])
        if (study.input('qualification-request')['environment'] != env
                or declared != study.manifest['sources']):
            raise ValueError('source-bound qualification differs from study')
        verify_qualification_report(study.input('qualification-report', raw=True),
                                    required_tests(), minimum_tests=60)
        baseline = ClosedStudy(root, PARENTS['wide'][0])
        copied = [key for key in baseline.manifest['inputs']
                  if key not in ('recipe', 'qualification-request',
                                 'qualification-report', 'qualification-environment',
                                 'protocol-binding')]
        if any(study.input(key, raw=True) != baseline.input(key, raw=True)
               for key in copied):
            raise ValueError('saved observed inputs differ from wide reference')
        _, protocol = bind(expected_sources={
            name: study.manifest['sources']['analysis/lll/' + name]
            for name in SOURCES})
        if protocol != study.input('protocol-binding'):
            raise ValueError('frozen observed protocol differs')
        source = 'analysis/lll/ilvis0_tangent.cpp'
        original = study.read('source-freeze/' + source,
                              study.manifest['sources'][source], raw=True)
        native = {}
        anchor = json.loads(gzip.decompress(study.input('training', raw=True)))[0]['height_m']
        for shard in range(study.manifest['allocation']['workers']):
            identities = {identity for identity, task in study.tasks.items()
                          if task['shard'] == shard}
            native.update(native_accounting(
                study.read(f'shards/{shard:03d}/charges/journal.sqlite', raw=True),
                study.completion['manifest_sha256'], identities,
                per_call_visits=None))
        pairs = []
        rows = []
        for identity, task in study.tasks.items():
            if identity not in study.rows:
                rows.append(dict(identity=identity, returned=False, passed=False))
                pairs.append(dict(identity=identity, passed=False,
                                  reason='no returned matched fit'))
                continue
            envelope = study.envelope(identity)
            result = envelope['result']
            if (result.get('original_reads', 0) != 0
                    or result.get('protected_reads', 0) != 0
                    or result.get('scientific_decision', 'abstain') != 'abstain'):
                raise ValueError('development-only abstaining result required')
            for path, sha in envelope['artifacts'].items():
                study.read(path, sha, raw=True)
            operations = native[identity]
            if (operations['value'] != 0
                    or operations['tangent'] != envelope['charged']['native_calls']
                    or operations['packet_visits'] != envelope['charged']['packet_visits']):
                raise ValueError('native charge record differs')
            row = dict(identity=identity, returned=True,
                       passed=bool(result.get('passed')),
                       model=task['payload']['model'],
                       profile=task['payload']['profile'],
                       policy_id=task['payload']['policy_id'],
                       start=task['payload']['start'])
            rows.append(row)
            if not all(key in result for key in ('wide', 'hybrid', 'comparison')):
                pairs.append(dict(identity=identity, passed=False,
                                  reason=result.get('error', result.get('reason',
                                           'paired result incomplete'))))
                continue
            for variant in ('wide', 'hybrid'):
                part = result[variant]
                if (any(part.get(key) != task['payload'][key]
                        for key in ('model', 'profile', 'policy_id', 'start'))
                        or part.get('group_id') != study.input('context')['group_id']
                        or part.get('original_reads') != 0
                        or part.get('protected_reads') != 0
                        or part.get('scientific_decision') != 'abstain'):
                    raise ValueError('paired variant changes case, group or evidence scope')
                compilation = study.artifact(identity, variant + '-compilation.json')
                if variant == 'wide':
                    verify_wide(meta=compilation, raw=original,
                                sources=study.manifest['sources'],
                                environment=env, anchor=anchor)
                else:
                    verify_compilation(compilation, original_source=original,
                                       sources=study.manifest['sources'],
                                       environment=env, anchor=anchor)
                if study.artifact(identity, variant + '-input-binding.json') != dict(
                        group_id=study.input('context')['group_id'],
                        layout=study.input('layout'),
                        input_sha256={key: value['sha256']
                                      for key, value in study.manifest['inputs'].items()},
                        original_reads=0, protected_reads=0):
                    raise ValueError('paired input binding differs')
            if (result['wide']['passed'] and result['hybrid']['passed']):
                paired = compare_pair(
                    result['wide'], result['hybrid'],
                    study.artifact(identity, 'wide-fit.json'),
                    study.artifact(identity, 'hybrid-fit.json'),
                    study.artifact(identity, 'wide-forecast.json'),
                    study.artifact(identity, 'hybrid-forecast.json'),
                    tolerance_m=.01)
            else:
                paired = dict(passed=False,
                              reason='at least one matched numerical fit did not qualify')
            if (encoded(paired) != encoded(result['comparison'])
                    or encoded(paired) != encoded(study.artifact(identity, 'comparison.json'))
                    or result['passed'] != paired['passed']
                    or envelope['charged']['native_calls'] !=
                    result['wide']['native_calls'] + result['hybrid']['native_calls']):
                raise ValueError('saved paired comparison or charge differs')
            pairs.append(dict(identity=identity, **paired))
        if len(pairs) != 24:
            raise ValueError('exact 24 new pairs required')
        primary_checks = []
        for model in r['models']:
            for profile in r['profiles']:
                for policy in r['policies']:
                    identities = [f'{model}-{int(profile)}-{policy}-{start}'
                                  for start in range(r['starts'])]
                    if all(identity in study.rows
                           and all(study.envelope(identity)['result'].get(variant, {}).get('passed')
                                   for variant in ('wide', 'hybrid'))
                           for identity in identities):
                        selected = []
                        for variant in ('wide', 'hybrid'):
                            selected.append(min(identities, key=lambda identity: (
                                study.envelope(identity)['result'][variant]['training_cost'],
                                study.tasks[identity]['payload']['start'])))
                        primary_checks.append(dict(model=model, profile=profile,
                                                   policy_id=policy,
                                                   same=selected[0] == selected[1],
                                                   reference=selected[0], candidate=selected[1]))
        gate = len(study.rows) == 24 and all(row['passed'] for row in pairs) and all(
            row['same'] for row in primary_checks)
        return dict(verified=True, qualified=gate,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    total=24, returned=len(study.rows),
                    matched_reference_starts=22,
                    matched_passed=sum(row['passed'] for row in pairs),
                    historical_wide_deadline_failures=2,
                    rows=rows, pairs=pairs, primary_checks=primary_checks,
                    original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        if baseline is not None:
            baseline.close()
        study.close()
