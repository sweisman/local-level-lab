# SPDX-License-Identifier: AGPL-3.0-or-later
"""Save a matched two-law affine interval union before later truth is opened.

This is a software bridge. The supplied law family, calibration box and
nonlinear aircraft approximation still require separate coverage validation.
"""
import math
import re

from lll.prediction_law_family import union_marginal_intervals
from lll.prediction_paired_law import run as paired_run
from lll.studies.artifacts import digest, encoded


TARGETS = dict(physical_position='bounded-physical.json',
               receiver_measurement='bounded-receiver.json')


def _binding_sha(candidates, laws):
    prefixes = []
    for law in laws:
        binding = candidates[law]['binding']
        prefix = dict(receiver=binding['training_receiver_sha256'],
                      imu={name:binding['training_prefix_sha256'][name]
                           for name in ('theta', 'dv', 'dt')},
                      training_epochs=binding['training_epochs'],
                      prediction_epochs=binding['prediction_epochs'])
        prefixes.append(prefix)
    if any(prefix != prefixes[0] for prefix in prefixes[1:]):
        raise ValueError('same earlier measurements required for interval union')
    return digest(encoded(prefixes[0]))


def _union_target(laws, candidates, saved, target, artifact, minimum_coverage):
    binding_sha = _binding_sha(candidates, laws)
    training_epochs = candidates[laws[0]]['binding']['training_epochs']
    expected_epochs = candidates[laws[0]]['binding']['prediction_epochs']
    alternatives = {}
    for law in laws:
        bounded = saved.get(law + '/' + artifact)
        if (not isinstance(bounded, dict) or
                bounded.get('prediction_target') != target or
                bounded.get('training_epochs') != training_epochs or
                bounded.get('prediction_epochs') != expected_epochs or
                bounded.get('coordinate_chart') != 'local_unwrapped_geodetic' or
                bounded.get('later_observations_used') is not False or
                bounded.get('nonlinear_aircraft_coverage_established') is not False or
                bounded.get('scientific_decision') != 'abstain'):
            raise ValueError('matched earlier-only bounded target required')
        diagnostic = candidates[law].get(
            'physical_diagnostic' if target == 'physical_position' else 'diagnostic')
        descriptor = diagnostic.get('error_operator') if isinstance(diagnostic, dict) else None
        configuration = descriptor.get('operator_configuration') if isinstance(descriptor, dict) else None
        if (descriptor is None or descriptor.get('prediction_target') != target or
                not isinstance(configuration, str) or
                re.fullmatch('[0-9a-f]{64}', configuration) is None or
                bounded.get('error_operator_configuration') != configuration):
            raise ValueError('bounded interval must match its own target error operator')
        alternatives[law] = dict(binding_sha256=binding_sha,
                                 prediction_target=target, interval=bounded)
    return union_marginal_intervals(
        alternatives, minimum_marginal_coverage=minimum_coverage)


def run(laws, *, fit_candidate, save, withheld_truth,
        minimum_marginal_coverage=.95):
    """Pair identical recorded prefixes, then save both unions before truth."""
    if (not all(callable(item) for item in (fit_candidate, save, withheld_truth)) or
            not isinstance(minimum_marginal_coverage, (int, float)) or
            not math.isfinite(minimum_marginal_coverage) or
            not 0 < minimum_marginal_coverage < 1):
        raise ValueError('fit, save, withheld callbacks and finite marginal target required')
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
            raise ValueError('matched training comparison must precede truth')
        for target, artifact in TARGETS.items():
            if comparison['status'] == 'numerically_unqualified':
                result = dict(supported=False, reason='candidate_fit_unqualified',
                              prediction_target=target, candidate_laws=list(laws),
                              binding_sha256=_binding_sha(candidates, laws),
                              selected_law=None, coverage_calibrated=False,
                              scientific_decision='abstain')
            else:
                result = _union_target(laws, candidates, saved, target,
                                       artifact, minimum_marginal_coverage)
            capture('union-' + artifact, result)
            unions[target] = result
        return withheld_truth()

    result = paired_run(laws, fit_candidate=fit, save=capture,
                        withheld_truth=open_truth)
    return dict(result, bounded_law_family=unions)
