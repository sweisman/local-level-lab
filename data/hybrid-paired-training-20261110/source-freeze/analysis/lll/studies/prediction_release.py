# SPDX-License-Identifier: AGPL-3.0-or-later
"""Declarative fresh cohorts over an unchanged qualified prediction method."""
from dataclasses import dataclass
import json
from pathlib import Path
import re

COMMON_SOURCE='analysis/lll/studies/prediction_release.py'
REPORTING_SOURCE='analysis/lll/prediction_calibration_report.py'


@dataclass(frozen=True)
class PredictionRelease:
    parent:object
    suffix:str
    scope:str
    plan:str
    adapter:str
    optimizer_report_path:str
    first_seeds:tuple
    reporting_updates:tuple
    tests:tuple
    required_case_names:tuple

    def __post_init__(self):
        if not isinstance(self.suffix,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,60}',self.suffix):
            raise ValueError('safe explicit release suffix required')
        if (len(self.first_seeds)!=2 or any(type(v) is not int or v<0 for v in self.first_seeds)
                or not self.scope or not self.tests or not self.required_case_names):
            raise ValueError('explicit finite release and qualification required')
        if (len({u[0] for u in self.reporting_updates})!=len(self.reporting_updates)
                or any(len(u)!=3 or u[0]!=REPORTING_SOURCE
                       or any(not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) for h in u[1:])
                       for u in self.reporting_updates)):
            raise ValueError('only an exact reporting-only source bridge is permitted')
        groups=[set(self.recipe(role)['seeds']) for role in ('calibration','validation')]
        if groups[0]&groups[1] or any(g&set(self.EXCLUDED_SEEDS) for g in groups):
            raise ValueError('fresh disjoint cohorts required; declared old cohorts stay excluded')

    @property
    def EXCLUDED_SEEDS(self):
        return tuple(sorted(set(self.parent.EXCLUDED_SEEDS)
            |set(self.parent.recipe('calibration')['seeds'])|set(self.parent.recipe('validation')['seeds'])))

    @property
    def REQUIRED_SOURCES(self):
        return self.parent.REQUIRED_SOURCES|{self.adapter,COMMON_SOURCE,'analysis/lll/studies/recovery.py'}

    @property
    def SCOPE(self):return self.scope

    @property
    def ADAPTER(self):return self.adapter

    @property
    def PARENT(self):return self.parent.PARENT

    @property
    def allowed_parent_updates(self):return frozenset(u[0] for u in self.reporting_updates)

    @property
    def source_updates(self):
        return {name:dict(original_sha256=old,current_sha256=new) for name,old,new in self.reporting_updates}

    @property
    def required_tests(self):return tuple(self.parent.required_tests)+self.required_case_names

    @property
    def required_report_tests(self):
        return tuple(self.parent.required_report_tests)+('test_handoff_rejects_interrupted_cohort_even_with_finite_draw_scores',)

    def identity(self,role):
        self.recipe(role)
        return 'prediction-'+role+'-'+self.suffix

    def recipe(self,role):
        r=self.parent.recipe(role);first=self.first_seeds[0 if role=='calibration' else 1]
        return dict(r,version='host-prediction-release-v1',seeds=list(range(first,first+len(r['seeds']))),
                    excluded_seeds=list(self.EXCLUDED_SEEDS),require_uninterrupted_cohort=True)

    def case_recipe(self,seed):
        from lll import prediction_calibration_study as original
        if type(seed) is not int or not any(seed in self.recipe(role)['seeds'] for role in ('calibration','validation')):
            raise ValueError('one fresh preassigned release seed required')
        return dict(original._configured(seed),workers=self.recipe('calibration')['workers'])

    def tasks(self,role,population_sha256):
        from lll.prediction_calibration_study import family_tasks
        return family_tasks(role,population_sha256,policy=self.recipe(role),case_provider=self.case_recipe)

    def population(self,sources,environment):
        from .artifacts import digest,encoded
        if not self.REQUIRED_SOURCES<=set(sources):raise ValueError('complete release sources required')
        p=self.parent.population(sources,environment)
        p['descriptor'].update(version='host-prediction-population-v1',execution_lifetime='host-user-service',
                               interruption_reporting='sealed-interruption-status-v1')
        return dict(sha256=digest(encoded(p['descriptor'])),descriptor=p['descriptor'])

    def policy(self):
        p=self.parent.policy()
        for name in ('recipe','tasks','case_recipe','population','EXCLUDED_SEEDS','SCOPE',
                     'qualification_sources','required_report_tests'):
            setattr(p,name,getattr(self,name))
        p.plan=self.plan
        return p

    def verify_optimizer_gate(self,report,binding,current,environment):
        # Reconstruct the exact historical binding only for the declared reporting
        # change. The original checker still hashes the entire historical map.
        sources=dict(binding.get('sources',{}));restored=dict(current)
        for name,old,new in self.reporting_updates:
            if name in sources or current.get(name)!=new:
                raise ValueError('exact separately qualified reporting update required')
            sources[name]=old;restored[name]=old
        return self.parent.verify_optimizer_gate(report,dict(binding,sources=sources),restored,environment)

    def optimizer_report(self,root):
        """Reuse the pinned qualification with an explicit current-source bridge.

        No historical verdict is recomputed under a changed reporting module.
        Both sealed parent completions and every other current source still bind.
        """
        from .artifacts import ArchiveStore,digest,encoded,safe_path
        from .closed import ClosedStudy
        from lll.airquantumgrav_inventory import environment
        root=Path(root).resolve();store=ArchiveStore(root)
        try:
            report=json.loads(store.read(self.optimizer_report_path))
            if digest(encoded(report))!=self.parent.GATE_REPORT_SHA256:
                raise ValueError('exact original combined optimizer report required')
            binding=None;env=environment()
            for prefix,expected in report['evidence'].items():
                old=ClosedStudy(root,prefix,store=store)
                try:
                    if old.completion!=expected or old.input('qualification-environment')!=env:
                        raise ValueError('original optimizer completion or environment changed')
                    if prefix==self.PARENT:
                        original=dict(old.manifest['sources'])
                        binding=dict(sources={n:h for n,h in original.items() if n not in self.allowed_parent_updates},
                                     environment=env,completion=dict(old.completion))
                finally:old.close();del old
            if binding is None:raise ValueError('qualified optimizer parent missing')
            current={n:digest(safe_path(root,n).read_bytes()) for n in original}
            self.verify_optimizer_gate(report,binding,current,env)
            return report
        finally:store.close()

    def qualification_sources(self,root):
        from .closed import ClosedStudy
        from .dependencies import source_closure
        parent=ClosedStudy(root,self.PARENT)
        try:names=set(parent.manifest['sources'])
        finally:parent.close()
        own=[self.adapter,self.plan,COMMON_SOURCE,*self.tests,*self.parent.TESTS]
        return sorted(names|set(source_closure(root,own)))

    def evaluate(self,task,context):
        from lll.airquantumgrav_inventory import environment
        from lll.coordinate_optimizer_study import kernels
        from lll.timing_optimizer_native_study import timing_case_context
        from lll.prediction_calibration_study import evaluate
        if json.loads(context.input_path('parent-source-updates').read_bytes())!=self.source_updates:
            raise ValueError('frozen reporting source bridge differs')
        self.verify_optimizer_gate(json.loads(context.input_path('optimizer-gate').read_bytes()),
            json.loads(context.input_path('optimizer-binding').read_bytes()),context.manifest['sources'],environment())
        return evaluate(task,context,protocol=self.policy(),kernel_provider=kernels,case_context=timing_case_context)

    def prepare(self,root,*,role,qualification,calibration=None):
        from lll.compensated_prediction_release import prepare
        if role=='validation' and calibration is None:raise ValueError('closed fresh calibration handoff required')
        return prepare(root,role=role,qualification=qualification,calibration=calibration,definition=self)

    def launch(self,root,*,role,reserved_threads):
        import shutil
        from lll.ilvis0_control_shards import launch
        from .recovery import inspect
        root=Path(root).resolve();minimum=self.recipe(role)['minimum_free_bytes']
        if shutil.disk_usage(root).free<minimum:
            raise ValueError(f'phase requires at least {minimum//2**30} GiB free disk before launch')
        prefix='data/'+self.identity(role);advice=inspect(root,prefix)
        if advice['state']!='uncharged_work_available':raise ValueError('recovery check blocks launch: '+advice['state'])
        return launch(root/prefix,reserved_threads=reserved_threads)
