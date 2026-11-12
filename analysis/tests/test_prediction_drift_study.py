# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen saved scores, abstentions and no-fit evaluator controls."""

import gzip
import json

import pytest


def _epochs():
    return [dict(epoch=index,
                 role='training' if index < 160 else 'prediction',
                 time_s=float(index),
                 north_direct_error_m=1. + .1*index,
                 east_direct_error_m=-2. + .2*index,
                 up_direct_error_m=3. - .05*index)
            for index in range(240)]


def test_study_keeps_all_settings_and_exact_original_scores(tmp_path):
    from lll.prediction_drift_control import evaluate as score
    from lll.prediction_drift_study import SCOPE, evaluate, recipe

    sid='segment'
    chosen='segment-0-0-header_elapsed-0'
    epochs=_epochs()
    original=score(epochs)['scores']['original']
    reference=dict(north_rms_m=original['north_rms_m'],
                   east_rms_m=original['east_rms_m'],
                   vertical_rms_m=original['height_rms_m'],
                   horizontal_rms_m=original['horizontal_rms_m'])
    selections=[dict(segment_id=sid, model=index//4,
                     profile=bool((index//2)%2),
                     clock='header_elapsed' if index%2==0 else 'nominal_200Hz',
                     chosen_identity=chosen if index==0 else None,
                     numerical_status='qualified' if index==0 else
                                      'no_qualified_start')
                for index in range(12)]
    material=gzip.compress(json.dumps(dict(segment_id=sid,
        selected_epochs={chosen:epochs})).encode())
    from lll.studies.artifacts import digest
    summary=dict(recipe=recipe(),
                 selected_settings=selections,
                 material_sha256={sid:digest(material)},
                 baseline_reference={chosen:reference})
    paths={}
    for name,blob in (('preparation',json.dumps(summary).encode()),
                      ('material-'+sid,material)):
        path=tmp_path/name
        path.write_bytes(blob)
        paths[name]=path

    class Context:
        manifest=dict(scope=SCOPE,tasks=[dict(identity=sid)])
        saved={}

        def input_path(self,name):
            return paths[name]

        def save(self,name,value):
            self.saved[name]=value

    context=Context()
    result=evaluate(dict(identity=sid),context)
    assert result['passed'] is True
    assert result['corrected_settings']==1
    assert result['numerical_abstentions']==11
    assert result['model_fits']==0
    rows=context.saved['drift-comparison.json']
    assert len(rows)==12
    assert rows[0]['correction']['scores']['linear'][
        'horizontal_rms_m']<1e-12
    assert all(row['correction'] is None for row in rows[1:])


def test_study_rejects_changed_uncorrected_baseline():
    from lll.prediction_drift_control import evaluate as score
    from lll.prediction_drift_study import require_baseline

    actual=score(_epochs())
    baseline=actual['scores']['original']
    reference=dict(north_rms_m=baseline['north_rms_m'],
                   east_rms_m=baseline['east_rms_m'],
                   vertical_rms_m=baseline['height_rms_m'],
                   horizontal_rms_m=baseline['horizontal_rms_m'])
    require_baseline(actual,reference)
    reference['east_rms_m']+=.01
    with pytest.raises(ValueError,match='uncorrected pilot'):
        require_baseline(actual,reference)
