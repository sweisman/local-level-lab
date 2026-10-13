# Saved-result diagnosis of the boundary-aware trial

Inspect the completed 24-start trial without reading original observations, making
native predictions or starting archival fits. Preserve its results and stopping rules.

1. Verify completion, manifest, summary, journals, saved tangents and epoch hashes.
2. Check saved costs and gradients against the saved residual/Jacobian arrays.
3. Separate stationary prediction-stability stalls from evaluation exhaustion.
4. Solve one bounded affine correction per saved tangent. Report its predicted cost
   change, residual change, dominant coordinates and remaining boundary slack.
5. Compare the three predetermined primary/repeat tracks at the same receiver epochs.
   Agreement alone cannot promote a failed fit.
6. Publish all 24 outcomes and identify the smallest useful next numerical test.

The work is bounded to 24 small affine systems and three saved-track comparisons.
There are zero original-file reads, native integrations and observed-data fit starts.
Use at most two numerical threads. These diagnostics cannot establish derivative
accuracy, a global optimum, physical adequacy or statistical significance.
