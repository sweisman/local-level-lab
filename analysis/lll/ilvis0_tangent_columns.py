# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare fixed-point tangent columns in local position units, without fitting."""


def compare(times, wide_coordinates, fast_coordinates, wide_jacobian,
            fast_jacobian, active_columns, *, boundaries):
    """Report NEU slope differences per normalized parameter and query epoch."""
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors
    from .models import radii

    t = np.asarray(times, float)
    coordinates = [np.asarray(value, float)
                   for value in (wide_coordinates, fast_coordinates)]
    jacobians = [np.asarray(value, float)
                 for value in (wide_jacobian, fast_jacobian)]
    if (t.ndim != 1 or not len(t) or not np.all(np.isfinite(t)) or
            np.any(np.diff(t) <= 0) or
            not isinstance(active_columns, list) or not active_columns or
            len(set(active_columns)) != len(active_columns) or
            any(not isinstance(name, str) or not name for name in active_columns) or
            any(value.shape != (len(t), 3) or not np.all(np.isfinite(value))
                for value in coordinates) or
            any(value.shape != (3*len(t), len(active_columns)) or
                not np.all(np.isfinite(value)) for value in jacobians) or
            not isinstance(boundaries, tuple) or len(boundaries) != 2 or
            any(type(value) is not int or value < 0 for value in boundaries)):
        raise ValueError('finite aligned times, values, boundaries and active columns required')
    position_difference = receiver_errors(coordinates[1], coordinates[0])
    rm, rn = radii(coordinates[0][:, 0])
    scale = np.column_stack((rm + coordinates[0][:, 2],
                             (rn + coordinates[0][:, 2]) *
                             np.cos(coordinates[0][:, 0]),
                             np.ones(len(t))))
    if np.any(scale <= 0):
        raise ValueError('positive local position metric required')
    slopes = [(jac.reshape(len(t), 3, len(active_columns)) * scale[:, :, None])
              for jac in jacobians]
    delta = slopes[1] - slopes[0]
    magnitude = np.linalg.norm(delta, axis=1)
    columns = []
    for index, name in enumerate(active_columns):
        epoch = int(np.argmax(magnitude[:, index]))
        columns.append(dict(
            name=name,
            maximum_difference_m_per_normalized_unit=float(magnitude[epoch, index]),
            maximum_epoch=epoch,
            maximum_time_s=float(t[epoch]),
            maximum_neu_difference_m_per_normalized_unit=delta[epoch, :, index].tolist(),
            final_difference_m_per_normalized_unit=float(magnitude[-1, index])))
    largest = max(columns, key=lambda row:
                  row['maximum_difference_m_per_normalized_unit'])
    return dict(version='same-point-tangent-columns-v1',
                values_bitwise_identical=coordinates[0].tobytes() ==
                                         coordinates[1].tobytes(),
                boundary_counts_identical=boundaries[0] == boundaries[1],
                maximum_position_difference_m=float(np.max(
                    np.linalg.norm(position_difference, axis=1))),
                active_columns=len(columns), columns=columns, largest_column=largest,
                new_fits=0, scientific_decision='abstain')
