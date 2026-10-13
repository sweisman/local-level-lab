# Frozen recovery plan

This study completes numerical comparisons for the original 41 unresolved NASA
airborne stretches. The [preparation](../ilvis0-position-recovery-preparation-20261013/README.md)
fixes every primary and repeated-start identity from original stopping status and
UTC order. Costs and gyro values do not select intervals or repeat identities.

The actual-position qualification completed **24/24 passing fits**, all six controls
and all three repeated-start checks. Its 15 recovered primary fits and three repeats
are reused with hashes and their original provenance; they consume no new allowance.

## Fixed computation

- 115 new primary recovery starts, 38 predetermined repeated starts and six controls.
- **159 new starts**, no retries or replacements.
- At most **600 fitting sweeps and two diagnostic predictions per start**;
  **95,718 native sweeps** in total.
- One durable worker with **two total numerical threads**.
- Six fresh controls execute first. Original physical models, bounds, nominal 200 Hz
  integration clock, covariance and selected complete intervals remain unchanged.
- Primary starts use the original first-pass endpoints; repeats use those endpoints
  with the same fixed 0.01 normalized-coordinate perturbation. Controls use the
  qualified trial endpoints. No best-cost endpoint selection is permitted.

The matched first-pass ceiling estimate is **51–76 hours**. This is a computational
ceiling estimate, not a promised runtime. The completed qualification used only
393 sweeps; difficult original endpoints can require much more.

## Numerical gates and findings

The qualified solver preserves the 1e-4 projected-gradient limit and 1e-8 relative
objective-change limit. A fresh full-model stability probe must move predicted
positions by at most 1 mm RMS per axis and 1 cm at any receiver epoch. Those are
numerical tolerances, not instrument-accuracy specifications.

Each stretch needs all six primary fits, a passing predetermined repeat, and passing
fresh controls before its recovery comparison is reported as complete. Repeat
agreement requires relative cost difference at most 1e-6 and axis RMS track change
at most 1 cm. Controls must reproduce their qualified endpoint objective within
1e-6 and tracks within 1 cm RMS per axis. A control failure withholds the recovery
comparisons. Other failures affect their own stretch and remain in the ledger.

Report globe/flat/unknown first. Report the specified background-field comparison
only after consistent globe preference across the two processing cases. Preserve
original first-pass findings separately. Numerical preferences are not calibrated
detections, global-optimum proofs or independent-flight counts.

## Freeze and recovery

Before launch, freeze sources, test receipt, selected original hashes, sealed trial
results, immutable schedule, native build and numerical environment. Source snapshots
are preserved. Charge starts and sweeps before execution; use exclusive locks,
atomic hashed fit results and append-only journals. An interrupted charged identity
is recorded as unfinished, with no retry. Unstarted identities may continue only
under the unchanged freeze. Completed studies cannot resume.

Publication after completion checks journal and artifact hashes and performs no fits.
It records all 41 recovery outcomes, reused subset results, controls and the combined
53-stretch tally. Original evidence and retained recordings remain intact.
