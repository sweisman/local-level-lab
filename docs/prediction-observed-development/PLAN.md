# Observed prediction development pilot

## Question

On the already selected ESA development recording, can the two supplied IMU
error laws be carried through a complete earlier-only fit and a forecast that
covers the withheld receiver period? This is a development check of prediction
and error assumptions. It is not an independent Earth-model test.

## Fixed input and first stage

Reuse prepared recording 187 and its saved 360,028 IMU packets and 1,200
receiver epochs. The first 800 receiver positions train the fit; the final
400 are opened only after both law-specific forecasts and both target interval
unions are saved. Use the same 239,867-packet training prefix, packet-header
clock, reported-short receiver policy, height-gravity anchor, no upstream
Earth-rate removal, specified-field globe candidate and start zero as the
completed technical preflight. The two supplied `increment` and `point` error
laws retain their generated-study numerical levels. They are assumptions,
not measured instrument limits.

The first stage has one task containing two matched fits, one per supplied
law. It records all numerical failures and boundary checks. It scores only
the withheld receiver observations. The archive contains no known true
physical aircraft path, so the physical-position interval is saved as a
diagnostic but receives no coverage score. A fit that predicts an implausible
height fails the fixed physical adequacy screen even if its horizontal error
is small.

## Finite allowance and recovery

The first-stage worker may start each law once, with at most 200 fit
evaluations per law. Its ceiling is 3,000,000 native calls, 80 billion
packet/query work units, eight hours of cooperative wall time and one
numerical thread. These conservative ceilings include the two full-history
error targets per law; the 27.5-minute no-fit preflight measured their
construction cost. At least 35 GiB must be free at launch. No automatic
scientific retry or increase to a running allowance is permitted.

Before launch, pass a short source-bound generated worker control, the
source/environment qualification and a finite task-level interruption
recovery test. The worker must be reboot-resumable without refitting a sealed
result. An interrupted unfinished task may continue only through a separately
charged, prospectively qualified continuation under unchanged scientific
inputs and methods.

## After this stage

Audit the sealed result without a refit. A technical pass permits a separately
frozen matrix covering all three physical candidates and the other already
designated development recordings. That later matrix must preserve shape-first
interpretation, both processing assumptions where declared, all failures and
the seven reserved ESA confirmation groups. The present first stage cannot
establish observed prediction coverage, scientific significance or a model
winner by itself.
