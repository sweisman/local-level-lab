# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.ilvis0_portable_refit import check_pins, select_task


def test_portable_refit_rejects_toolchain_or_environment_changes():
    pins = dict(executables={'cc': 'a', 'c++': 'b', 'python': 'c'},
                environment={'python': 'original'})
    check_pins(pins, dict(pins))
    with pytest.raises(ValueError, match='toolchain'):
        check_pins(pins, dict(pins, executables={**pins['executables'], 'cc': 'changed'}))
    with pytest.raises(ValueError, match='environment'):
        check_pins(pins, dict(pins, environment={'python': 'changed'}))


def test_portable_refit_keeps_one_control_and_its_frozen_inputs():
    segment = '3df34ea39a6cbdbe15bb0f36'
    identity = segment + '-sphere_rotating'
    task = dict(identity=identity, index=1, shard=1, segment_id=segment,
                input_key=segment+'-packets', limits={'native_calls': 61})
    selected, inputs = select_task({identity: task})
    assert selected == {k: v for k, v in task.items() if k not in ('index', 'shard')}
    assert set(inputs) == {'recipe', 'recovery', 'recovery_tests', 'qualification',
                           'qualification_tests', segment+'-packets', segment+'-queries',
                           segment+'-training', identity+'-reference'}
    with pytest.raises(ValueError, match='allowance'):
        select_task({identity: dict(task, limits={'native_calls': 62})})
