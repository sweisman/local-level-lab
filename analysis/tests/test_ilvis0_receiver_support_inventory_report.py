"""Saved-only public summary of the receiver support study."""

from lll.ilvis0_receiver_support_inventory_report import summarize


def test_summary_preserves_supported_widths_and_decoder_abstention():
    targets = [dict(selected_half_window_s=15.),
               dict(selected_half_window_s=5.),
               dict(selected_half_window_s=None)]
    segments = [dict(segment_id='a', filename='a.013',
                     disposition='screened', receiver_targets=3,
                     supported_targets=2,
                     support=dict(targets=targets)),
                dict(segment_id='b', filename='b.013',
                     disposition='abstain', reason='prior_receiver_decoder_failure',
                     receiver_targets=0, supported_targets=0)]
    rows, aggregate = summarize(segments)
    assert len(rows) == 2
    assert rows[0]['half_15_s'] == 1
    assert rows[0]['half_10_s'] == 0
    assert rows[0]['half_5_s'] == 1
    assert rows[0]['unsupported_targets'] == 1
    assert rows[1]['reason'] == 'prior_receiver_decoder_failure'
    assert aggregate['targets'] == 3
    assert aggregate['supported_targets'] == 2
    assert aggregate['decoder_abstentions'] == 1
