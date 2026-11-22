# Restore the strongly constrained residual after a rejected trial

The [direct residual change control](DIRECT_RESIDUAL_CHANGE_RESULT.md)
recovered the two curved-interior starts, while both curvature methods
still failed the two weak-direction starts. A large move along
a weak direction can bend the residual that constrains another
coordinate much more tightly.

Use the trial's measured tangent to identify singular directions at
least one thousandth as strong as its largest direction. A restoration
is eligible only when there are both retained and discarded directions.
Take one least-squares correction in the retained space. Shorten it
uniformly if needed to keep the combined trial inside the original
parameter box and the 0.5 normalized step radius. Preserve the weak
displacement. Evaluate the restored trial once. Require a true decrease
and the same 0.1 ratio against the unrepaired step's predicted
decrease. Keep both trial outcomes in the record.

Compare against the sealed direct-change run on the same eight
known cases and starts for each curvature method. Use the same 40
evaluation limit per start and require the unchanged fresh convergence
gate, objective tolerance and parameter tolerance. A method qualifies
only with eight passes. Use one worker, one numerical thread, 16
starts, at most 640 residual evaluations and a 60-second wall limit.
Interrupted work uses the existing finite recovery allowance.

No measured flight enters this control. A pass supports a separate
generated flight-scale test, with the cost of the restoration and
finite-difference tangent charged explicitly. It does not change the
observed solver or allow a retry of an aircraft fit.
