# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-result audit for a model-declared ESA tangent choice."""

import hashlib
import itertools
import json
from pathlib import Path
import platform

from .ilvis0_tangent_dispatch import method_for_model


REPORT_SHA256 = '7900aa4852546571c172a086640428c6302a2792dcda766715dd154022fbe7e3'
SELECTIVE_SHA256 = '4e8c229d57f9293e9437aad8a5e26652e31671187f7102eb8cd65a1b073c24a8'
WIDE_SHA256 = 'ba2d3933eae6aff994e7d4370863dc525a60e1011316b5d8076c44feb08b35fe'


def select_saved(row):
    """Select the recorded result by model only, preserving failures."""
    method = method_for_model(row['model'])
    if method == 'selective':
        if (row['comparison'].get('passed') is not True or
                row['wide'].get('passed') is not True or
                row['hybrid'].get('passed') is not True):
            raise ValueError('globe selective comparison did not pass')
        if (row['wide'].get('accuracy_all_sections') !=
                row['hybrid'].get('accuracy_all_sections')):
            raise ValueError('globe physical accuracy classification differs')
        selected = row['hybrid']
    else:
        selected = row['wide']
    return dict(identity=row.get('identity'), model=row['model'], method=method,
                numerical_passed=bool(selected['passed']),
                physical_accuracy_passed=bool(selected.get('accuracy_all_sections')),
                training_cost=selected['training_cost'],
                baseline_numerical_passed=bool(row['wide']['passed']))


def build(root):
    root = Path(root).resolve()
    source = root / 'docs/esa-observed-hybrid/combined/verified-report.json'
    code = root / 'analysis/lll'
    expected = ((source, REPORT_SHA256),
                (code / 'ilvis0_hybrid_tangent.py', SELECTIVE_SHA256),
                (code / 'ilvis0_wide_tangent.py', WIDE_SHA256))
    if any(hashlib.sha256(path.read_bytes()).hexdigest() != digest
           for path, digest in expected):
        raise ValueError('unchanged sealed paired audit and tangent loaders required')
    report = json.loads(source.read_text())
    rows = report['rows']
    expected_cases = set(itertools.product(
        ('sphere_rotating', 'sphere_still', 'flat_still'),
        (False, True), ('reported-short-v1', 'reported-persistent-v1'), (0, 1)))
    actual_cases = {(row['model'], row['profile'], row['policy_id'], row['start'])
                    for row in rows}
    if (report.get('verified') is not True or report.get('total') != 24 or
            report.get('returned') != 24 or len(rows) != 24 or
            actual_cases != expected_cases or
            len({row['identity'] for row in rows}) != 24):
        raise ValueError('complete unique verified 24-case matrix required')
    selected = [select_saved(row) for row in rows]
    if any(item['numerical_passed'] != item['baseline_numerical_passed']
           for item in selected):
        raise ValueError('model-declared dispatch changes numerical disposition')
    counts = {method: dict(cases=sum(item['method'] == method for item in selected),
                           numerical_passes=sum(item['method'] == method and
                                                item['numerical_passed']
                                                for item in selected))
              for method in ('selective', 'wide')}
    return dict(version='esa-model-declared-tangent-saved-audit-v1',
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                method_source_sha256=hashlib.sha256((
                    code / 'ilvis0_tangent_dispatch.py').read_bytes()).hexdigest(),
                paired_report_sha256=REPORT_SHA256,
                selective_loader_sha256=SELECTIVE_SHA256,
                wide_loader_sha256=WIDE_SHA256,
                python_version=platform.python_version(),
                selected=selected, counts=counts,
                matching_saved_numerical_dispositions=24,
                new_fits=0, native_calculations=0, original_reads=0,
                protected_group_reads=0,
                actual_dispatch_fit_qualified=False,
                general_substitution_qualified=False,
                scientific_decision='abstain')


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/mixed-tangent-hybrid'
    atomic(base / 'MODEL_DISPATCH_RESULT.json', encoded(result))
    summary = result['counts']
    page = ('# Model-declared tangent precision: saved-result audit\n\n'
        'A fixed rule selects the first selective tangent for both globe '
        'candidates and the established wide tangent for the flat candidate. '
        'The choice uses only the model ID, before fitting. On the complete '
        'sealed 24-case ESA development audit, all 16 globe pairs passed '
        'the original selective-versus-wide gate. The eight flat cases use '
        'the original wide outcomes unchanged.\n\n'
        '| Selected method | Cases | Numerical passes |\n'
        '| --- | ---: | ---: |\n'
        f'| Selective, globe | {summary["selective"]["cases"]} | '
        f'{summary["selective"]["numerical_passes"]} |\n'
        f'| Wide, flat | {summary["wide"]["cases"]} | '
        f'{summary["wide"]["numerical_passes"]} |\n\n'
        'All 24 saved numerical dispositions match the wide reference, '
        'including one retained flat-model failure. This is a development '
        'audit of **existing results**.\n\n'
        'Two generated 20-second smoke cases also run the dispatcher through '
        'the fitter and forecast. They match the wide reference on inputs '
        'and forecast positions within 0.00001 m. Both stop at the test’s '
        'eight-evaluation cap without meeting convergence, so neither is '
        'a qualifying fit. The dispatcher has not been timed or qualified '
        'for observed substitution; the established wide method remains '
        'in use. No Earth-model decision follows.\n\n'
        '[Fixed method](MODEL_DISPATCH_PLAN.md) · '
        '[Per-case audit](MODEL_DISPATCH_RESULT.json) · '
        '[Original 24-case audit](../esa-observed-hybrid/combined/README.md).\n')
    atomic(base / 'MODEL_DISPATCH_RESULT.md', page.encode())
    return result


if __name__ == '__main__':
    result = publish('.')
    print(json.dumps(result['counts']))
