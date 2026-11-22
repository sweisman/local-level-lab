# The receiver term cannot replace part of the existing forecast covariance

The estimated `air1` receiver covariance exceeded the existing forecast
covariance in at least one direction in every ESA development window.
Only **18.7–25.8%** of the estimated receiver covariance could be removed
before the remainder became invalid. Both input conventions gave the
same range.

All eight tasks completed and reproduced the existing scores and
covariance determinants. The compatibility check failed in all 16
window-by-input combinations, so no alternate receiver was scored
under the proposed replacement. The calculation used the donor
estimates without shrinking them to fit. It used 32 charged calls,
six software checks and zero new aircraft fits.

The estimated receiver terms can predict relative GPS differences and
still be incompatible with the absolute forecast covariance. A new
combined model would need to estimate the common forecast term and the
receiver terms together. Shared GPS error remains unmeasured. The seven
reserved flight groups stay closed.

[Frozen plan](ESA_RECEIVER_COVARIANCE_COMPATIBILITY_PLAN.md) ·
[Verified evidence](esa-receiver-covariance-compatibility-evidence/README.md)
