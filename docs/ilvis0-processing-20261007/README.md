# First receiver-stream audit

This completed first audit preserved the settings, clock and receiver evidence for six
existing recordings. All original hashes and outer framing checks reproduced. It found
complete Trimble survey-record envelopes in every file and GSOF receiver messages.

The strict receiver parser stopped in four streams at byte `0x15`. Subsequent examination
identified this as Trimble's documented single-byte NAK command response. It is not proof
of source corruption, and the first parser did not silently skip it. The first audit's
10,331 assembled survey records therefore describe complete accepted prefixes, not the
full six-file population.

The [separately frozen revision](../ilvis0-processing-v2-20261007/README.md) implements
documented ACK/NAK handling and decodes receiver-reported position uncertainty. This first
manifest, source snapshot, completion and report remain preserved. Do not resume it with
revised live sources. No Earth fit, eligibility change or original deletion occurred.
