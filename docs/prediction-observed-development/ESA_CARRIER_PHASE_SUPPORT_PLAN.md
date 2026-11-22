# Check carrier-phase continuity on the opened ESA flight

Read the hash-verified AIR1 excerpt for recording 187. Check every one
of its 1,040 adjacent half-second pairs. Use GPS L1 C/A carrier phase
with its matching Doppler, and a common L2 carrier code. When both
endpoints carry L2W, use it. Otherwise use L2X only when both endpoints
carry that code. Keep each satellite's rejection reason.

Reject missing fields and a nonzero loss-of-lock flag at either endpoint.
Require the L1 phase change plus the mean Doppler integrated over the
half-second interval to be within 0.35 cycles. Require the difference
between L1 and L2 phase changes in metres to be within 0.075 m. The latter
removes the shared geometric range change. The first check helps catch
L1 jumps and the second helps catch isolated L2 jumps. These are working
continuity screens with generated checks, rather than a guarantee that
all ambiguity jumps, multipath or ionospheric residuals are absent.
[RINEX 3.04, phase and loss-of-lock fields](https://files.igs.org/pub/data/format/rinex304.pdf)

Report how many consecutive pairs retain at least five satellites.
Five is a necessary support check for a later position-change fit with
three displacement components and a common receiver clock change.
Coverage alone leaves geometric conditioning and absolute receiver
accuracy open. Allow one read of the sealed excerpt, one continuity
pass, zero position solves and zero inertial fits. No reserved flight
group is part of this preflight.
