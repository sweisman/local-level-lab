# Score complete ESA forecasts with their time correlation

Use the sealed full and reduced changing-drift ranges for the same 24 starts
on ESA development recording 187. Retain the four failed starts and the
original training-selected starts in each matched setting. Keep both receiver
weighting cases, the fixed earlier coordinate chart, and the first 60 and all
120 later reports. Bind the earlier range seals before opening later positions.

Use each law's conditional covariance to whiten departures from its already
saved forecast center. The calculation uses the later covariance given the
earlier reports, including correlations across reports and axes. Carry the
same filter state across the full later block. Report squared standardized
error, its root mean square and the Gaussian score including the covariance
determinant. Keep point accuracy and coordinate-range containment separate.
In complete settings compare globe and disc before comparing the two globe
variants. No score cutoff or scientific decision is licensed by this check.

Use the same method on the 256 sealed generated histories, with their original
61/60 split. Verify the earlier-only reduced range against its saved hash.
Report the wholly paired differences and whole-path error scale for context.
The histories were generated under different assumptions and have a shorter
training interval. Their scores do not establish an aircraft cutoff.

Freeze all input receipts, source and environment. Allow four aircraft and
two generated covariance operators, up to 80 aircraft and 512 generated
whole-path evaluations, one thread, and zero new fits, simulations or reserved
group reads. Verify the conditional score independently against a dense known
covariance before scoring the saved histories.
