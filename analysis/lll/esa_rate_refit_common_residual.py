# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decompose sealed ESA forecast errors into common and rate-method parts."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_rate_refit_report import IDENTITIES, PARENT, STUDY
from .esa_rate_refit_study import LAWS, METHODS


def decompose(routes, receiver, *, training_epochs, block_epochs=100):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors

    receiver = np.asarray(receiver, dtype=float)
    n = len(receiver)
    if (set(routes) != set(IDENTITIES) or receiver.ndim != 2 or
            receiver.shape != (n, 3) or not np.all(np.isfinite(receiver)) or
            type(training_epochs) is not int or type(block_epochs) is not int or
            not 0 < training_epochs < n or block_epochs < 1 or
            training_epochs % block_epochs or (n-training_epochs) % block_epochs):
        raise ValueError('matched six routes and fixed complete receiver blocks required')
    errors = {}
    for identity in IDENTITIES:
        route = np.asarray(routes[identity], dtype=float)
        if route.shape != receiver.shape or not np.all(np.isfinite(route)):
            raise ValueError('matched six finite forecast routes required')
        errors[identity] = receiver_errors(route, receiver)

    def metrics(common, departures):
        horizontal = np.linalg.norm(common[:, :2], axis=1)
        spread = np.linalg.norm(departures[:, :, :2], axis=2)
        return dict(epochs=len(common),
                    shared_horizontal_rms_m=float(np.sqrt(np.mean(horizontal**2))),
                    shared_vertical_rms_m=float(np.sqrt(np.mean(common[:, 2]**2))),
                    maximum_shared_horizontal_m=float(np.max(horizontal)),
                    maximum_absolute_shared_up_m=float(np.max(np.abs(common[:, 2]))),
                    method_horizontal_spread_rms_m=float(np.sqrt(np.mean(spread**2))),
                    method_vertical_spread_rms_m=float(np.sqrt(np.mean(departures[:, :, 2]**2))),
                    maximum_method_horizontal_spread_m=float(np.max(spread)),
                    maximum_absolute_method_up_spread_m=float(np.max(np.abs(departures[:, :, 2]))))

    output = {}
    for law in LAWS:
        stacked = np.stack([errors[f'{method}-{law}'] for method in METHODS])
        common = stacked.mean(axis=0)
        departures = stacked-common[None, :, :]
        def section(first, last):
            return metrics(common[first:last], departures[:, first:last, :])
        blocks = [dict(start_epoch=start, end_epoch_exclusive=start+block_epochs,
                       part='training' if start < training_epochs else 'prediction',
                       **section(start, start+block_epochs))
                  for start in range(0, n, block_epochs)]
        output[law] = dict(training=section(0, training_epochs),
                           prediction=section(training_epochs, n),
                           blocks=blocks)
    return output


def build(root):
    import numpy as np
    from .esa_rate_refit_report import build as verified_refit
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    prior = verified_refit(root)
    study = ClosedStudy(root, STUDY)
    parent = ClosedStudy(root, PARENT)
    try:
        if (study.completion['manifest_sha256'] != prior['manifest_sha256'] or
                study.completion['summary_sha256'] != prior['summary_sha256'] or
                parent.completion['manifest_sha256'] != prior['parent_manifest_sha256'] or
                parent.manifest['inputs']['scoring']['sha256'] != prior['scoring_sha256']):
            raise ValueError('sealed refit or receiver source changed')
        routes = {identity: study.artifact(identity, 'forecast.json')['coordinates']
                  for identity in IDENTITIES}
        rows = json.loads(gzip.decompress(parent.input('scoring', raw=True)))
        if len(rows) != 1200:
            raise ValueError('exact saved ESA receiver support required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
                                math.radians(row['longitude_deg']),
                                row['height_m']] for row in rows], dtype=float)
        result = decompose(routes, receiver, training_epochs=800, block_epochs=100)
        return dict(study=STUDY,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    parent_manifest_sha256=parent.completion['manifest_sha256'],
                    scoring_sha256=prior['scoring_sha256'],
                    refit_report_source_sha256=prior['report_source_sha256'],
                    diagnostic_source_sha256=hashlib.sha256(
                        (root/'analysis/lll/esa_rate_refit_common_residual.py').read_bytes()
                    ).hexdigest(), training_epochs=800, prediction_epochs=400,
                    block_epochs=100, laws=result, refits=0, native_calls=0,
                    protected_reads=0, preferred_sampling_method=None,
                    confidence_calibrated=False, scientific_decision='abstain')
    finally:
        parent.close()
        study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({law: {part: result['laws'][law][part]
                            for part in ('training', 'prediction')}
                      for law in LAWS}, sort_keys=True))


if __name__ == '__main__':
    main()
