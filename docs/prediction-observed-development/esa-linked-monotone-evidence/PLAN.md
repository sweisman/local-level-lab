# Tighten the linked calibration cuts using derivative signs

The [linked graph cuts](ESA_LINKED_GRAPH_CUTS_RESULT.md) only rarely
excluded a relaxed calibration point. Each cut was bounded over a
whole physical box. Test whether excluding impossible combinations in
that calculation makes the cuts more useful.

Keep all eleven surviving ranges, their original losses, all 60
columns, earlier constraints and verified witnesses. Recheck each
saved graph direction. If its interval derivative is strictly
positive throughout the current box, the maximum lies on the upper
face for that coordinate. If it is strictly negative, use the lower
face. Move all such coordinates to their maximizing endpoints for
the purpose of that single upper bound. Repeat once, using the new
interval derivatives. Bound the remaining expression by the tighter
of its outward interval evaluation and the centred mean-value bound.
Add the original numerical allowance and retain the earlier cut if
it is stronger. This does not shrink the allowed physical calibration
region or remove a fitted column.

Test each tightened cut against its original proposed point and every
saved witness. Keep all earlier accepted constraints. Add a rechecked
cut if it excludes the original proposal, then obtain one new linear
proposal per range. Verify its bound with the original exact dual
certificate. Preserve the previous bound when a new certificate is
missing or weaker. Report the combined bound against the 25.41-unit
forecast separation. The independent uncertainty and complete nonlinear
integration checks remain open.

Freeze the same archived proposals and all original input and source
hashes. Allow three interval evaluations plus one point evaluation per
saved graph cut and one linear proposal per box, on two one-thread
workers. Use a 360-second cooperative wall allowance with a separate
360-second recovery allowance and one additional attempt per
interrupted task. Use no new trajectory integrations, fits or reserved
recordings. Retain checked cuts, charges and the full cover.
