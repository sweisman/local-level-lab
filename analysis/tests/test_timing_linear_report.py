# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib


def report():
    return dict(completed_diagnoses=4,accepted_task_envelopes=0,charged_linear_solves=4,
        failures=[dict(reason='one explicit software result and continued scientific abstention required') for _ in range(4)],
        rows=[dict(identity=str(i),original_fit_converged=i<2,anchor_cost=1.,
                   predicted_cost=1. if i<2 else 1.01,nonworsening=i<2,linear_success=True) for i in range(4)])


def test_linear_report_distinguishes_saved_calculations_from_rejected_envelopes():
    text=importlib.import_module('lll.timing_linear_report').render(report())
    assert '4 saved linear calculations' in text
    assert '0/4 task envelopes' in text and 'schema' in text
    assert 'No calculation was rerun' in text


def test_linear_report_does_not_relabel_failed_fits_or_claim_native_replay():
    text=importlib.import_module('lll.timing_linear_report').render(report())
    assert 'unchanged' in text and 'different anchor' in text
    assert 'calibration threshold' in text


def test_partial_linear_report_does_not_claim_the_complete_comparison():
    r=report();r['rows']=[];r['completed_diagnoses']=0
    text=importlib.import_module('lll.timing_linear_report').render(r)
    assert 'comparison is incomplete' in text
    assert 'two failed calibration cases return higher' not in text


def test_corrected_linear_report_describes_four_accepted_nonworsening_results():
    r=report();r['accepted_task_envelopes']=4
    for row in r['rows']:row.update(nonworsening=True,predicted_cost=row['anchor_cost'])
    text=importlib.import_module('lll.timing_linear_report').render(r)
    assert 'All four proposals' in text and '4/4 task envelopes' in text
    assert 'schema error omitted' not in text and 'not a native replay' in text
