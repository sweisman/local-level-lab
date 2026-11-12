# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-data start selection and receiver-precision study controls."""

import csv
import gzip
import io
import json
import math

import pytest


def _pilot():
    tasks = {}
    outcomes = {}
    for sid in ('a', 'b', 'c'):
        for model in range(3):
            for profile in (False, True):
                for clock in ('header_elapsed', 'nominal_200Hz'):
                    for start in (0, 1):
                        identity = f'{sid}-{model}-{int(profile)}-{clock}-{start}'
                        tasks[identity] = dict(payload=dict(segment_id=sid,
                            model=model, profile=profile, clock=clock,
                            start=start))
                        outcomes[identity] = dict(converged=True,
                            all_active_columns_retained=True,
                            training_cost=10. + start,
                            horizontal_rms_m=100. if start == 0 else .001)
    for key in sorted({(v['payload']['segment_id'], v['payload']['model'],
                       v['payload']['profile'], v['payload']['clock'])
                       for v in tasks.values()})[:8]:
        for identity, task in tasks.items():
            p = task['payload']
            if (p['segment_id'], p['model'], p['profile'], p['clock']) == key:
                outcomes[identity]['converged'] = False
    return tasks, outcomes


def test_select_primaries_uses_training_cost_only_and_keeps_missing_settings():
    from lll.receiver_precision_holdout_study import select_primaries

    tasks, outcomes = _pilot()
    selected = select_primaries(tasks, outcomes)
    assert len(selected) == 36
    assert sum(row['chosen_identity'] is None for row in selected) == 8
    assert all(row['chosen_identity'].endswith('-0') for row in selected
               if row['chosen_identity'])
    outcomes[next(iter(outcomes))]['training_cost'] = float('nan')
    # The altered row is in a no-qualified-start setting, so it stays excluded.
    assert select_primaries(tasks, outcomes) == selected


def test_evaluate_uses_frozen_saved_rows_and_never_refits(tmp_path):
    from lll.receiver_precision_holdout_study import SCOPE, evaluate, recipe

    sid = 'a'
    identity = 'a-0-0-header_elapsed-0'
    epochs = []
    positions = []
    training = []
    for index in range(6):
        lat = 42. + .001 * index
        lon = -120. + .001 * index
        height = 1000. + index
        epochs.append(dict(epoch=index,
            role='training' if index < 2 else 'prediction',
            time_s=float(index), north_direct_error_m=float(index),
            east_direct_error_m=0., up_direct_error_m=-float(index)))
        positions.append(dict(gps_week='1800',
            gps_milliseconds=str((100015 + index) * 1000),
            latitude_deg=str(lat), longitude_deg=str(lon),
            ellipsoid_height_m=str(height), reported_sigma_north_m='2',
            reported_sigma_east_m='3', reported_sigma_up_m='4'))
        if index < 2:
            training.append([math.radians(lat), math.radians(lon), height])
    material = dict(segment_id=sid, selected_epochs={identity:epochs},
                    origin_utc_week_s=100000., gps_week=1800,
                    training_gps=training)
    settings = [dict(segment_id=sid, model=index // 4,
                     profile=bool((index // 2) % 2),
                     clock='header_elapsed' if index % 2 == 0 else 'nominal_200Hz',
                     chosen_identity=identity if index == 0 else None,
                     numerical_status='qualified' if index == 0 else
                                      'no_qualified_start')
                for index in range(12)]
    summary = dict(recipe=recipe(), segments={sid:{}}, primaries=settings)
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=list(positions[0]),
                            lineterminator='\n')
    writer.writeheader()
    writer.writerows(positions)
    inputs = dict(preparation=json.dumps(summary).encode(),
                  **{'material-a':gzip.compress(json.dumps(material).encode()),
                     'positions-a':gzip.compress(output.getvalue().encode())})
    paths = {}
    for name, data in inputs.items():
        path = tmp_path / name
        path.write_bytes(data)
        paths[name] = path

    class Context:
        manifest = dict(scope=SCOPE, tasks=[dict(identity=sid)])
        saved = {}

        def input_path(self, name):
            return paths[name]

        def save(self, name, value):
            self.saved[name] = value

        def save_bytes(self, name, value):
            self.saved[name] = value

    context = Context()
    result = evaluate(dict(identity=sid), context)
    assert result['passed'] is True
    assert result['qualified_primaries'] == 1
    assert result['no_qualified_start'] == 11
    assert result['model_fits'] == 0
    assert len(json.loads(gzip.decompress(context.saved[
        'matched-' + identity + '.json.gz']))) == 6
    assert context.saved['precision-comparison.json'][0]['report'][
        'prediction_epochs'] == 4
    with pytest.raises(ValueError, match='unchanged frozen'):
        evaluate(dict(identity='changed'), context)
