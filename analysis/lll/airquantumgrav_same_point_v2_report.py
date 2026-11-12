# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and publish the six frozen revised-tangent saved-point comparisons."""
import argparse
import hashlib
import io
from pathlib import Path

from lll.airquantumgrav_same_point_v2 import (
    IDENTITY, PARENT, VISITS_PER_CALL, gate, tasks)
from lll.studies.artifacts import atomic, encoded
from lll.studies.closed import ClosedStudy


MANIFEST_SHA256 = '55f08ddc8a6ee283d594635c9888f7c76f74231f493ec38ff32510a4f4120da4'


def build(root='.'):
    import numpy as np
    from lll.ilvis0_tangent_columns import compare

    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/'+IDENTITY)
    try:
        if (study.completion['state'] not in ('complete', 'terminal') or
                study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                list(study.tasks) != [item['identity'] for item in tasks()] or
                len(study.rows) != 3 or
                study.manifest['allocation']['total'] != 3):
            raise ValueError('exact frozen six-call study required')
        points = study.input('points')
        rows = []
        for identity in study.tasks:
            record = study.rows[identity]
            envelope = study.envelope(identity)
            result = envelope['result']
            if (result['scientific_decision'] != 'abstain' or
                    result['native_calls'] != 2 or result['optimizer_starts'] != 0 or
                    result['original_reads'] != 0 or result['protected_reads'] != 0 or
                    result['observed_substitution_qualified'] is not False or
                    envelope['charged']['native_calls'] != 2 or
                    envelope['charged']['packet_visits'] !=
                    2*VISITS_PER_CALL):
                raise ValueError('saved no-fit charges or abstention changed')
            metadata = study.artifact(identity, 'compilation.json')
            if (metadata['precision_revision'] != 'attitude-x-y-wide' or
                    metadata['production_method_changed'] is not False):
                raise ValueError('revised prototype metadata differs')
            for source in ('wide', 'hybrid'):
                old = study.input(identity+'-'+source+'-old-comparison')
                saved = study.artifact(identity, source+'-comparison.json')
                with np.load(io.BytesIO(study.input(
                        identity+'-'+source+'-reference', raw=True)),
                        allow_pickle=False) as prior:
                    times = prior['times_s'].copy()
                    wide_coordinates = prior['wide_coordinates'].copy()
                    wide_jacobian = prior['wide_jacobian'].copy()
                with np.load(io.BytesIO(study.artifact(
                        identity, source+'-revised-tangent.npz', raw=True)),
                        allow_pickle=False) as current:
                    new_times = current['times_s'].copy()
                    coordinates = current['coordinates'].copy()
                    jacobian = current['jacobian'].copy()
                if not np.array_equal(times, new_times):
                    raise ValueError('saved point times differ')
                active = points[identity][source]['active_parameters']
                replay = compare(times, wide_coordinates, coordinates,
                                 wide_jacobian, jacobian, active,
                                 boundaries=(old['boundaries'][0],
                                             old['boundaries'][0]))
                replay['boundary_counts_identical'] = saved['boundary_counts_identical']
                replay['passes_improvement_gate'] = gate(
                    replay, old, fraction=.1, attitude_limit=1e-8)
                replay['point_source'] = source
                if (encoded(replay) != encoded(saved) or
                        encoded(replay) != encoded(result['comparisons'][source])):
                    raise ValueError('saved revised comparison does not replay')
                columns = {row['name']: row['maximum_difference_m_per_normalized_unit']
                           for row in replay['columns']}
                rows.append(dict(identity=identity, point_source=source,
                                 original_max_m_per_unit=old['largest_column'][
                                     'maximum_difference_m_per_normalized_unit'],
                                 revised_max_m_per_unit=replay['largest_column'][
                                     'maximum_difference_m_per_normalized_unit'],
                                 attitude_x_m_per_unit=columns['attitude_x'],
                                 attitude_y_m_per_unit=columns['attitude_y'],
                                 passed=replay['passes_improvement_gate']))
            if record['passed'] is not (rows[-1]['passed'] and rows[-2]['passed']):
                raise ValueError('task gate and saved point gates differ')
        if (len(rows) != 6 or study.summary['charged']['native_calls'] != 6 or
                study.summary['charged']['packet_visits'] !=
                6*VISITS_PER_CALL):
            raise ValueError('six exact native calls required')
        source = root/'analysis/lll/airquantumgrav_same_point_v2_report.py'
        return dict(verified=True, study=IDENTITY, parent=PARENT,
                    manifest_sha256=MANIFEST_SHA256,
                    summary_sha256=study.completion['summary_sha256'],
                    reporter_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    completed=len(rows), passing=sum(row['passed'] for row in rows),
                    development_gate_passed=all(row['passed'] for row in rows),
                    observed_substitution_qualified=False,
                    new_fits=0, protected_reads=0,
                    scientific_decision='abstain', rows=rows)
    finally:
        study.close()


def render(report):
    if report.get('verified') is not True or report['completed'] != 6:
        raise ValueError('six verified saved-point reports required')
    lines = ['# Revised fast tangent on six saved ESA points', '',
             f"**{report['passing']}/6 saved points pass the predeclared improvement gate.**",
             'No model was refitted. The three original observed-fit failures and',
             'the 21/24 substitution result remain unchanged.', '',
             '| Failed pair | Point | Old maximum | Revised maximum | Attitude X | Attitude Y | Gate |',
             '|---|---|---:|---:|---:|---:|---|']
    for row in report['rows']:
        lines.append('| {identity} | {point_source} | {original_max_m_per_unit:.3g} | '
                     '{revised_max_m_per_unit:.3g} | {attitude_x_m_per_unit:.3g} | '
                     '{attitude_y_m_per_unit:.3g} | {passed} |'.format(**row))
    lines += ['', 'Differences are metres of predicted position per normalized',
              'parameter unit. Values and timing-boundary counts must match the',
              'wide reference; the largest derivative difference must shrink by',
              'at least tenfold and both attitude columns must be below 10⁻⁸.',
              'This check uses one development recording, not protected flights.',
              'It cannot qualify replacement of the established wide method.', '',
              '[Frozen gate](../../mixed-tangent-hybrid/V2_SAVED_POINT_PLAN.md) ·',
              '[Original saved-point result](../same-point-result/README.md)']
    return '\n'.join(lines)+'\n'


def publish(root='.'):
    root = Path(root).resolve()
    report = build(root)
    target = root/'docs/esa-observed-hybrid/same-point-v2'
    atomic(target/'README.md', render(report).encode())
    atomic(target/'verified-report.json', encoded(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    report = publish(args.root)
    print(f"{report['passing']}/6 saved-point gates passed; "
          f"substitution qualified={report['observed_substitution_qualified']}")


if __name__ == '__main__':
    main()
