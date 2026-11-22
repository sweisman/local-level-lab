# Generated changing-drift pilot

## Question

Can one fixed, time-correlated position-error law describe forecast errors
produced by the independent generated IMU and receiver streams? This is a
**development stress check**, not an ESA or NASA aircraft result. Failure
would rule out this fixed candidate as a complete forecast law even when the
initial physical state is supplied exactly.

## Frozen cases and split

Use eight distinct seeds, `2026111600` through `2026111607`. Even-numbered
seeds include the generator's physical vibration; odd-numbered seeds omit
it. Each case lasts 120 seconds at 100 IMU samples per second. Receiver
reports are at integer seconds. Condition on reports 0–60 only; score reports
61–120 afterward. Keep the generator's white gyro/force errors, changing
biases, shared gyro/force error and receiver white/random-walk errors. Do not
fit any Earth model, choose a seed after scoring, or inspect an aircraft file.

Use the candidate law's fixed scales below, derived from the generator's
declared process amplitudes before seeing these draws:

| Quantity | Fixed value |
|---|---:|
| White acceleration intensity | `(0.01² + 0.02²) / 100 = 5e-6` |
| Changing-acceleration intensity | `0.0003² + 9.80665² × (0.0001² + 0.0002²) / 100` |
| Receiver random-walk intensity | `0.01² = 0.0001` |
| Receiver white standard deviation | `0.03 m` per axis |
| Initial receiver-offset standard deviation | `0.01 m` per axis |
| Initial inertial position/velocity/acceleration uncertainty | zero (truth supplied) |

The gyro-bias random walk and motion/processing mismatch are **not fully
represented** by this law. That is an intentional adversary; the pilot must
record any forecast miscoverage rather than silently enlarge a parameter
after seeing it.

For each draw, save training residuals, earlier-conditioned forecast mean and
scale, later errors, the largest absolute standardized later error, marginal
95% fractions and whole-period 95% containment. Count each seed once, not
each receiver epoch as an independent trial. Numerical completeness is the
only technical pass criterion; no coverage or scientific pass is declared
from eight draws.

Freeze the code, policy, Python/NumPy/SciPy environment and eight task IDs
before launch. Each task is limited to 12,000 generated IMU packets, 121
receiver reports, zero native calls, zero Earth-model fits and one start.
Use one numerical worker/thread and a 10-minute original wall allowance.
Qualify and freeze task-level recovery before launch. Preserve completed
failures; only unfinished technical work may continue under a separately
charged finite allowance. The seven reserved ESA flight groups remain closed.
