# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only checks: missing sectors must never become a complete union."""
import json
from lll import ilvis0_control_shards as runner
import ilvis0_longer_acceleration_cover as report


def test_complete_and_missing_sector_publication(tmp_path,monkeypatch):
    for omit in (False,True):
        project=tmp_path/str(omit);project.mkdir();(project/'adapter.py').write_text('# fixture\n')
        previous=dict(cases=[dict(case_key=f'case-{m}-{p}-400',union_width_m=[1.,2.,3.]) for m in range(3) for p in range(2)])
        (project/'short.json').write_text(json.dumps(previous))
        tasks=[dict(identity=f'c-{m}-{p}-{s}',payload=dict(model=m,profile=bool(p),sector=s),input_key='short-unions',
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))
            for m in range(3) for p in range(2) for s in range(8)]
        data=project/'data';public=project/'public';public.mkdir();(public/'PLAN.md').write_text('Fixture scope.\n')
        manifest=runner.prepare(data,project_root=project,tasks=tasks,sources=['adapter.py'],inputs={'short-unions':'short.json'},
            adapter='adapter.py',environment=runner.runtime_environment())
        for task in manifest['tasks'][:-1] if omit else manifest['tasks']:
            context=runner.TaskContext(data,task['shard'],task['identity']);s=task['payload']['sector']
            context.finish(dict(passed=True,scientific_decision='abstain',excluded=False,
                future_lower_m=[-s,-s,-s],future_upper_m=[s+1,s+2,s+3]))
        runner._finish_study(data,manifest)
        monkeypatch.setattr(report,'DATA',data);monkeypatch.setattr(report,'PUBLIC',public)
        report.publication();union=json.loads((public/'case-unions.json').read_text())
        assert union['all_cases_complete'] is (not omit)
        assert len(union['cases'])==6
        assert union['cases'][0]['union_width_m']==[15.,16.,17.]
        assert union['cases'][-1]['complete'] is (not omit)
        assert union['cases'][-1]['completed']==(7 if omit else 8)
        assert union['scientific_decision']=='abstain'
        assert 'confidence intervals' in (public/'README.md').read_text()
