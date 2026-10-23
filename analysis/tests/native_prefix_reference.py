# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read the hash-verified original cold orchestration; never run its study."""
from functools import lru_cache
from pathlib import Path
import base64
import gzip
import json


@lru_cache(maxsize=1)
def original():
    from lll.studies.closed import load_python_reference
    record=json.loads(Path(__file__).with_name('ilvis0_native_prefix_reference.json').read_text())
    raw=gzip.decompress(base64.b64decode(record['gzip_base64'],validate=True));sha=record['sha256']
    if len(raw)!=record['byte_size']:raise ValueError('sealed cold source size mismatch')
    module=load_python_reference(raw,name='lll._sealed_remainder_native_'+sha[:16],sha256=sha)
    return module,raw
