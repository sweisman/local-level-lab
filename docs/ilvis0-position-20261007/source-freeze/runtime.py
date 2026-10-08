# SPDX-License-Identifier: AGPL-3.0-or-later
"""Actual numerical versions and thread settings, independent of optional git provenance."""
import os
import platform

import numpy as np
import scipy

from .inference_policy import digest


def numerical_environment():
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "thread_settings": {key: os.environ.get(key) for key in
                                ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")}}


def numerical_environment_hash():
    return digest(numerical_environment())


def check_environment(value):
    if value != numerical_environment():
        raise ValueError("numerical environment mismatch; regenerate under the frozen versions and thread settings")
