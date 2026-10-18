# SPDX-License-Identifier: AGPL-3.0-or-later
"""A reused source directory must acquire only one exclusive lock."""
import fcntl
import hashlib
import importlib.util
from pathlib import Path


def worker():
    path=Path(__file__).with_name('ilvis0_remaining_free_time_v2_worker.py')
    assert path.exists(), 'deduplicated-lock launcher is missing'
    spec=importlib.util.spec_from_file_location('remaining_free_time_v2',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def test_shared_sources_acquire_one_real_exclusive_lock(tmp_path):
    module=worker();other=tmp_path/'other';other.mkdir()
    directories=module.lock_directories(tmp_path,other,tmp_path/'.',other)
    assert directories==[tmp_path.resolve(),other.resolve()]
    files=[]
    try:
        for directory in directories:
            lock=(directory/'worker.lock').open('a+');files.append(lock)
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    finally:
        for lock in files:lock.close()


def test_new_freeze_preserves_first_attempt_and_scientific_executor():
    module=worker();before=hashlib.sha256(module.TEMPLATE.read_bytes()).hexdigest()
    executor=module.build_executor()
    assert hashlib.sha256(module.TEMPLATE.read_bytes()).hexdigest()==before
    assert executor.OUTPUT.name=='ilvis0-remaining-free-time-v2-20261018'
    assert executor.VERSION=='ilvis0-remaining-two-case-free-time-v2'
    assert executor.TESTS==38 and executor.lock_directories is module.lock_directories
    assert executor.__file__==str(Path(module.__file__).resolve())
    source=module.executor_source(module.parent.TEMPLATE.read_text())
    assert 'for directory in lock_directories(OUTPUT,PARENT,ENDPOINTS,CONTROLS):' in source
    assert 'maximum_evaluations=80' in source and 'verify_stability' in source


def test_original_two_case_population_and_allowance_stay_fixed():
    from test_ilvis0_remaining_free_time_worker import inputs
    executor=worker().build_executor();plan=executor.make_plan(*inputs())
    assert plan['version']==executor.VERSION
    assert plan['maximum_starts']==6 and plan['maximum_optimizer_starts']==4
    assert plan['maximum_native_evaluations']==342 and plan['numerical_threads']==4
    assert sum(t['maximum_fit_calls']+t['maximum_diagnostic_calls'] for t in plan['tasks'])==342
