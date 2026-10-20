# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only gates distinguish completion from an unmet usefulness target."""
import json
from lll import ilvis0_control_shards as runner
import ilvis0_transform_cover_worker as report


def test_missing_sector_and_unmet_target_cannot_publish_as_success(tmp_path,monkeypatch):
    for kind in ('complete','missing','target-failure'):
        project=tmp_path/kind;project.mkdir();(project/'adapter.py').write_text('# metadata fixture\n')
        cases=[dict(model=m,profile=bool(p),union_width_m=[100.,100.,100.]) for m in range(3) for p in range(2)]
        if kind=='target-failure':cases[-1]['union_width_m']=[1.,1.,1.]
        (project/'baseline.json').write_text(json.dumps(dict(cases=cases)))
        (project/'ordinary.json').write_text(json.dumps(dict(cases=cases)))
        tasks=[dict(identity=f'case-{m}-{p}-{s}',payload=dict(model=m,profile=bool(p),sector=s),input_key='baseline',
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))
            for m in range(3) for p in range(2) for s in range(8)]
        data=project/'data';public=project/'public';public.mkdir();(public/'PLAN.md').write_text('Metadata fixture only.\n')
        manifest=runner.prepare(data,project_root=project,tasks=tasks,sources=['adapter.py'],
            inputs={'baseline':'baseline.json','ordinary-baseline':'ordinary.json'},adapter='adapter.py',environment=runner.runtime_environment())
        for task in manifest['tasks'][:-1] if kind=='missing' else manifest['tasks']:
            context=runner.TaskContext(data,task['shard'],task['identity']);sector=task['payload']['sector']
            context.finish(dict(passed=True,scientific_decision='abstain',task=task['payload'],excluded=False,
                future_lower_m=[-sector]*3,future_upper_m=[sector+1,sector+2,sector+3]))
        runner._finish_study(data,manifest);monkeypatch.setattr(report,'DATA',data);monkeypatch.setattr(report,'PUBLIC',public)
        report.publish();comparison=json.loads((public/'comparison.json').read_text())
        assert comparison['all_cases_complete'] is (kind!='missing')
        assert comparison['all_cases_twofold'] is (kind=='complete')
        assert comparison['cases'][0]['union_width_m']==[15.,16.,17.]
        assert comparison['scientific_decision']=='abstain'
