# SPDX-License-Identifier: AGPL-3.0-or-later
"""Package sealed software studies without executing their calculations."""
from pathlib import Path
import shutil
from . import ilvis0_control_shards as runner


def publish(data,public,text,*,plan=None):
    data=Path(data);public=Path(public)
    manifest=runner.verify(data);summary=runner.verify_completion(data)
    names={'manifest.json','authorization.json','start.json','start.seal.json','summary.json','completion.json'}
    names.update('source-freeze/'+name for name in manifest['sources'])
    names.update(record['path'] for record in manifest['inputs'].values())
    for row in summary['results']:
        path=runner.path_within(data,row['artifact'])
        names.update((row['artifact'],str(path.with_suffix('.seal.json').relative_to(data))))
        names.update(runner._load(path)['artifacts'])
    for shard in range(manifest['allocation']['workers']):
        directory=data/'shards'/f'{shard:03d}'
        for name in ('done.json','worker.log'):
            if (directory/name).is_file():names.add(str((directory/name).relative_to(data)))
        names.update(str(p.relative_to(data)) for p in (directory/'charges').glob('*.json'))
        if manifest.get('accounting_format')=='sqlite-v1':
            names.add(str((directory/'charges/journal.sqlite').relative_to(data)))
    for name in sorted(names):
        target=runner.path_within(public,name);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(runner.path_within(data,name),target)
    if plan is not None:
        if plan not in manifest['sources']:raise ValueError('publication plan must be frozen')
        shutil.copyfile(runner.path_within(data/'source-freeze',plan),public/'PLAN.md');names.add('PLAN.md')
    (public/'README.md').write_text(text.rstrip()+'\n');names.add('README.md')
    runner._replace(public/'evidence-receipt.json',dict(artifacts={n:runner._sha(public/n) for n in sorted(names)}))


def check(data,public):
    runner.verify_completion(data);public=Path(public)
    for name,digest in runner._load(public/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(public,name))!=digest:
            raise ValueError('published control evidence changed: '+name)
