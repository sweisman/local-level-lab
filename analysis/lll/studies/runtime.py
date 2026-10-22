# SPDX-License-Identifier: AGPL-3.0-or-later
"""One metadata/lifecycle interface, using the existing bounded study engine."""
import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from .artifacts import ArchiveStore, safe_path


@dataclass(frozen=True)
class Definition:
    id:str
    configuration:dict

    @classmethod
    def from_dict(cls,value,root):
        from ..compute_budget import allocation
        from ..ilvis0_control_shards import _tasks
        identity=value.get('id','')
        if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):
            raise ValueError('safe unique study ID required')
        allocation(workers=value['workers'],threads=value['threads'],reserved=0)
        wall=value['maximum_wall_s']
        if type(wall) not in (int,float) or not math.isfinite(wall) or wall<=0:
            raise ValueError('finite positive wall allowance required')
        _tasks(value['tasks'],value['workers'])
        if value['adapter'] not in value['sources']:raise ValueError('adapter must belong to frozen dependencies')
        for name in value['sources']+list(value['inputs'].values()):
            if not safe_path(root,name).is_file():raise ValueError('declared dependency is missing: '+name)
        if any(t['input_key'] not in value['inputs'] for t in value['tasks']):raise ValueError('unknown input')
        return cls(identity,dict(value))

    def prepare(self,root):
        from .. import ilvis0_control_shards as runner
        value=self.configuration;root=Path(root)
        shared=['analysis/tests/ilvis0_control_shards.py','analysis/lll/ilvis0_control_shards.py',
            'analysis/lll/ilvis0_receipt_journal.py','analysis/lll/compute_budget.py','analysis/lll/__init__.py']
        shared.extend(str(p.relative_to(root)) for p in (root/'analysis/lll/studies').glob('*.py'))
        return runner.prepare(root/'data'/self.id,project_root=root,tasks=value['tasks'],
            sources=sorted(set(value['sources']+shared)),inputs=value['inputs'],adapter=value['adapter'],
            workers=value['workers'],threads=value['threads'],maximum_wall_s=value['maximum_wall_s'],
            environment=runner.runtime_environment(),accounting_format='sqlite-v1')


def inspect_study(root,prefix):
    safe_path(root,prefix);store=ArchiveStore(root);out=dict(path=prefix,numerical_work=0)
    for name in ('manifest.json','summary.json','completion.json','authorization.json'):
        try:out[name.removesuffix('.json')]=json.loads(store.read(prefix+'/'+name))
        except FileNotFoundError:pass
    return out


def command(argv=None):
    parser=argparse.ArgumentParser(prog='lll studies',description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3])
    actions=parser.add_subparsers(dest='action',required=True)
    for name in ('inspect','restore','compact','check'):
        sub=actions.add_parser(name);sub.add_argument('prefix',nargs='?',default='')
        if name=='restore':sub.add_argument('--destination',type=Path)
    prep=actions.add_parser('prepare');prep.add_argument('definition',type=Path)
    run=actions.add_parser('run');run.add_argument('prefix');run.add_argument('--reserved-threads',type=int,required=True)
    publish=actions.add_parser('publish');publish.add_argument('prefix');publish.add_argument('--output',required=True)
    publish.add_argument('--text',type=Path,required=True);publish.add_argument('--plan')
    pack=actions.add_parser('archive');pack.add_argument('--restore-verification',type=Path,required=True)
    pack.add_argument('--local-root',type=Path)
    tests=actions.add_parser('test');tests.add_argument('--threads',type=int,default=4)
    tests.add_argument('--reserved-threads',type=int,default=0);tests.add_argument('pytest_arguments',nargs=argparse.REMAINDER)
    args=parser.parse_args(argv);root=args.root.resolve();store=ArchiveStore(root)
    if args.action=='test':
        from .testing import run
        arguments=args.pytest_arguments
        if arguments[:1]==['--']:arguments=arguments[1:]
        return run(root,arguments,threads=args.threads,reserved=args.reserved_threads)
    if args.action=='archive':
        from .migration import migrate,add_local_aliases
        out=migrate(root,restore_destination=args.restore_verification)
        if args.local_root:out.update(add_local_aliases(root,args.local_root))
    elif args.action=='inspect':out=inspect_study(root,args.prefix)
    elif args.action=='prepare':out=Definition.from_dict(json.loads(args.definition.read_text()),root).prepare(root)
    elif args.action=='run':
        from .. import ilvis0_control_shards as runner
        directory=safe_path(root,args.prefix)
        if (directory/'completion.json').exists():raise ValueError('completed study cannot resume')
        out=runner.launch(directory,reserved_threads=args.reserved_threads)
    elif args.action=='publish':
        from ..ilvis0_control_publication import publish
        publish(safe_path(root,args.prefix),safe_path(root,args.output),args.text.read_text(),plan=args.plan)
        from .publication import archive_publication
        out=archive_publication(root,safe_path(root,args.prefix),safe_path(root,args.output))
        out['published']=args.output
    else:
        prefix=args.prefix.rstrip('/')
        if prefix:safe_path(root,prefix)
        names=[n for n in store.catalog()['paths'] if not prefix or n==prefix or n.startswith(prefix+'/')]
        if args.action=='restore':out=dict(restored=store.restore(args.destination or root,names=names),numerical_work=0)
        elif args.action=='compact':out=dict(compacted=store.compact(names=names),numerical_work=0)
        else:out=store.verify()
    print(json.dumps(out,sort_keys=True,default=str));return 0
