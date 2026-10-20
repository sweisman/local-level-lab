# Short equivalence passes; long pose precision needs explanation

The finite study ended after **45 of 48 identities**. Forty-four passed, one
failed its declared acceptance, and three were not started. No allowance will
be reused and the study cannot restart.

All 24 value/tangent comparisons and 18 independent short constant-pose controls
pass. Chunk layouts and a serialized restart preserve the calculations bit for
bit, including all 27 derivative columns and left-interval timing at a boundary.

The first two scaling cases pass. In the third, 120,000 packets represent a
400-second constant-pose record. Its value prediction differs from the exact
pose by **3.48 micrometres**, exceeding the frozen 1-micrometre limit. Its traced
working allocation is 0.339 MiB and the native state remains 560 bytes. This is
a generated numerical discrepancy, not an observed aircraft error.

The long scaling cases did not compare against the unchanged whole-array kernel.
The saved result alone therefore cannot attribute this discrepancy to chunking
or to arithmetic accumulated by the existing mechanization. The next separate
qualification must make that comparison and use an exactly representable
constant-pose control. It must retain the original tolerance and failure, not
silently widen the threshold or claim complete long-record qualification.

The original 53 model comparisons and their findings are unchanged. New archive
prediction fits remain blocked by the recording-scale uncertainty and adequacy
requirements.

[Saved results](README.md) · [Frozen method](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
