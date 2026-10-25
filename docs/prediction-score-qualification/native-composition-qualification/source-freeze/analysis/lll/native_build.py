# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source/compiler-bound cached C++ builds with explicit build accounting."""
import fcntl
import json
from pathlib import Path
import re
import shutil
import subprocess

from .studies.artifacts import atomic,digest,encoded


def cpp(directory,source,*,prefix,expected_sha256,reserve_build):
    if (not isinstance(source,bytes) or not source or len(source)>1024*1024
            or digest(source)!=expected_sha256 or not isinstance(prefix,str)
            or re.fullmatch(r'[a-z][a-z0-9-]{0,47}',prefix) is None or not callable(reserve_build)):
        raise ValueError('bound source hash, safe prefix and explicit build accounting required')
    compiler=shutil.which('c++')
    if compiler is None:raise ValueError('configured C++ compiler unavailable')
    version=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]
    basis=dict(version='native-cpp-cache-v1',source_sha256=expected_sha256,compiler=version,
        compiler_executable=compiler,flags=['-O2','-std=c++17','-fPIC','-shared'])
    key=digest(encoded(basis));directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    stem=prefix+'-'+key;unit=directory/(stem+'.cpp');binary=directory/(stem+'.so');record=directory/(stem+'.json')
    with (directory/(stem+'.lock')).open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if unit.exists() and unit.read_bytes()!=source:raise ValueError('cached native source hash differs')
        if not unit.exists():atomic(unit,source)
        if binary.exists() or record.exists():
            if not binary.exists() or not record.exists():raise ValueError('incomplete native cache; no uncharged repair')
            metadata=json.loads(record.read_bytes())
            if (any(metadata.get(k)!=v for k,v in basis.items())
                    or metadata.get('binary_sha256')!=digest(binary.read_bytes())):
                raise ValueError('cached native binary/compiler binding differs')
        else:
            reserve_build();partial=binary.with_suffix('.partial.so')
            subprocess.run([compiler,*basis['flags'],str(unit),'-o',str(partial)],check=True,capture_output=True)
            partial.replace(binary);metadata=dict(basis,binary_sha256=digest(binary.read_bytes()),cache_sha256=key,
                source_file=unit.name,binary_file=binary.name)
            atomic(record,encoded(metadata))
    return binary,metadata
