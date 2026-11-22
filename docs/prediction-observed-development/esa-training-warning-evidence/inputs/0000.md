# Check whether earlier GPS residuals warn of later forecast failures

Use the same 12 windows and both inertial error laws from the
[raw accuracy audit](ESA_RAW_ACCURACY_RESULT.md). Use the selected fits
unchanged. Apply the existing four position-error limits to the recorded
raw training residuals, using the same local coordinate conversion as the
later score. Fix all warning flags before comparing with the saved later
outcomes. Report warnings followed by a later failure, failures without a
warning and warnings followed by a later pass. Also report the full four
checks by window and law. Preserve missing scores and all later failures.

Use only sealed earlier observations and archived fitted positions. The
evaluation opens no original files and runs no new navigation fits or
native calls. Use 12 task identities and 24 charged evaluations on one
thread with a 90-second cooperative limit. This is a retrospective warning
check on one development flight. Its limits are fixed from the earlier
study and do not qualify an eligibility gate for reserved flights.
