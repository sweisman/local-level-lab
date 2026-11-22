# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decompose the sealed ESA difference by time and innovation direction."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path


SOURCE_SHA = '1bec76a051028709ff4a9bc658c88b1b37b84d36dab799ce709c32b4e3d9a6c6'
EARLY_SCORE_SHA = '2c25c3c2a8721e89bf2d14b030f7dd12f6c632198f2668161cd982ddea9c1e14'
LATE_SCORE_SHA = '2836734250eee33d06c216fdb5770acbb564c5c4d84aac7fe5e1da1cbe857794'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_INNOVATION_TRANSFER_PLAN.md'
FREEZE = FOLDER+'esa-innovation-transfer-freeze.json'
EARLY = FOLDER+'esa-innovation-transfer-earlier.json'
RESULT = FOLDER+'esa-innovation-transfer-result.json'
BLOCKS, PEAKS = 4, 3


def window(study, cut, parent, prior):
    import numpy as np
    from .esa_changing_drift_transfer import _coordinates
    from .esa_native_rolling_transfer import matched_window, LAWS, LATER
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric
    from .innovations_snapshot import restore
    from .studies.artifacts import digest, encoded

    training = json.loads(gzip.decompress(study.input(f'{cut}-training', raw=True)))
    times = study.input(f'{cut}-forecast_times')
    origin = study.input(f'{cut}-saved-input-binding')['time_origin_s']
    held = matched_window(parent, training, times, origin=origin)
    if (len(held) != LATER or prior['cut'] != cut
            or digest(encoded(held)) != prior['held_receiver_sha256']):
        raise ValueError('exact original scored receiver window required')
    coords = _coordinates(held)
    metres = physical_metric(_coordinates(training[-1:]))[0]
    values = {}
    for law in LAWS:
        identity = f'{cut}-{law}'
        original = study.input(identity+'-conditional')
        receipt = study.artifact(identity, 'factor-replay.json')
        op = restore(study.artifact(identity, 'rolling-factors.npz', raw=True),
            expected_sha256=receipt['snapshot_sha256'],
            expected_configuration=original['full_operator_configuration'], maximum_bytes=64*1024**2)
        residual = coords-np.asarray(original['conditional_receiver_mean'])
        residual[:, 1] = longitude_residual(residual[:, 1])
        _, state = op.apply_block(np.zeros(cut*3), first_epoch=0)
        whitened, _ = op.apply_block(residual.ravel(), first_epoch=cut, state=state)
        if not np.isclose(whitened@whitened,
                prior['scores'][law]['squared_standardized_error'], rtol=1e-12, atol=1e-12):
            raise ValueError('innovation energy differs from originally sealed joint score')
        values[law] = (whitened.reshape(-1,3), residual*metres)
    return values


def run(root, action):
    import numpy as np
    from . import esa_native_rolling_transfer as prior
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .innovation_transfer import diagnose, estimates, score
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root, 'data/'+prior.ID)) as study:
        if (study.completion['manifest_sha256'] != SOURCE_SHA or study.completion['state'] != 'complete'
                or set(study.rows) != {task['identity'] for task in prior.tasks()}
                or any(not row['passed'] for row in study.rows.values())):
            raise ValueError('closed four-arm native rolling transfer required')
        own = Path(__file__).relative_to(root).as_posix()
        frozen = encoded(dict(source=study.completion, early_score_sha256=EARLY_SCORE_SHA,
            late_score_sha256=LATE_SCORE_SHA, environment=runtime_environment(),
            sources={name:digest((root/name).read_bytes()) for name in source_closure(
                root, (own, PLAN, 'analysis/tests/test_innovation_transfer.py'))},
            blocks=BLOCKS, peaks=PEAKS, training_cuts=[200,400], epochs_per_window=120,
            native_calls=0, optimizer_starts=0, protected_reads=0))
        if action == 'freeze':
            _write_equal(root/FREEZE, frozen)
            return dict(freeze_sha256=digest(frozen))
        if (root/FREEZE).read_bytes() != frozen:
            raise ValueError('frozen diagnostic changes are not allowed')
        if action == 'earlier':
            earlier = (root/prior.EARLIER_REPORT).read_bytes()
            if digest(earlier) != EARLY_SCORE_SHA:
                raise ValueError('sealed earlier score changed')
            receiver = json.loads(gzip.decompress(study.input('400-training', raw=True)))
            values = window(study, 200, receiver, json.loads(earlier))
            details = {}
            for law,(innovations, physical) in values.items():
                covariances = estimates(innovations)
                details[law] = dict(innovations=diagnose(innovations,blocks=BLOCKS,peaks=PEAKS),
                    physical_errors=diagnose(physical,blocks=BLOCKS,peaks=PEAKS),
                    covariance={k:v.tolist() for k,v in covariances.items()},
                    baseline_scores={k:score(innovations,v) for k,v in covariances.items()})
            report = dict(freeze_sha256=digest(frozen), details=details, later_opened=False)
            target = EARLY
        else:
            early_bytes = (root/EARLY).read_bytes()
            early = json.loads(early_bytes)
            late = (root/prior.REPORT).read_bytes()
            if (early['freeze_sha256'] != digest(frozen) or early['later_opened'] is not False
                    or digest(late) != LATE_SCORE_SHA):
                raise ValueError('earlier estimates must be sealed before comparison')
            with closing(ClosedStudy(root, prior.LATER_SOURCE, store=study.store)) as parent:
                if parent.completion['manifest_sha256'] != prior.LATER_SOURCE_SHA:
                    raise ValueError('later receiver source changed')
                receiver = json.loads(gzip.decompress(parent.input('training', raw=True)))
            values = window(study, 400, receiver, json.loads(late))
            details = {}
            for law,(innovations, physical) in values.items():
                entry = diagnose(innovations, blocks=BLOCKS, peaks=PEAKS)
                details[law] = dict(innovations=entry,
                    physical_errors=diagnose(physical,blocks=BLOCKS,peaks=PEAKS),
                    channel_transfer=(np.asarray(entry['channel_energy'])/
                                      np.asarray(early['details'][law]['innovations']['channel_energy'])).tolist(),
                    scores_on_earlier_scale={name:score(innovations,value)
                        for name,value in early['details'][law]['covariance'].items()})
            report = dict(freeze_sha256=digest(frozen), earlier_sha256=digest(early_bytes),
                          details=details, later_opened=True)
            target = RESULT
    payload = encoded(dict(**report, protected_reads=0, optimizer_starts=0,
                           scientific_decision='abstain'))
    _write_equal(root/target, payload)
    return dict(path=target, sha256=digest(payload))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze','earlier','compare'))
    print(json.dumps(run(Path.cwd(),parser.parse_args().action),sort_keys=True))
