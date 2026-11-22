# Value-only trial checks would save work on one of 16 ESA fit pairs

In the [sealed ESA solver comparison](OBSERVED_DISPATCH_FRESH_RESULT.md),
only one pair contained evaluations used solely for rejected steps. Across
all 32 fits, checking proposed steps without derivatives could remove
**3.1%** of wide-precision derivative calls and **8.2%** of selective-precision
calls. The saving is concentrated in the first start for the specified-field
globe with the short receiver-error description and zero upstream removal.

| Method | Saved fit derivative calls | Avoidable derivative calls | Extra value-only calls | Break-even value-only cost |
| --- | ---: | ---: | ---: | ---: |
| Wide precision | 288 | 9 | 240 | 3.75% of a wide derivative call |
| Selective precision | 304 | 25 | 256 | 9.77% of a selective derivative call |

The break-even cost divides the derivative calls saved by the additional
value-only calls. It assumes equal cost per call within a method and leaves
other fit work unchanged. These percentages are planning estimates. The
audit measured no run time for the alternative and does not qualify it for
this ESA window. On the one high-rejection pair, the possible saving was
much larger. The estimated derivative count fell from 16 to 7 using wide
precision and from 32 to 7 using selective precision.

The [fixed audit](OBSERVED_TRIAL_WORK_PLAN.md) counts distinct evaluations
and keeps every initial, accepted and fresh stopping calculation. It
verified all 32 saved fit artifacts against the original 624 native calls,
including 32 forecast calls outside the table. The audit charged 32 fit
reads and made zero new native calls. No later receiver positions or reserved
flights were opened.

[Verified per-fit work ledger](observed-trial-work-result.json) ·
[Source and execution receipts](observed-trial-work-evidence/README.md) ·
[Verified reproduction bundle](observed-trial-work-evidence/bundle.zip)
