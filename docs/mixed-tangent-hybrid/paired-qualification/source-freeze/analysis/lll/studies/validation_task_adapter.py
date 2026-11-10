# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run one pending validation task with the original full scientific manifest.

The stage owns charges and output artifacts. The frozen evaluator sees its
unchanged 4,344-task model matrix, recipe, sources and calibrated threshold.
"""
import json

from lll.studies.artifacts import digest

ADAPTER='analysis/lll/studies/validation_task_adapter.py'


class _OriginalManifestContext:
    def __init__(self,stage,manifest,task):
        self._stage=stage
        # Scientific task matrix and sources remain original. The cooperative
        # deadline belongs to this charged execution stage, whose start seal
        # is checked by timing_case_context through context.manifest.
        self.manifest=dict(manifest,limits=dict(manifest['limits'],
            maximum_wall_s=stage.manifest['limits']['maximum_wall_s']))
        self.task=task

    def __getattr__(self,name):
        return getattr(self._stage,name)


def _original_evaluate(task,context):
    from lll.host_prediction_release import evaluate
    return evaluate(task,context)


def evaluate(task,context):
    original_path=context.input_path('continuation-parent-manifest')
    original=json.loads(original_path.read_bytes())
    policy=json.loads(context.input_path('continuation-policy').read_bytes())
    plan=json.loads(context.input_path('continuation-plan').read_bytes())
    if (digest(original_path.read_bytes())!=policy['parent_manifest_sha256']
            or plan['parent_manifest_sha256']!=policy['parent_manifest_sha256']
            or plan['parent_merged_sha256']!=policy['parent_merged_sha256']
            or context.manifest['sources']!={**original['sources'],
                                            ADAPTER:policy['adapter_sha256']}
            or context.manifest['adapter']!=ADAPTER
            or context.manifest['environment']!=original['environment']
            or context.manifest['numerical_environment']!=original['numerical_environment']
            or set(context.manifest['inputs'])!=set(original['inputs'])|
                {'continuation-parent-manifest','continuation-policy','continuation-plan'}
            or any(context.manifest['inputs'][name]['sha256']!=record['sha256']
                   for name,record in original['inputs'].items())):
        raise ValueError('continuation changed the frozen scientific context')
    old=[item for item in original['tasks'] if item['identity']==task['identity']]
    selected=[item for item in plan['tasks'] if item['identity']==task['identity']]
    scientific={key:value for key,value in task.items() if key not in ('index','shard')}
    if (len(old)!=1 or len(selected)!=1 or scientific!=selected[0]
            or scientific!={key:value for key,value in old[0].items()
                            if key not in ('index','shard')}):
        raise ValueError('continuation task differs from original prescribed fit')
    return _original_evaluate(old[0],_OriginalManifestContext(context,original,old[0]))
