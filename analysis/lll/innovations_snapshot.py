# SPDX-License-Identifier: AGPL-3.0-or-later
"""Preserve a fixed innovations operation without rerunning its source model."""

import io
import math
import re
from zipfile import BadZipFile, ZipFile

from .state_space_covariance import LinearInnovations
from .studies.artifacts import digest, encoded


VERSION = 'linear-innovations-factors-v1'
FACTORS = ('transition', 'observation', 'lower', 'gain')
HEADER_LIMIT = 8192


def capture(operator):
    """Encode the actual numerical factors, including their source identity."""
    import numpy as np

    if not isinstance(operator, LinearInnovations):
        raise ValueError('complete shared innovations operator required')
    header = dict(version=VERSION, configuration=operator.configuration,
                  log_determinant=operator.log_determinant, storage_bytes=operator.storage_bytes,
                  observation_form=operator.observation_form,
                  epochs=operator.epoch_count, states=operator.state_dimension,
                  observations=operator.observation_dimension)
    result = io.BytesIO()
    factors = {name: getattr(operator, '_'+name).astype('<f8', copy=False)
               for name in FACTORS}
    np.savez_compressed(result, header=np.frombuffer(encoded(header), dtype=np.uint8), **factors)
    return result.getvalue()


def restore(payload, *, expected_sha256, expected_configuration, maximum_bytes):
    """Load the hash-bound factors with explicit uncompressed memory limits."""
    import json
    import numpy as np

    if (not isinstance(payload, bytes) or digest(payload) != expected_sha256
            or not isinstance(expected_configuration, str)
            or not re.fullmatch(r'[0-9a-f]{64}', expected_configuration)
            or type(maximum_bytes) is not int or maximum_bytes <= 0):
        raise ValueError('expected immutable snapshot, configuration and storage limit required')
    try:
        with ZipFile(io.BytesIO(payload)) as members:
            names = sorted(name+'.npy' for name in ('header', *FACTORS))
            if (sorted(members.namelist()) != names
                    or members.getinfo('header.npy').file_size > HEADER_LIMIT
                    or sum(members.getinfo(name+'.npy').file_size for name in FACTORS)
                       > maximum_bytes + len(FACTORS)*HEADER_LIMIT):
                raise ValueError('snapshot exceeds declared storage or has unexpected members')
        with np.load(io.BytesIO(payload), allow_pickle=False) as archive:
            raw_header = archive['header']
            if raw_header.ndim != 1 or raw_header.dtype != np.dtype('uint8'):
                raise ValueError('byte-encoded snapshot header required')
            header = json.loads(raw_header.tobytes())
            if (set(header) != {'version', 'configuration', 'epochs', 'states', 'observations',
                               'observation_form', 'log_determinant', 'storage_bytes'}
                    or header['version'] != VERSION
                    or header['configuration'] != expected_configuration
                    or header['observation_form'] not in ('after_transition',
                                                         'before_transition_shared_noise')):
                raise ValueError('snapshot identity, version or observation timing differs')
            n, k, d = (header[name] for name in ('epochs', 'states', 'observations'))
            if (any(type(value) is not int for value in (n,k,d))
                    or not (1 <= n <= 100000 and 1 <= k <= 40 and 1 <= d <= 3)):
                raise ValueError('supported innovations dimensions required')
            shapes = dict(transition=(n,k,k), observation=(n,d,k), lower=(n,d,d), gain=(n,k,d))
            storage = n*(k*k+2*k*d+d*d)*8
            if storage != header['storage_bytes'] or storage > maximum_bytes:
                raise ValueError('declared factors exceed storage allowance')
            factors = {}
            for name, shape in shapes.items():
                # Read the NPY shape and dtype before letting NumPy allocate.
                with archive.zip.open(name+'.npy') as stream:
                    if np.lib.format.read_magic(stream) != (1, 0):
                        raise ValueError('supported snapshot array format required')
                    dims, fortran, dtype = np.lib.format.read_array_header_1_0(stream)
                    if dims != shape or fortran or dtype != np.dtype('<f8'):
                        raise ValueError('snapshot factor shape, storage order or type differs')
                array = np.asarray(archive[name], dtype=float)
                if not np.all(np.isfinite(array)):
                    raise ValueError('finite innovations factors required')
                factors[name] = array
    except (BadZipFile, KeyError, EOFError, TypeError, OverflowError) as error:
        raise ValueError('malformed innovations snapshot') from error
    lower = factors['lower']
    diagonal = np.diagonal(lower, axis1=1, axis2=2)
    if np.any(diagonal <= 0) or np.any(np.triu(lower, k=1)):
        raise ValueError('innovations factors require positive triangular diagonals')
    determinant = float(2*np.log(diagonal).sum())
    if not math.isclose(determinant, header['log_determinant'], rel_tol=1e-14, abs_tol=1e-14):
        raise ValueError('innovations determinant differs from the factor receipt')
    # The saved factors already include the covariance recurrence. Restore the
    # same operations without treating them as newly estimated error inputs.
    loaded = LinearInnovations.__new__(LinearInnovations)
    loaded.epoch_count, loaded.state_dimension, loaded.observation_dimension = n, k, d
    loaded.configuration = expected_configuration
    loaded.observation_form = header['observation_form']
    loaded.storage_bytes = storage
    loaded.log_determinant = header['log_determinant']
    loaded.error_law_calibrated = loaded.parameter_uncertainty_included = False
    for name, array in factors.items():
        array.setflags(write=False)
        setattr(loaded, '_'+name, array)
    return loaded
