# SPDX-License-Identifier: AGPL-3.0-or-later
"""Save matched candidate-law fits before opening withheld observations."""
from .prediction_training_law_comparison import compare


REQUIRED = frozenset(('fit.json', 'forecast.json',
                      'forecast-error-diagnostic.json',
                      'receiver-error-diagnostic.json'))


def run(laws, *, fit_candidate, save, withheld_truth):
    if (not isinstance(laws, tuple) or len(laws) != 2 or
            any(not isinstance(law, str) or not law for law in laws) or
            laws[0] == laws[1] or
            not all(callable(action) for action in
                    (fit_candidate, save, withheld_truth))):
        raise ValueError('two distinct fixed laws and explicit callbacks required')
    candidates = {}
    for law in laws:
        written = set()

        def save_candidate(name, value):
            if not isinstance(name, str) or not name or '/' in name or name in written:
                raise ValueError('unique saved candidate artifact name required')
            save(law + '/' + name, value)
            written.add(name)

        candidates[law] = fit_candidate(law, save_candidate)
        if not REQUIRED <= written:
            raise ValueError('both saved forecasts and diagnostics required before withheld truth')
    comparison = compare({law:{key:record[key] for key in
                               ('fit', 'binding', 'diagnostic')}
                          for law, record in candidates.items()})
    save('training-law-comparison.json', comparison)
    return dict(candidates=candidates, comparison=comparison,
                withheld_truth=withheld_truth())
