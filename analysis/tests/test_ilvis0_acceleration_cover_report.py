# SPDX-License-Identifier: AGPL-3.0-or-later
"""Standard-library-only publication checks; no numerical thread allocation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[2]/'docs/ilvis0-acceleration-cover/build_report.py'
spec=importlib.util.spec_from_file_location('acceleration_cover_publication',SOURCE)
report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)


class PublicationTests(unittest.TestCase):
    def fixture(self,root):
        def write(name,value):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));return hashlib.sha256(p.read_bytes()).hexdigest()
        tasks=[];rows=[];cases=[];artifacts={}
        for m in range(3):
            for p in range(2):
                key=f'case-{m}-{p}-400'
                for sector in range(8):
                    identity=f'{m}-{p}-{sector}';task=dict(identity=identity,sector=sector,model=m,profile=bool(p),packets=400,
                        training_times=[.2,.35,.6,.9,1.2,1.5],future_time=1.8);tasks.append(task)
                    name='results/'+identity+'.json'
                    digest=write(name,dict(identity=identity,passed=True,case_key=key,task=task,
                        known_truth_retained=True,excluded=False,future_truth_m=[0.,0.,0.],future_lower_m=[-1.,-2.,-3.],future_upper_m=[1.,2.,3.]))
                    artifacts[name]=digest;rows.append(dict(identity=identity,passed=True,artifact=name,artifact_sha256=digest))
                cases.append(dict(case_key=key,completed=True,future_truth_contained=True,union_lower_m=[-1.,-2.,-3.],
                    union_upper_m=[1.,2.,3.],union_width_m=[2.,4.,6.],baseline_width_m=[200.,200.,200.],
                    width_ratio=[.01,.02,.03],tenfold_width_improvement=True))
        artifacts['inputs/baselines.json']=write('inputs/baselines.json',{c['case_key']:dict(width_after_m=[200.,200.,200.]) for c in cases})
        artifacts['manifest.json']=write('manifest.json',dict(tasks=tasks,inputs=dict(baselines=dict(path='inputs/baselines.json',sha256=artifacts['inputs/baselines.json']))))
        artifacts['summary.json']=write('summary.json',dict(state='complete',passed=True,results=rows,charged=dict(native_calls=144),elapsed_s=100.))
        artifacts['completion.json']=write('completion.json',dict(state='complete',manifest_sha256=artifacts['manifest.json'],summary_sha256=artifacts['summary.json']))
        artifacts['case-unions.json']=write('case-unions.json',dict(cases=cases,all_cases_complete=True))
        artifacts['case-comparison.json']=write('case-comparison.json',dict(all_cases_complete=True,tenfold_vs_original=True))
        write('evidence-receipt.json',dict(artifacts=artifacts));return artifacts,write

    def test_saved_complete_union_renders_without_native_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);self.fixture(root);evidence=report.audit(root);text=report.render(evidence)
            self.assertTrue(evidence['target']);self.assertIn('48 sectors pass correctness',text)
            self.assertIn('not measured aircraft errors',text)

    def test_changed_or_escaping_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);artifacts,write=self.fixture(root)
            write('results/0-0-0.json',dict(changed=True))
            with self.assertRaises(ValueError):report.audit(root)
            with self.assertRaises(ValueError):report._path(root,'../outside')

    def test_union_cannot_omit_a_sector_even_with_updated_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);artifacts,write=self.fixture(root);name='results/0-0-7.json'
            value=json.loads((root/name).read_text());value['task']['sector']=6
            artifacts[name]=write(name,value)
            summary=json.loads((root/'summary.json').read_text())
            next(r for r in summary['results'] if r['artifact']==name)['artifact_sha256']=artifacts[name]
            artifacts['summary.json']=write('summary.json',summary)
            artifacts['completion.json']=write('completion.json',dict(state='complete',manifest_sha256=artifacts['manifest.json'],summary_sha256=artifacts['summary.json']))
            write('evidence-receipt.json',dict(artifacts=artifacts))
            with self.assertRaises(ValueError):report.audit(root)

    def test_false_improvement_claim_is_recomputed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);artifacts,write=self.fixture(root)
            baselines=json.loads((root/'inputs/baselines.json').read_text())
            baselines['case-0-0-400']['width_after_m']=[1.,1.,1.]
            artifacts['inputs/baselines.json']=write('inputs/baselines.json',baselines)
            manifest=json.loads((root/'manifest.json').read_text())
            manifest['inputs']['baselines']['sha256']=artifacts['inputs/baselines.json']
            artifacts['manifest.json']=write('manifest.json',manifest)
            unions=json.loads((root/'case-unions.json').read_text())
            unions['cases'][0]['baseline_width_m']=[1.,1.,1.];unions['cases'][0]['width_ratio']=[2.,4.,6.]
            artifacts['case-unions.json']=write('case-unions.json',unions)
            artifacts['completion.json']=write('completion.json',dict(state='complete',manifest_sha256=artifacts['manifest.json'],summary_sha256=artifacts['summary.json']))
            write('evidence-receipt.json',dict(artifacts=artifacts))
            with self.assertRaises(ValueError):report.audit(root)


if __name__=='__main__':unittest.main()
