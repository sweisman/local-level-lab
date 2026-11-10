# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four-thread allocations for new work; no numerical imports or frozen changes."""
MAX_THREADS = 4
THREAD_KEYS = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
               'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')


def allocation(*, workers=1, threads=None, reserved=0):
    """Count worker × numerical-thread capacity plus other active allocations."""
    if type(workers) is not int or workers < 1 or type(reserved) is not int or reserved < 0:
        raise ValueError('positive integer workers and nonnegative reserved threads required')
    available = MAX_THREADS-reserved
    if threads is None:
        threads = available//workers
    if type(threads) is not int or threads < 1 or workers*threads+reserved > MAX_THREADS:
        raise ValueError('numerical allocation exceeds the four-thread total budget')
    return dict(workers=workers, threads=threads, reserved=reserved, total=workers*threads+reserved)


def environment(*, workers=1, threads=None, reserved=0):
    """Settings must be applied before importing numerical libraries."""
    selected = allocation(workers=workers, threads=threads, reserved=reserved)
    value = str(selected['threads'])
    return {**{key: value for key in THREAD_KEYS}, 'OMP_THREAD_LIMIT': value,
            'OMP_MAX_ACTIVE_LEVELS': '1'}
