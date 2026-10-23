# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lazy hash-checked access to explicit closed-study records and archive aliases."""
import json
from pathlib import Path
from .artifacts import ArchiveStore,digest,encoded,safe_path


def load_python_reference(raw,*,name,sha256):
    """Load an explicitly selected, hash-verified repository source reference.

    This executes trusted frozen project code, not untrusted uploaded data.
    Relative imports remain in lll; their source/environment freeze is a separate
    prerequisite. A module name cannot silently switch to different source bytes.
    """
    import sys
    import types
    if (not isinstance(raw,bytes) or digest(raw)!=sha256 or not isinstance(name,str)
            or not name.startswith('lll.') or any(not v.isidentifier() for v in name.split('.'))):
        raise ValueError('explicit analysis module and matching source hash required')
    if name in sys.modules:
        module=sys.modules[name]
        if getattr(module,'__lll_source_hash__',None)!=sha256:raise ValueError('reference module identity already bound')
        return module
    module=types.ModuleType(name);module.__package__=name.rpartition('.')[0]
    module.__file__='<sealed:'+sha256+'>';module.__lll_source_hash__=sha256
    code=compile(raw,module.__file__,'exec');sys.modules[name]=module
    try:exec(code,module.__dict__)
    except BaseException:
        if sys.modules.get(name) is module:del sys.modules[name]
        raise
    return module


class ClosedStudy:
    def __init__(self,root,prefix,*,store=None):
        self.root=Path(root).resolve();safe_path(self.root,prefix);self.prefix=prefix.rstrip('/')
        self.store=store or ArchiveStore(self.root);self.owns_store=store is None
        self.catalog=self.store.catalog();self.cache={};self.envelopes={}
        try:
            try:self.completion=self.read('completion.json')
            except FileNotFoundError as exc:raise ValueError('closed study required') from exc
            self.manifest=self.read('manifest.json',self.completion['manifest_sha256'])
            self.summary=self.read('summary.json',self.completion['summary_sha256'])
            self.tasks={t['identity']:t for t in self.manifest['tasks']}
            self.rows={r['identity']:r for r in self.summary['results']}
            if (self.completion['state'] not in ('complete','terminal')
                    or self.summary['state']!=self.completion['state']
                    or len(self.tasks)!=len(self.manifest['tasks'])
                    or len(self.rows)!=len(self.summary['results']) or not set(self.rows)<=set(self.tasks)
                    or self.summary['total']!=len(self.tasks) or self.summary['completed']!=len(self.rows)):
                raise ValueError('closed identities or completion counts differ')
        except Exception:self.close();raise

    def reference(self,record,*,raw=False):
        name=record['path'];safe_path(self.root,name)
        if name not in self.cache:self.cache[name]=self.store._read(name,self.catalog)
        data=self.cache[name]
        if record.get('sha256') is not None and digest(data)!=record['sha256']:
            raise ValueError('closed reference hash mismatch: '+name)
        return data if raw else json.loads(data)

    def read(self,name,expected=None,*,raw=False):
        return self.reference(dict(path=self.prefix+'/'+name,sha256=expected),raw=raw)

    def input(self,key,*,raw=False):
        record=self.manifest['inputs'][key]
        return self.read(record['path'],record['sha256'],raw=raw)

    def envelope(self,identity):
        if identity not in self.envelopes:
            row=self.rows[identity];value=self.read(row['artifact'],row['artifact_sha256'])
            if (value['identity']!=identity or value['manifest_sha256']!=self.completion['manifest_sha256']
                    or digest(encoded(value['result']))!=value['result_sha256']
                    or value['result']['passed']!=row['passed']):
                raise ValueError('closed result identity or hash differs')
            self.envelopes[identity]=value
        return self.envelopes[identity]

    def artifact(self,identity,name,*,raw=False):
        path='artifacts/'+identity+'/'+name
        return self.read(path,self.envelope(identity)['artifacts'][path],raw=raw)

    def close(self):
        if self.owns_store:self.store.close()
