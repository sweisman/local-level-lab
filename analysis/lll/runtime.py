# SPDX-License-Identifier: AGPL-3.0-or-later
"""Actual numerical versions, independent of optional git provenance."""
import platform

import numpy as np
import scipy

from .inference_policy import digest


def numerical_environment():
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}


def numerical_environment_hash():
    return digest(numerical_environment())


def check_environment(value):
    if value != numerical_environment():
        raise ValueError("numerical environment mismatch; regenerate under the frozen Python/NumPy/SciPy versions")
