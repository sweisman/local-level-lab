# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two matched native fits with whole-period bounds for both targets."""


def calculate(spec, recipe, material, *, noise_kernel, kernel_factory,
              reserve, save, withheld_truth, check_continue):
    from .bounded_simultaneous_forecast_wrapper import evaluate as bound
    from .prediction_paired_native_core import calculate as core
    from .prediction_paired_simultaneous_family import run as pair

    calibration = recipe.get('calibration_alpha')
    simultaneous = recipe.get('simultaneous_alpha')
    if (not isinstance(calibration, (int, float)) or
            not isinstance(simultaneous, (int, float)) or
            not 0 < calibration < simultaneous <= .025):
        raise ValueError('two-target joint 95% whole-period allowance required')
    return core(spec, recipe, material, noise_kernel=noise_kernel,
                kernel_factory=kernel_factory, reserve=reserve, save=save,
                withheld_truth=withheld_truth, check_continue=check_continue,
                bound_evaluate=bound, pair_run=pair,
                bound_options=dict(calibration_alpha=calibration,
                                   simultaneous_alpha=simultaneous),
                pair_options=dict(minimum_simultaneous_coverage=1-simultaneous))
