# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate earlier-GPS loss changes in the two saved ESA linkage examples."""

from contextlib import closing
from pathlib import Path


RESULT = 'docs/prediction-observed-development/esa-calibration-linkage-loss.json'
BLOCKS = (('clock_velocity', 27, 30), ('lever', 30, 33),
          ('clock_squared_acceleration', 33, 36), ('clock_times_acceleration', 36, 39),
          ('acceleration_remainder', 39, 42), ('force_transform', 42, 51))


def report(root):
    import numpy as np
    from .esa_calibration_witness import ID, MODELS
    from .esa_coupled_training_score import WITNESS_SHA
    from .esa_linked_training_support import projection_inputs
    from .esa_original_whitening import score_change
    from .studies.closed import ClosedStudy

    records = []
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if study.completion['manifest_sha256'] != WITNESS_SHA or not study.summary['passed']:
            raise ValueError('complete two-candidate witness archive required')

        def load(key):
            return study.input(key, raw=True)

        for model in MODELS:
            residual, _, design, _, _, _, _, _ = projection_inputs(load, model)
            rows = study.artifact(model, 'witnesses.json')['rows']
            independent, linked = (next(row for row in rows if row['source']=='independent_shared'
                                        and row['variant']==label and row['fraction']==1.)
                                   for label in ('independent_shared','linked_shared'))
            if (linked['physical_point'] != independent['physical_point']
                    or not independent['loss_passed'] or linked['loss_passed']):
                raise ValueError('same physical point with the two saved shared settings required')
            center = np.asarray(study.input(model+'-force')['center'])
            displacement = np.asarray(independent['physical_point'])-center
            before = design@np.r_[displacement, independent['shared']]
            difference = np.asarray(linked['shared'])-np.asarray(independent['shared'])
            changes = [design[:, start:stop]@difference[start-27:stop-27]
                       for _,start,stop in BLOCKS]
            together = np.sum(changes, axis=0)
            before_loss = score_change(residual, before)
            after_loss = score_change(residual, before+together)
            for value, row in ((before_loss, independent), (after_loss, linked)):
                if not np.isclose(value, row['loss_upper'], atol=5e-8, rtol=5e-11):
                    raise ValueError('block reconstruction differs from the archived earlier loss')
            direction = 2*(residual+before)+together
            signed = [float(direction@change) for change in changes]
            if not np.isclose(sum(signed), after_loss-before_loss, rtol=5e-13):
                raise ValueError('signed block contributions did not reproduce the total')
            records.append(dict(model=model, earlier_loss_with_independent_coefficients=before_loss,
                earlier_loss_with_linked_coefficients=after_loss, blocks=[
                    dict(block=name, whitened_change_norm=float(np.linalg.norm(change)),
                         signed_loss_change=effect,
                         loss_with_only_this_block_linked=score_change(residual, before+change))
                    for (name, _, _), change, effect in zip(BLOCKS, changes, signed, strict=True)]))
    return dict(manifest_sha256=WITNESS_SHA, rows=records, fit_starts=0, new_bound_calls=0,
                scientific_decision='abstain')


if __name__ == '__main__':
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded

    root = Path.cwd()
    raw = encoded(report(root))
    _write_equal(root/RESULT, raw)
    print(digest(raw))
