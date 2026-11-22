# Satellite range coverage in the 21 pilot candidates

Check all 21 sources in the saved pilot metadata inventory. Use the
archived primary-receiver byte streams and selected time bounds. Keep the
original checksums, captured boundary bytes and hashes. Reassemble only
complete RT17 or RT27 measurement records. Preserve framing, unsupported
layout, missing measurement and duplicate epoch failures. Use no fused
navigation, inertial measurements, fitted model results or ESA data.

At every original enhanced-position epoch in each selected stretch, look
for a corresponding satellite record to the recorded millisecond.
Use the existing L1 and dual-frequency range checks and recorded orbit and
clock messages. Check five-degree elevation and full position/clock rank
at the onboard receiver's position. The purpose is to inventory input
support. Position solves, downloads and Earth-model evaluations are zero.
Take no missing measurement from an adjacent epoch.

The ceiling is 21 stream tasks, at most 64 MB of receiver data, 200,000
checked binary packets, 60,000 measurement records and 20,000 original
selected epochs per task. Use two single-thread workers under a 600-second
cooperative allowance. Charge the stream task before reading its inputs.
Retain every closed task including unsupported files. Use the shared
study engine to bind each frozen byte stream, bounds and numerical
environment, and once the run closes verify its result hashes before
choosing a separate receiver-position comparison.
