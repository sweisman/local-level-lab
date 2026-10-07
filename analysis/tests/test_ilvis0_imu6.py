# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import numpy as np
import pytest

from lll import ilvis0_imu6 as audit


MAPPING = dict(permutation=[1, 0, 2], signs=[-1, 1, 1])


def samples(gyro_scale=1, velocity_scale=3.38e-5, late_scale=1):
    rng = np.random.default_rng(64006)
    raw = rng.normal(size=(160, 3)) * 10000
    force = rng.normal(size=(160, 3)) * 50000
    gravity = rng.normal(size=(160, 3))
    mapped = raw[:, MAPPING['permutation']] * MAPPING['signs']
    mapped_force = force[:, MAPPING['permutation']] * MAPPING['signs']
    factor = np.r_[np.ones(80), np.full(80, late_scale)]
    return [dict(time=i, error=0, gyro=r.tolist(), force=f.tolist(), gravity=g.tolist(),
                 gyro_reference=(m * audit.ANGLE_SCALE * gyro_scale * factor[i] + .001).tolist(),
                 acceleration_reference=(mf * velocity_scale + 9.81 * g + .01).tolist())
            for i, (r, f, g, m, mf) in enumerate(zip(raw, force, gravity, mapped, mapped_force))]


def test_gyro_units_relative_rotation_and_no_scientific_promotion():
    result = audit.validate_samples(samples())
    assert result['gyro_scale_validated']
    assert result['mapping'] == MAPPING
    assert result['mapping_rotation_determinant'] == pytest.approx(1)
    assert result['gyro']['axes'][0]['source_axis'] == 'y'
    assert result['gyro']['axes'][0]['sign'] == -1
    assert audit.ANGLE_SCALE == pytest.approx(np.deg2rad(.4 / 3600))
    assert result['accelerometer_empirical_scale_reproduces']
    assert not result['complete_physical_decoder_validated']
    assert not result['scientific_eligible']
    assert not result['accelerometer_empirical']['exact_velocity_scale_known']


def test_frozen_mapping_and_scale_do_not_refit_to_pass_second_date():
    wrong = audit.validate_samples(samples(), dict(permutation=[0, 1, 2], signs=[1, 1, 1]))
    assert not wrong['gyro_scale_validated'] and not wrong['mapping_matches_fixed']
    first = audit.validate_samples(samples())
    second = audit.validate_samples(samples(velocity_scale=3.39e-5), first['mapping'],
                                    first['frozen_empirical_velocity_scale_mps_per_count'])
    assert second['gyro_scale_validated']
    assert not second['accelerometer_empirical_scale_reproduces']
    assert second['frozen_empirical_velocity_scale_mps_per_count'] == first['frozen_empirical_velocity_scale_mps_per_count']


def test_wrong_scale_chronological_instability_and_insufficient_samples_fail():
    assert not audit.validate_samples(samples(gyro_scale=1.005))['gyro_scale_validated']
    assert not audit.validate_samples(samples(late_scale=1.005))['gyro_scale_validated']
    assert not audit.validate_samples(samples()[:20])['gyro_scale_validated']


def test_representatives_use_configuration_date_and_hash_not_result():
    def row(task, date, digest, decision='keep'):
        return dict(task_id=task, actual_dates=[date], source_sha256=digest,
                    imu_types={'6': 1}, storage_decision=decision)
    contexts = {k: dict(inspection=dict(versions={'v': 1}, imu_types={'6': 1},
                                       rate_codes={'2': 1}))
                for k in ('a', 'b', 'c', 'd')}
    rows = [row('a', '2009-01-01', 'h1'), row('b', '2009-01-03', 'h1'),
            row('c', '2009-01-04', 'h2', 'discard_duplicate'), row('d', '2009-01-02', 'h3')]
    assert audit.select_representatives(rows, contexts)[0]['representatives'] == ['a', 'd']


def test_resume_checks_samples_and_frozen_inputs_without_rereading_sources(tmp_path, monkeypatch):
    corpus, retention, prior = (tmp_path / p for p in ('corpus', 'retention', 'prior'))
    for path in (corpus, retention, prior):
        path.mkdir()
    row = dict(task_id='a', filename='a.013', storage_decision='keep', imu_types={'6': 1},
               actual_dates=['2009-01-01'], source_sha256='original')
    source = corpus / 'a/decoded/a.013.gz'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'preserved')
    (corpus / 'records.jsonl').write_text(json.dumps(dict(task_id='a', filename='a.013')) + '\n')
    (retention / 'summary.json').write_text(json.dumps(dict(results=[row])))
    (retention / 'cleanup.jsonl').write_text('')
    context = dict(task_id='a', inspection=dict(versions={'v': 1}, imu_types={'6': 1}, rate_codes={'2': 1}))
    (prior / 'summary.json').write_text(json.dumps(dict(results=[context])))
    calls = []
    def match(*args, **kwargs):
        calls.append(args)
        return samples(), 160
    monkeypatch.setattr(audit.il, 'matched_samples', match)
    monkeypatch.setattr(audit.motion, 'read_motion', lambda *a: ([], [], {}))
    output = tmp_path / 'output'
    assert audit.run(corpus, retention, prior, output)['gyro_passes'] == 1
    assert audit.run(corpus, retention, prior, output)['gyro_passes'] == 1
    assert len(calls) == 1 and source.read_bytes() == b'preserved'
    (output / 'a.matched-samples.json.gz').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='samples changed'):
        audit.run(corpus, retention, prior, output)
    (retention / 'cleanup.jsonl').write_text('changed')
    with pytest.raises(ValueError, match='mismatch'):
        audit.run(corpus, retention, prior, output)
