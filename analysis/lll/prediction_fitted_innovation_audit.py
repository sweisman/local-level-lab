# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved full-fit innovation structure in the generated prediction cohort."""

import hashlib
import json
import math
from pathlib import Path
from statistics import median


STUDY = 'data/prediction-simultaneous-law-family-v3-runtime-20261112'
PUBLIC = 'docs/prediction-simultaneous-law-family-v3/verified-report.json'
CONVENTION = 'whitened residual derivative by normalized parameter'


def correlation(series, lag):
    if (type(lag) is not int or lag < 1 or not isinstance(series, (list, tuple))
            or len(series) <= lag or any(type(x) not in (int, float)
                                         or not math.isfinite(x) for x in series)):
        raise ValueError('finite series and interior positive lag required')
    left, right = series[:-lag], series[lag:]
    a, b = sum(left)/len(left), sum(right)/len(right)
    centered = [(x-a, y-b) for x, y in zip(left, right, strict=True)]
    xx = sum(x*x for x, _ in centered)
    yy = sum(y*y for _, y in centered)
    return None if xx == 0 or yy == 0 else sum(
        x*y for x, y in centered)/math.sqrt(xx*yy)


def summarize(values):
    if not values:
        return None
    import numpy as np
    data = np.asarray(values, dtype=float)
    return dict(count=len(values), median=float(median(values)),
                p95=float(np.quantile(data, .95)), maximum=float(np.max(data)))


def _lineage(root):
    from .studies.closed_single_stage_lineage import inspect
    return inspect(root, STUDY + '-continuation',
                   expected_parent=STUDY, expected_total=96)


def build(root):
    from .airquantumgrav_observed_hybrid_combined_audit import CombinedStudy

    root = Path(root).resolve()
    public = json.loads((root / PUBLIC).read_bytes())
    lineage = _lineage(root)
    if (public.get('verified') is not True
            or public.get('study') != STUDY
            or public.get('scientific_decision') != 'abstain'
            or public.get('totals', {}).get('completed') != 96
            or public['totals'].get('numerical_passing_fits') != 190
            or lineage.get('verified') is not True
            or lineage.get('completed') != 96
            or lineage.get('total') != 96
            or lineage.get('lineage_sha256') !=
                public['continuation_lineage_sha256']):
        raise ValueError('complete sealed generated cohort required')
    study = CombinedStudy(root, lineage)
    try:
        if (study.completion['manifest_sha256'] != public['manifest_sha256']
                or study.completion['summary_sha256'] != public['summary_sha256']
                or len(study.rows) != 96):
            raise ValueError('saved study and publication differ')
        rows = []
        for index in range(96):
            identity = f'case-{index:03d}'
            result = study.envelope(identity)['result']
            if result.get('technical_pair_complete') is not True:
                raise ValueError('complete generated pair required')
            for law in ('increment', 'point'):
                fit = study.artifact(identity, law + '/fit.json')
                passed = (fit.get('converged') is True and
                          fit.get('stopping_rule_verified') is True)
                if passed != result['candidate_results'][law]['converged']:
                    raise ValueError('saved fit classification differs')
                row = dict(identity=identity, law=law, passed=passed)
                if passed:
                    linear = fit.get('local_linearization', {})
                    residual = linear.get('residual')
                    training = study.artifact(
                        identity, law + '/training-observations.json')
                    epochs = training['training_epochs']
                    if (linear.get('convention') != CONVENTION
                            or epochs != 79 or not isinstance(residual, list)
                            or len(residual) != 3 * epochs
                            or any(type(value) not in (int, float)
                                   or not math.isfinite(value)
                                   for value in residual)
                            or not math.isclose(sum(value*value for value in residual),
                                                fit['residual_sum_squares'],
                                                rel_tol=1e-10, abs_tol=1e-10)):
                        raise ValueError('saved fitted innovations differ from fit')
                    row['axes'] = {}
                    for axis, name in enumerate(('north', 'east', 'height')):
                        values = residual[axis::3]
                        row['axes'][name] = dict(
                            rms=math.sqrt(sum(x*x for x in values)/epochs),
                            lag1=correlation(values, 1),
                            lag20=correlation(values, 20))
                rows.append(row)
        passes = sum(row['passed'] for row in rows)
        if len(rows) != 192 or passes != 190:
            raise ValueError('all generated fits and failures required')
        by_law = {}
        for law in ('increment', 'point'):
            part = [row for row in rows if row['law'] == law and row['passed']]
            by_law[law] = {axis: {stat: summarize([
                row['axes'][axis][stat] for row in part
                if row['axes'][axis][stat] is not None])
                for stat in ('rms', 'lag1', 'lag20')}
                for axis in ('north', 'east', 'height')}
        per_recording = []
        for index in range(96):
            available = [abs(row['axes']['height']['lag1']) for row in rows
                if row['identity'] == f'case-{index:03d}' and row['passed']
                and row['axes']['height']['lag1'] is not None]
            if available:
                per_recording.append(max(available))
        return dict(version='generated-full-fit-innovation-audit-v1',
            verified=True, study=STUDY,
            manifest_sha256=public['manifest_sha256'],
            continuation_lineage_sha256=lineage['lineage_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            archived_lineage_verification=
                lineage['archived_source_snapshots_verified'],
            recordings=96, fit_attempts=192, passing_fits=passes,
            failed_fits=192-passes, training_epochs=79,
            by_law=by_law,
            recordings_with_passing_height_innovations=len(per_recording),
            recording_max_absolute_height_lag1=summarize(per_recording),
            rows=rows, new_fits=0, original_reads=0, protected_reads=0,
            observed_error_law_qualified=False,
            scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh saved-audit output required')
    report = build(args.root)
    atomic(output, encoded(report))
    print(json.dumps(dict(recordings=report['recordings'],
        passing_fits=report['passing_fits'],
        maximum_height_lag1=report['recording_max_absolute_height_lag1']['maximum']),
        sort_keys=True))


if __name__ == '__main__':
    main()
