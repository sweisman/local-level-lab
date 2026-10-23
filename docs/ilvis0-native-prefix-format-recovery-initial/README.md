# Initial cached-report recovery: startup failure

All four workers stopped while loading the adapter. Its relative imports were
incompatible with the frozen worker's module loader. No task identity, native
calculation, cached batch or optimizer start was charged.

This freeze is closed and preserved. A separate version corrects the imports and
adds a regression using the actual loader name. It retains the same numerical
library, physical assumptions and finite limits.

[Current recovery](../ilvis0-native-prefix-format-recovery/README.md).
