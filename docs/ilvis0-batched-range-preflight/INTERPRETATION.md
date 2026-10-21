# The runtime obstacle is resolved on this screen

All **six full-history source comparisons complete and preserve their reference
maps**. The study took 134.46 seconds; each bound finished within its original
120-second limit. The previous implementation completed only two cases before
four globe cases reached that limit.

Compared with the best compatible saved bounds, the new height allowances are
**17–37% smaller**. North and east allowances are wider in every case. The
retained comparison therefore keeps the old horizontal bounds and the new
height bounds. It never substitutes a wider allowance for a tighter valid one.

This screen does not recompute complete prediction regions. The last complete
width comparison remains four of six groups, and withheld aircraft fitting is
still waiting for a useful complete error range.

The next task is to retain the source's calibration derivatives when bounding
its nonlinear remainder. The current value-interval calculation loses that
linear information and overstates horizontal uncertainty. A replacement needs
its own mathematical and numerical qualification, including reference rounding
and packet-clock boundaries; acceptance limits stay fixed.

[Six-case results](README.md) · [Frozen scope](PLAN.md) ·
[Technical next step](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
