# Fixed-point precision check on unfinished alternative fits

The generated matched-field study finished every task. Thirty-three
alternative fits failed their final numerical probe. Each fresh probe
increased training cost, despite a submillimetre position change. This
check asks how much of that increase remains when the same calculation
uses wider arithmetic and subtracts receiver coordinates before rounding.

Use all 33 affected fits. Reconstruct the proposed probe from each saved
normalized endpoint, residual and Jacobian using the original bounded
linear solve. Verify the predicted cost change and parameter step against
the sealed artifacts. Evaluate the exact same endpoint and probe with
binary64 and wider arithmetic. Require the binary64 replay to agree
with the original endpoint and probe costs. Use one common measurement
weighting and the original clock, bounds and removal case.

Each identity has four charged native training tangents. There are at
most 132 calls and 5,009,928 packet visits. Use two single-thread workers,
a 30-minute cooperative wall cap and qualified task recovery. There are
no new fit starts, solver retries or withheld receiver observations.
The original stopping labels and limits remain in force.

Report the cost and position change in both calculations, with the
original (10^{-8}) relative cost limit shown for comparison. If the
increase persists in the wider calculation, wider subtraction alone
does not explain it. If it disappears, test a separately frozen solver
qualification before using wider arithmetic in any observed comparison.
