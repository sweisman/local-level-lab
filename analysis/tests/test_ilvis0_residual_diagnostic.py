# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import numpy as np
import pytest

import ilvis0_residual_diagnostic as worker


def test_prediction_charges_are_unique_finite_and_durable(tmp_path):
    path = tmp_path/'predictions.jsonl'; ids = ['one', 'two']
    worker.charge(path, 'one', 'hash', ids)
    assert len(worker.journal(path, 'hash', ids)) == 1
    with pytest.raises(ValueError, match='charged'):
        worker.charge(path, 'one', 'hash', ids)
    with pytest.raises(ValueError, match='scope'):
        worker.charge(path, 'other', 'hash', ids)
    worker.charge(path, 'two', 'hash', ids)
    assert len(worker.journal(path, 'hash', ids)) == 2
    with pytest.raises(ValueError):
        worker.journal(path, 'changed', ids)


def test_input_mismatch_cannot_launch_a_prediction(tmp_path):
    original = tmp_path/'input'; original.write_text('altered')
    with pytest.raises(ValueError, match='hash'):
        worker.check_hashes({str(original): '0'*64})


def test_prediction_must_reproduce_saved_objective_and_axes():
    physical = np.ones((5, 3)); z = np.ones((5, 3))*2
    fit = dict(residual_sum_squares=60., residual_rms_neu_m=[1., 1., 1.],
               header_fixed_parameter_rms_neu_m=[1., 1., 1.])
    worker.check_reproduction(fit, 'nominal_200Hz', physical, z)
    with pytest.raises(ValueError, match='cost'):
        worker.check_reproduction(fit, 'nominal_200Hz', physical, z*2)
    with pytest.raises(ValueError, match='RMS'):
        worker.check_reproduction(fit, 'header_elapsed', physical*2, z)


def test_corrupted_cached_prediction_is_not_silently_reused(tmp_path):
    worker.base.save(tmp_path/'sample.json', dict(state='complete'), 'hash')
    assert worker.base.cached(tmp_path/'sample.json', 'hash')['state'] == 'complete'
    record = json.loads((tmp_path/'sample.json').read_text())
    record['result']['state'] = 'changed'
    (tmp_path/'sample.json').write_text(json.dumps(record))
    with pytest.raises(ValueError):
        worker.base.cached(tmp_path/'sample.json', 'hash')
