# Bind the corrected input bundle to the solver comparison

Use the cases, numerical checks, and work limits in the [fresh comparison
plan](OBSERVED_DISPATCH_FRESH_PLAN.md). Bind the [corrected preparation](OBSERVED_DISPATCH_INPUT_V2.md)
with manifest SHA-256
`00028f5c4826e26023b60c9480244acb696f68bc97cc13d550455366272447fb`.
It produced 359,729 inertial increments, including 239,718 in the
training prefix, and saved 800 earlier GPS positions and 400 later
times. The later positions stayed withheld. Keep the first preparation's
sealed failure alongside this result.

Use the qualification commands in the original plan with
`observed-dispatch-fresh-v2-tests.xml` as the test report filename. The
comparison continues to use both methods and both starts in each of
the eight settings. The qualification and staging steps run no fits.
