# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pair whole-period forecast intervals before opening generated later truth."""
import math
import re

from .prediction_paired_bound_family import _binding_sha
from .prediction_paired_law import run as paired_run
from .prediction_simultaneous_law_family import union_simultaneous_intervals


TARGETS = dict(physical_position='simultaneous-bounded-physical.json',
               receiver_measurement='simultaneous-bounded-receiver.json')


def run(laws, *, fit_candidate, save, withheld_truth,
        minimum_simultaneous_coverage=.975):
    if (not all(callable(value) for value in
                (fit_candidate, save, withheld_truth)) or
            not isinstance(minimum_simultaneous_coverage, (int, float)) or
            not math.isfinite(minimum_simultaneous_coverage) or
            not 0 < minimum_simultaneous_coverage < 1):
        raise ValueError('finite whole-period target and callbacks required')
    saved = {}
    candidates = {}
    unions = {}

    def capture(name, value):
        if name in saved:
            raise ValueError('duplicate paired artifact')
        save(name, value)
        saved[name] = value

    def fit(law, save_candidate):
        record = fit_candidate(law, save_candidate)
        candidates[law] = record
        return record

    def open_truth():
        comparison = saved.get('training-law-comparison.json')
        if not isinstance(comparison, dict):
            raise ValueError('training comparison must precede withheld truth')
        binding = _binding_sha(candidates, laws)
        expected_training = candidates[laws[0]]['binding']['training_epochs']
        expected_future = candidates[laws[0]]['binding']['prediction_epochs']
        for target, artifact in TARGETS.items():
            if comparison['status'] == 'numerically_unqualified':
                interval = dict(supported=False, reason='candidate_fit_unqualified',
                                prediction_target=target, candidate_laws=list(laws),
                                binding_sha256=binding, selected_law=None,
                                coverage_calibrated=False,
                                scientific_decision='abstain')
            else:
                alternatives = {}
                for law in laws:
                    bounded = saved.get(law+'/'+artifact)
                    diagnostic = candidates[law].get(
                        'physical_diagnostic' if target == 'physical_position'
                        else 'diagnostic')
                    descriptor = (diagnostic.get('error_operator')
                                  if isinstance(diagnostic, dict) else None)
                    configuration = (descriptor.get('operator_configuration')
                                     if isinstance(descriptor, dict) else None)
                    if (not isinstance(bounded, dict) or
                            bounded.get('training_epochs') != expected_training or
                            bounded.get('prediction_epochs') != expected_future or
                            bounded.get('coordinate_count') != 3*expected_future or
                            not isinstance(descriptor, dict) or
                            descriptor.get('prediction_target') != target or
                            not isinstance(configuration, str) or
                            re.fullmatch('[0-9a-f]{64}', configuration) is None or
                            bounded.get('error_operator_configuration') != configuration):
                        raise ValueError('whole-period bound or error operator differs from target')
                    alternatives[law] = dict(binding_sha256=binding,
                                             prediction_target=target,
                                             operator_configuration=configuration,
                                             interval=bounded)
                interval = union_simultaneous_intervals(
                    alternatives,
                    minimum_simultaneous_coverage=minimum_simultaneous_coverage)
            capture('union-'+artifact, interval)
            unions[target] = interval
        return withheld_truth()

    result = paired_run(laws, fit_candidate=fit, save=capture,
                        withheld_truth=open_truth)
    return dict(result, simultaneous_law_family=unions)
