# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run the frozen training worker with the shared recovery metadata."""

from . import esa_repeat_turn_execution as original

ID = 'esa-repeat-turn-forecast-v2'
CONTINUATION_INPUTS = frozenset({
    'continuation-parent-manifest', 'continuation-policy', 'continuation-plan',
    'continuation-qualification-request', 'continuation-qualification-report',
})


class TrainingContext:
    def __init__(self, context, inputs):
        self._context = context
        self.manifest = dict(context.manifest, inputs=inputs)

    def input_path(self, key=None):
        if key is None:
            key = self._context.task['input_key']
        if key not in self.manifest['inputs']:
            raise ValueError('input is outside the training-only selection')
        return self._context.input_path(key)

    def __getattr__(self, name):
        return getattr(self._context, name)


def evaluate(task, context):
    training = original.input_keys()
    inputs = context.manifest['inputs']
    if set(inputs) not in (training, training | CONTINUATION_INPUTS):
        raise ValueError('exact training inputs and complete optional continuation metadata required')
    return original.evaluate(task, TrainingContext(context, {key: inputs[key] for key in training}))
