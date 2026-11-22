# SPDX-License-Identifier: AGPL-3.0-or-later
"""Combine the checked linked ranges with the complete saved ESA cover."""

from contextlib import closing
from fractions import Fraction as F
from pathlib import Path

from .esa_linked_directional import ID, MODES, RANGES, SENSITIVITY_SHA


RESULT = 'docs/prediction-observed-development/esa-linked-directional.json'


def collect(root):
    from .ilvis0_saved_prediction_audit import endpoint
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or set(study.rows) != set(RANGES):
            raise ValueError('both sealed linked directional tasks must pass')
        sensitivity = study.input('sensitivity', raw=True)
        if digest(sensitivity) != SENSITIVITY_SHA:
            raise ValueError('unchanged previous range bounds required')
        prior = {group['model']: group['rows'][0] for group in study.input('sensitivity')['rows']}
        cover = study.input('cover')['rows']
        results = []
        for group in cover:
            model, nominal = group['model'], group['nominal_separation']
            record = study.artifact(model, 'linked-directional.json')
            rows = {tuple(row['identity']): row for row in record['rows']}
            if set(rows) != set(RANGES[model]) or nominal != record['nominal_separation']:
                raise ValueError('complete original survivors and score direction required')
            retained, excluded, improved = [], [], []
            for parent in group['rows']:
                pair = parent['parent_index'], parent['cell_index']
                identity = f'{model}-{pair[0]}-{pair[1]}'
                old_upper = parent['upper']
                if identity in prior[model]['excluded_ranges']:
                    if pair in rows:
                        raise ValueError('previously excluded range entered a survivor task')
                    continue
                if pair not in rows:
                    if old_upper > nominal/2:
                        raise ValueError('unchecked high-bound survivor')
                    retained.append((old_upper, pair))
                    continue
                row = rows[pair]
                trials = {(trial['direction'], trial['mode']): F(trial['exact_upper'])
                          for trial in row['trials']}
                if set(trials) != {(mode, representation) for mode in ('score','earlier_loss')
                                  for representation in MODES} or len(row['trials']) != len(trials):
                    raise ValueError('every frozen directional certificate required')
                reject = min(trials['earlier_loss', name] for name in MODES) < 0
                upper = endpoint(min(trials['score', name] for name in MODES), True)
                if reject != row['excluded'] or upper != row['upper']:
                    raise ValueError('sealed range summary changed')
                if reject:
                    excluded.append(pair)
                else:
                    if upper < old_upper:
                        improved.append(pair)
                    retained.append((min(old_upper, upper), pair))
            current = max(value for value, _ in retained)
            old = prior[model]['upper']
            results.append(dict(model=model, nominal_separation=nominal, upper=min(current, old),
                recalculated_upper=current, previous_upper=old, excluded=excluded,
                tightened_against_original_cover=improved, ranges=record['rows']))
        return dict(rows=results, manifest_sha256=study.completion['manifest_sha256'],
                    scientific_decision='abstain')


if __name__ == '__main__':
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded

    root = Path.cwd()
    payload = encoded(collect(root))
    _write_equal(root/RESULT, payload)
    print(digest(payload))
