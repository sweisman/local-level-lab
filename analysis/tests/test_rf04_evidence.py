# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.rf04_evidence import bind_result, compare_rows


def test_rf04_evidence_binds_the_full_result_and_charge_record():
    result = dict(passed=True, new_fits=0, reserved_reads=0, scientific_decision='abstain', scores=[.1, .2])
    charged = dict(native_calls=0, packet_visits=0, bound_calls=7, bound_steps=100)
    completion = {'state': 'complete'}
    report = dict(result, completion=completion, charged=charged)
    envelope = dict(result=result.copy(), charged=charged.copy())
    bind_result('fixture', report, envelope, completion, 7)
    with pytest.raises(ValueError, match='fixture'):
        bind_result('fixture', report | {'scores': [.2, .1]}, envelope, completion, 7)
    with pytest.raises(ValueError, match='fixture'):
        bind_result('fixture', report, envelope, completion, 8)


def test_rf04_evidence_rejects_the_wrong_receiver_epoch_or_values():
    def attitude_row(second):
        return dict(utc=f'12:00:{second:02}Z', GGSTATUS=1)

    def velocity_row(second):
        return dict(utc=f'12:00:{second:02}Z', status=1, velocity_ne_mps=[-200., 10.])

    attitude, velocity = [attitude_row(i) for i in range(2)], [velocity_row(i) for i in range(2)]
    compare_rows(attitude, velocity, 2)
    with pytest.raises(ValueError, match='receiver'):
        compare_rows(attitude, velocity[::-1], 2)
    velocity[-1]['velocity_ne_mps'][0] = None
    with pytest.raises(ValueError, match='receiver'):
        compare_rows(attitude, velocity, 2)
