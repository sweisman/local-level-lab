# Finite numerical qualification plan

Source, test and dependency hashes are frozen before execution. The solver is a
separate module; existing solvers and active research freezes remain unchanged.

The matrix includes:

- Forty analytic checks: ten controls under four fixed starts, at most 200 residual/
  tangent evaluations each. Controls cover interior and boundary optima, redundant
  parameters, scaling, nonlinear gain/offset trade-offs, curved valleys and a
  27-parameter problem with a known objective and predicted observations.
- Six raw-increment motion controls with independently calculated receiver positions,
  interior/near-boundary/exact-boundary truths and two starts, at most forty
  evaluations each. These use the previously qualified wider-arithmetic kernel.
- One six-evaluation nonstationary control, which must remain unfinished.
- One forty-evaluation control checking that a failed fresh physical gate cannot be
  bypassed by damping.

There are **48 test executions and at most 8,286 fitting evaluations**, zero
observed-data starts, one test batch, no retries, two numerical threads, and a
ten-minute batch timeout. Reusing a fixture does not rerun its earlier frozen study.
Each run must retain feasible parameters, counted evaluations, the known objective
and observations, and the unchanged stopping gates. Parameter agreement is required
only for identifiable control cases. A correct abstention is required for the two
negative controls. Every test must pass before qualification is declared.

The waiter reads only completion records and locks until the active two-stage
sequence finishes. It then holds those locks while the two-thread test batch runs.
Changed sources or environment block execution. A charged interruption stays failed.
Reports preserve test failures and source/environment hashes; they do not relabel
archival outcomes.

## Subsequent matched archival trial

If qualification passes, the next trial will use the same three preselected target
model/case identities as the completed budget continuation. Start from its frozen
primary endpoints, give each a predetermined perturbed repeat, and rerun the two
completed controls. Reuse the fifteen passing companion primaries with their hashes.
The proposed separate allowance is eight starts / 1,296 native sweeps: six primary/
repeat starts at 200 fitting evaluations, two controls at forty, plus two diagnostics
per start. This qualification worker performs no archival trial. That trial needs
its own prepared inputs, source freeze and durable launcher before execution.
