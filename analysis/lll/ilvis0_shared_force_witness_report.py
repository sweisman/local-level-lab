# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and summarize the saved common-receiver force checks."""

from contextlib import closing
from pathlib import Path

from .ilvis0_shared_force_witness_study import ID, ORIGINAL, ORIGINAL_SHA, PER_WINDOW, STEPS, WINDOWS
from .studies.closed import ClosedStudy


RESULT = 'docs/ilvis0-measurement-contribution/shared-force-witness.json'


def _counts(rows):
    fields = ('initial_deficit_mps2', 'reconstructed_deficit_mps2', 'reconstructed_stronger_deficit_mps2')
    return {key: dict(violations=sum(row[key] > 0. for row in rows),
                      max_excess_mps2=max(0., max(row[key] for row in rows))) for key in fields}


def collect(root):
    results = []
    manifests = {}
    for runtime, identity, expected_charges in ((ORIGINAL, 'imu21', 4), (ID, 'imu8', 3)):
        with closing(ClosedStudy(root, 'data/'+runtime)) as study:
            if not study.rows[identity]['passed'] or study.summary['bound_evaluations'] != expected_charges:
                raise ValueError('each matched recorder needs its own sealed passing result')
            manifest = study.completion['manifest_sha256']
            if runtime == ORIGINAL and manifest != ORIGINAL_SHA:
                raise ValueError('original IMU21 source freeze changed')
            manifests[identity] = manifest
            scored = study.artifact(identity, 'inequalities.json')
            correction = study.artifact(identity, 'receiver-error.json')
            summary = study.envelope(identity)['result']
            expected = WINDOWS[summary['imu_type']]*PER_WINDOW
            roster = {(row['side'], row['gps_tag'], row['clock'], row['model']) for row in scored}
            projected_rows = correction.get('projected_rows', list(range(expected)))
            if (len(scored) != expected or len(roster) != expected
                    or len(correction['projected']) != len(projected_rows)
                    or projected_rows != (list(range(expected)) if runtime == ORIGINAL else
                                           [i for i,r in enumerate(scored) if r['initial_deficit_mps2'] > 0.])
                    or len(correction['times_s']) != len(correction['correction_m'])
                    or summary['steps'] > STEPS or summary['imu_type'] != identity[3:]
                    or summary['fit_starts'] or summary['gyro_observations_used']):
                raise ValueError('sealed common-error case differs from frozen scope')
            split = {side: _counts([row for row in scored if row['side'] == side])
                     for side in ('training', 'later')}
            models = {model: {side: _counts([row for row in scored
                         if row['model'] == model and row['side'] == side]) for side in split}
                      for model in sorted({row['model'] for row in scored})}
            results.append(dict(summary, split=split, models=models))
    return dict(rows=results, manifests=manifests, scientific_decision='abstain')


if __name__ == '__main__':
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded

    root = Path.cwd()
    raw = encoded(collect(root))
    _write_equal(root/RESULT, raw)
    print(digest(raw))
