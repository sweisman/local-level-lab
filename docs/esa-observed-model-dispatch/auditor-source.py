# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only result gate for model-declared tangent substitution."""

import math
import hashlib
import json
import csv
import io


MODELS = ('sphere_rotating', 'sphere_still')
POLICIES = ('reported-short-v1', 'reported-persistent-v1')
SAVED_FLAT_FAILURE = 'flat_still-1-reported-short-v1-0'
STUDY = 'data/esa-observed-model-dispatch-globe-pairs-v2'
PUBLIC = 'docs/esa-observed-model-dispatch'


def publish(root, *, prefix=STUDY, output=PUBLIC):
    """Seal a closed, replayed result. The receipt is written last."""
    from pathlib import Path
    from lll.studies.artifacts import atomic, digest, encoded, safe_path

    root = Path(root).resolve()
    public = safe_path(root, output)
    receipt_path = safe_path(public, 'evidence-receipt.json')
    if receipt_path.exists():
        raise ValueError('dispatch publication already sealed')
    report = inspect(root, prefix)
    materials = publication_artifacts(report)
    hashes = {}
    for name, raw in materials.items():
        atomic(safe_path(public, name), raw)
        hashes[name] = digest(raw)
    receipt = dict(version='esa-dispatch-publication-v1',
                   artifacts=hashes, cases=24,
                   qualified=report['qualified'],
                   manifest_sha256=report['manifest_sha256'],
                   summary_sha256=report['summary_sha256'],
                   original_reads=0, protected_reads=0,
                   scientific_decision='abstain')
    atomic(receipt_path, encoded(receipt))
    return dict(published=output, qualified=report['qualified'], cases=24,
                receipt_sha256=digest(encoded(receipt)))


def verify_publication(root, *, prefix=STUDY, output=PUBLIC):
    """Regenerate public bytes from sealed evidence and compare every hash."""
    from pathlib import Path
    from lll.studies.artifacts import digest, safe_path

    root = Path(root).resolve()
    public = safe_path(root, output)
    receipt_raw = safe_path(public, 'evidence-receipt.json').read_bytes()
    receipt = json.loads(receipt_raw)
    report = inspect(root, prefix)
    materials = publication_artifacts(report)
    if (receipt.get('version') != 'esa-dispatch-publication-v1'
            or receipt.get('cases') != 24
            or receipt.get('qualified') != report['qualified']
            or receipt.get('manifest_sha256') != report['manifest_sha256']
            or receipt.get('summary_sha256') != report['summary_sha256']
            or receipt.get('original_reads') != 0
            or receipt.get('protected_reads') != 0
            or receipt.get('scientific_decision') != 'abstain'
            or set(receipt.get('artifacts', {})) != set(materials)):
        raise ValueError('publication receipt differs from closed study')
    for name, expected in materials.items():
        if (digest(expected) != receipt['artifacts'][name]
                or safe_path(public, name).read_bytes() != expected):
            raise ValueError('published evidence changed: ' + name)
    return dict(verified=True, artifacts=len(materials),
                receipt_sha256=digest(receipt_raw))


def publication_artifacts(report):
    """Build a compact, path-free public record from a verified closed audit."""
    from pathlib import Path
    from lll.studies.artifacts import encoded

    page = render(report)
    auditor = Path(__file__).read_bytes()
    fields = ('origin', 'identity', 'model', 'profile', 'policy_id', 'start',
              'wide_passed', 'selected_passed', 'comparison_passed',
              'wide_training_cost', 'selected_training_cost', 'reason')
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for origin, rows in (('new_globe', report['rows']),
                         ('saved_flat', report['flat_rows'])):
        for row in sorted(rows, key=lambda item: item['identity']):
            public = {key: row.get(key) for key in fields if key != 'reason'}
            public['origin'] = origin
            public['reason'] = (
                'saved flat numerical fit did not qualify'
                if origin == 'saved_flat' and not row['comparison_passed']
                else _public_reason(row.get('reason'))
                if not row['comparison_passed'] else '')
            writer.writerow(public)
    summary_keys = ('verified', 'qualified', 'state', 'study',
                    'globe_pairs_passed', 'globe_pairs_total',
                    'primary_groups_agree', 'primary_groups_total',
                    'flat_identity_count', 'flat_numerical_failures_retained',
                    'manifest_sha256', 'summary_sha256', 'charged')
    summary = {key: report[key] for key in summary_keys if key in report}
    summary['scientific_decision'] = 'abstain'
    summary['auditor_sha256'] = hashlib.sha256(auditor).hexdigest()
    return {'README.md': page.encode(),
            'pair-results.csv': output.getvalue().encode(),
            'verified-report.json': encoded(summary),
            'auditor-source.py': auditor}


def _public_reason(reason):
    if reason in {
            'no sealed result',
            'paired calculation incomplete',
            'at least one matched numerical fit did not qualify',
            'paired method check failed',
    }:
        return reason
    return 'saved calculation did not complete'


def render(report):
    """Explain a verified method result without presenting a physical claim."""
    if (report.get('verified') is not True
            or report.get('state') not in ('complete', 'terminal')):
        raise ValueError('closed verified report required')
    decision = assess(report['rows'], report['flat_rows'])
    if any(report.get(key) != value for key, value in decision.items()):
        raise ValueError('qualified label or pair count differs from replay')
    status = 'qualified' if decision['qualified'] else 'did not qualify'
    lines = [
        '# ESA model-declared tangent check', '',
        f"**{decision['globe_pairs_passed']}/16 globe-method comparisons matched; "
        f"the faster method {status}.**", '',
        'This compares two ways of calculating the same model on one ESA',
        'development recording. Each pair uses the same prepared measurements',
        'and fitting rules. The selected calculation must reproduce the',
        'established wide calculation to within 0.01 m at every withheld',
        'receiver position and choose the same primary training start.', '',
        f"Primary starts agree in {decision['primary_groups_agree']}/8 "
        'globe model/processing groups. The flat candidate keeps the',
        'established wide calculation, including one saved flat numerical failure.',
        '',
        'This is a software-method check, not an Earth-model decision.',
        'It does not calibrate aircraft prediction error or statistical confidence.',
    ]
    failed = [row for row in report['rows'] if not row['comparison_passed']]
    if failed:
        lines += ['', '## Pairs that did not pass', '']
        for row in failed:
            lines.append(f"- `{row['identity']}`: "
                         f"{_public_reason(row.get('reason'))}")
    lines += ['', '[Frozen observed plan](../OBSERVED_DISPATCH_PLAN.md) · '
              '[Earlier flat identity audit](../MODEL_DISPATCH_RESULT.md).', '']
    return '\n'.join(lines)


def verify_charge_totals(native, charged):
    """Include charged work even when a task has no sealed fit result."""
    totals = dict(native_calls=sum(row['value'] + row['tangent']
                                   for row in native.values()),
                  packet_visits=sum(row['packet_visits']
                                    for row in native.values()),
                  bound_calls=0, bound_steps=0)
    if totals != charged or any(row['value'] for row in native.values()):
        raise ValueError('native journal totals differ from study charge summary')
    return totals


def load_frozen_flat(study):
    """Use the study's hash-checked source copy, never a mutable docs path."""
    from lll.airquantumgrav_observed_dispatch import SAVED_AUDIT

    return load_saved_flat(study.read(
        'source-freeze/' + SAVED_AUDIT,
        study.manifest['sources'][SAVED_AUDIT], raw=True))


def verify_qualified_sources(root, declared, manifest, *, expected_names):
    """Allow only Definition's recorded runtime extension to qualified sources."""
    from lll.studies.source_binding import verify

    if set(declared) != set(expected_names):
        raise ValueError('qualified source enumeration changed')
    return verify(root, declared=declared, manifest=manifest)


def verify_declared_method(meta, model):
    from lll.ilvis0_tangent_dispatch import VERSION, method_for_model

    if (model not in MODELS or
            {key: meta.get('tangent', {}).get(key) for key in (
                'dispatch_version', 'dispatch_model', 'dispatch_method',
                'scientific_decision')} != dict(
                    dispatch_version=VERSION, dispatch_model=model,
                    dispatch_method=method_for_model(model),
                    scientific_decision='abstain')):
        raise ValueError('compiled method differs from predeclared globe choice')


def verify_contract(manifest):
    """Reject a different study, matrix or finite work allowance."""
    from lll.airquantumgrav_observed_dispatch import IDENTITY, SCOPE

    if (manifest.get('adapter') !=
            'analysis/lll/airquantumgrav_observed_dispatch.py'
            or manifest.get('scope') != SCOPE
            or manifest.get('scientific_decision') != 'abstain'
            or manifest.get('allocation') != dict(workers=4, threads=1,
                                                  total=4, reserved=0)
            or manifest.get('limits') != dict(
                maximum_identities=16, maximum_wall_s=108000.0,
                native_calls=6432, packet_visits=1241944115200,
                bound_calls=0, bound_steps=0)):
        raise ValueError(f'expected {IDENTITY} v2 study contract')
    tasks = manifest.get('tasks', ())
    if (len(tasks) != 16 or
            {task['identity'] for task in tasks} != _expected(MODELS)
            or any(task.get('limits') != dict(
                native_calls=402, packet_visits=77621507200,
                bound_calls=0, bound_steps=0)
                or task.get('input_key') != 'interval'
                or task.get('native_kind') != 'tangent'
                for task in tasks)):
        raise ValueError('sixteen-case task identities or limits differ')


def inspect(root, prefix='data/esa-observed-model-dispatch-globe-pairs-v2'):
    """Replay a closed observed study without opening originals or fitting."""
    from pathlib import Path
    from lll.studies.closed import ClosedStudy

    if prefix != 'data/esa-observed-model-dispatch-globe-pairs-v2':
        raise ValueError('expected current v2 observed study identity')
    root = Path(root).resolve()
    study = ClosedStudy(root, prefix)
    try:
        from lll.airquantumgrav_inventory import environment
        from lll.airquantumgrav_observation_report import native_accounting
        from lll.airquantumgrav_observed_dispatch import (
            SCOPE, recipe, sources, tasks,
            required_tests,
        )
        from lll.airquantumgrav_observed_hybrid import parent_proof
        from lll.airquantumgrav_observed_hybrid_report import (
            verify_compilation, verify_qualification_report,
        )
        from lll.airquantumgrav_observed_report import verify_audit_environment
        from lll.airquantumgrav_observed_wide_report import (
            verify_compilation as verify_wide_compilation,
        )
        verify_contract(study.manifest)
        declared = study.input('qualification-request')
        env = study.input('qualification-environment')
        verify_audit_environment(env, environment())
        if declared.get('environment') != env:
            raise ValueError('source-bound qualification differs from manifest')
        source_proof = verify_qualified_sources(
            root, declared.get('sources'), study.manifest['sources'],
            expected_names=sources(root))
        verify_qualification_report(study.input('qualification-report', raw=True),
                                    required_tests(), minimum_tests=60)
        r = study.input('recipe')
        layout = study.input('layout')
        frozen = {identity: {key: value for key, value in task.items()
                             if key not in ('index', 'shard')}
                  for identity, task in study.tasks.items()}
        if (r != recipe(maximum_wall_s=r['maximum_wall_s'])
                or study.manifest['scope'] != SCOPE
                or frozen != {task['identity']: task for task in tasks(layout)}
                or study.input('parent-proof') != parent_proof(root)):
            raise ValueError('prepared measurements or task matrix changed')
        proof = study.input('dispatch-parent-proof')
        if (hashlib.sha256(study.input('dispatch-recovery-request', raw=True))
                .hexdigest() != proof['recovery_request_sha256']
                or hashlib.sha256(study.input('dispatch-recovery-report', raw=True))
                .hexdigest() != proof['recovery_report_sha256']):
            raise ValueError('task-recovery evidence differs from frozen proof')
        flat = load_frozen_flat(study)
        if proof.get('flat_saved_cases') != len(flat):
            raise ValueError('saved flat identity count differs')
        native = {}
        for shard in range(study.manifest['allocation']['workers']):
            identities = {identity for identity, task in study.tasks.items()
                          if task['shard'] == shard}
            native.update(native_accounting(study.read(
                f'shards/{shard:03d}/charges/journal.sqlite', raw=True),
                study.completion['manifest_sha256'], identities,
                per_call_visits=None))
        if set(native) != set(study.tasks):
            raise ValueError('native charge identities differ from frozen matrix')
        charged = verify_charge_totals(native, study.summary['charged'])
        import gzip
        source = 'analysis/lll/ilvis0_tangent.cpp'
        original = study.read('source-freeze/' + source,
                              study.manifest['sources'][source], raw=True)
        anchor = json.loads(gzip.decompress(
            study.input('training', raw=True)))[0]['height_m']
        globe = []
        for identity in study.tasks:
            if identity in study.rows:
                envelope = study.envelope(identity)
                for path, sha in envelope['artifacts'].items():
                    study.read(path, sha, raw=True)
                if all(key in envelope['result'] for key in
                       ('wide', 'hybrid', 'comparison')):
                    verify_wide_compilation(
                        meta=study.artifact(identity, 'wide-compilation.json'),
                        raw=original, sources=study.manifest['sources'],
                        environment=env, anchor=anchor)
                    selected = study.artifact(identity,
                                              'hybrid-compilation.json')
                    verify_compilation(
                        selected, original_source=original,
                        sources=study.manifest['sources'],
                        environment=env, anchor=anchor)
                    verify_declared_method(
                        selected, study.tasks[identity]['payload']['model'])
                operations = native[identity]
                if (operations['value'] != 0
                        or operations['tangent'] !=
                        envelope['charged']['native_calls']
                        or operations['packet_visits'] !=
                        envelope['charged']['packet_visits']):
                    raise ValueError('native calls or packet visits differ')
            globe.append(replay_case(study, identity))
        decision = assess(globe, flat)
        return dict(verified=True, **decision,
                    study=prefix, state=study.completion['state'],
                    source_proof=source_proof,
                    charged=charged,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    rows=globe, flat_rows=flat,
                    original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        study.close()


def load_saved_flat(raw):
    """Read only the hash-bound prior flat identity dispositions."""
    from lll.airquantumgrav_observed_dispatch import SAVED_AUDIT_SHA256

    if hashlib.sha256(raw).hexdigest() != SAVED_AUDIT_SHA256:
        raise ValueError('saved dispatch audit hash differs')
    audit = json.loads(raw)
    if (audit.get('matching_saved_numerical_dispositions') != 24
            or audit.get('native_calculations') != 0
            or audit.get('new_fits') != 0
            or audit.get('original_reads') != 0
            or audit.get('protected_group_reads') != 0
            or audit.get('scientific_decision') != 'abstain'
            or len(audit.get('selected', ())) != 24):
        raise ValueError('complete saved identity audit required')
    flat = []
    for item in audit['selected']:
        if item.get('model') != 'flat_still':
            continue
        if (item.get('method') != 'wide'
                or type(item.get('numerical_passed')) is not bool
                or item.get('baseline_numerical_passed') !=
                item['numerical_passed']):
            raise ValueError('saved flat case changed method or disposition')
        identity = item['identity']
        profile = identity.split('-')[1] == '1'
        policy = '-'.join(identity.split('-')[2:-1])
        start = int(identity.rsplit('-', 1)[1])
        passed = item['numerical_passed']
        flat.append(dict(identity=identity, model='flat_still',
                         profile=profile, policy_id=policy, start=start,
                         wide_passed=passed, selected_passed=passed,
                         comparison_passed=passed,
                         wide_training_cost=item['training_cost'],
                         selected_training_cost=item['training_cost']))
    return flat


def replay_case(study, identity):
    """Recompute a sealed pair verdict from its two saved fit forecasts."""
    from lll.airquantumgrav_observed_hybrid_report import compare_pair
    from lll.studies.artifacts import encoded

    payload = study.tasks[identity]['payload']
    row = dict(identity=identity, **payload, wide_passed=False,
               selected_passed=False, comparison_passed=False,
               wide_training_cost=None, selected_training_cost=None)
    if identity not in study.rows:
        row['reason'] = 'no sealed result'
        return row
    result = study.envelope(identity)['result']
    if (result.get('original_reads') != 0
            or result.get('protected_reads') != 0
            or result.get('scientific_decision') != 'abstain'):
        raise ValueError('observed case must abstain and use only saved development data')
    if not all(key in result for key in ('wide', 'hybrid', 'comparison')):
        if result.get('passed') is not False:
            raise ValueError('incomplete case cannot pass')
        row['reason'] = result.get('error', result.get('reason',
                                                    'paired calculation incomplete'))
        return row
    for variant in ('wide', 'hybrid'):
        part = result[variant]
        if any(part.get(key) != value for key, value in payload.items()):
            raise ValueError('paired fit changed case identity')
        row['wide_passed' if variant == 'wide' else 'selected_passed'] = (
            part.get('passed') is True)
        row['wide_training_cost' if variant == 'wide' else
            'selected_training_cost'] = part.get('training_cost')
    if row['wide_passed'] and row['selected_passed']:
        expected = compare_pair(
            result['wide'], result['hybrid'],
            study.artifact(identity, 'wide-fit.json'),
            study.artifact(identity, 'hybrid-fit.json'),
            study.artifact(identity, 'wide-forecast.json'),
            study.artifact(identity, 'hybrid-forecast.json'),
            tolerance_m=0.01)
    else:
        expected = dict(passed=False,
                        reason='at least one matched numerical fit did not qualify')
    if (encoded(expected) != encoded(result['comparison'])
            or encoded(expected) != encoded(study.artifact(
                identity, 'comparison.json'))
            or result.get('passed') != expected['passed']):
        raise ValueError('saved pair comparison differs from independent replay')
    row['comparison_passed'] = expected['passed']
    if not expected['passed']:
        row['reason'] = expected.get('reason', 'paired method check failed')
    return row


def _expected(models):
    return {
        f'{model}-{int(profile)}-{policy}-{start}'
        for model in models for profile in (False, True)
        for policy in POLICIES for start in (0, 1)
    }


def assess(globe_rows, flat_rows):
    """Apply the frozen 16-pair gate and retain the saved flat failure."""
    if (not isinstance(globe_rows, list) or not isinstance(flat_rows, list)
            or len(globe_rows) != 16 or len(flat_rows) != 8):
        raise ValueError('exact globe and flat matrices required')
    for rows, models in ((globe_rows, MODELS), (flat_rows, ('flat_still',))):
        if {row.get('identity') for row in rows} != _expected(models):
            raise ValueError('case identities differ from frozen matrix')
        for row in rows:
            expected_id = (f"{row.get('model')}-{int(row.get('profile'))}-"
                           f"{row.get('policy_id')}-{row.get('start')}")
            if row['identity'] != expected_id or row.get('profile') not in (False, True):
                raise ValueError('case payload differs from identity')
            for key in ('wide_passed', 'selected_passed', 'comparison_passed'):
                if type(row.get(key)) is not bool:
                    raise ValueError('explicit Boolean fit dispositions required')
            for key in ('wide_training_cost', 'selected_training_cost'):
                value = row.get(key)
                if value is None and rows is globe_rows and not row['comparison_passed']:
                    continue
                if type(value) not in (int, float) or not math.isfinite(value):
                    raise ValueError('finite saved training costs required')
            if row['comparison_passed'] and not (
                    row['wide_passed'] and row['selected_passed']):
                raise ValueError('comparison cannot pass a failed fit')

    flat_failures = {row['identity'] for row in flat_rows
                     if not row['wide_passed']}
    if flat_failures != {SAVED_FLAT_FAILURE} or any(
            row['wide_passed'] != row['selected_passed']
            or row['wide_passed'] != row['comparison_passed']
            or row['wide_training_cost'] != row['selected_training_cost']
            for row in flat_rows):
        raise ValueError('saved flat identity or numerical failure changed')

    groups_agree = 0
    for model in MODELS:
        for profile in (False, True):
            for policy in POLICIES:
                pair = [row for row in globe_rows if row['model'] == model
                        and row['profile'] == profile and row['policy_id'] == policy]
                if (all(row['comparison_passed'] for row in pair)
                        and min(pair, key=lambda row: (row['wide_training_cost'],
                                                       row['start']))['start']
                        == min(pair, key=lambda row: (
                            row['selected_training_cost'], row['start']))['start']):
                    groups_agree += 1
    passed = sum(row['comparison_passed'] for row in globe_rows)
    return dict(qualified=passed == 16 and groups_agree == 8,
                globe_pairs_passed=passed, globe_pairs_total=16,
                primary_groups_agree=groups_agree, primary_groups_total=8,
                flat_identity_count=8,
                flat_numerical_failures_retained=len(flat_failures))


def main():
    """Publish or verify only the closed model-declared method comparison."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('publish', 'verify'))
    parser.add_argument('--project', default='.')
    args = parser.parse_args()
    result = (publish(args.project) if args.action == 'publish'
              else verify_publication(args.project))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
