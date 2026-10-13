# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest


def policy():
    assert Path(__file__).parents[1].joinpath('lll/compute_budget.py').exists(), 'thread-budget guard missing'
    return importlib.import_module('lll.compute_budget')


def test_single_worker_defaults_to_four_threads():
    assert policy().allocation() == dict(workers=1, threads=4, reserved=0, total=4)


@pytest.mark.parametrize('workers,threads', [(2, 2), (4, 1)])
def test_parallel_workers_share_four_threads(workers, threads):
    assert policy().allocation(workers=workers)['threads'] == threads


def test_active_two_thread_job_reserves_half_the_budget():
    assert policy().allocation(reserved=2)['threads'] == 2


@pytest.mark.parametrize('options', [dict(workers=2, threads=4), dict(threads=5),
    dict(threads=4, reserved=2), dict(workers=5), dict(reserved=4), dict(workers=0),
    dict(threads=0), dict(workers=True), dict(reserved=-1)])
def test_oversubscription_and_invalid_allocations_are_rejected(options):
    with pytest.raises(ValueError):
        policy().allocation(**options)


def test_launcher_overrides_inherited_numerical_settings_without_importing_numpy():
    policy()
    target = Path(__file__).with_name('run_numerical.py')
    assert target.exists(), 'guarded numerical launcher missing'
    environment = dict(os.environ, OPENBLAS_NUM_THREADS='32', OMP_NUM_THREADS='32', MKL_NUM_THREADS='32')
    command = [sys.executable, str(target), '--reserved-threads', '2', '--', sys.executable, '-c',
        'import os,sys; assert "numpy" not in sys.modules; print(" ".join(os.environ[k] for k in '
        '("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS")))']
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '2 2 2'


def test_launcher_rejects_oversubscription_before_starting_target(tmp_path):
    policy()
    target = Path(__file__).with_name('run_numerical.py')
    assert target.exists(), 'guarded numerical launcher missing'
    output = tmp_path/'never-created'
    command = [sys.executable, str(target), '--workers', '2', '--threads', '4', '--',
               sys.executable, '-c', 'import pathlib,sys; pathlib.Path(sys.argv[1]).touch()', str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0
    assert not output.exists()
