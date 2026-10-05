# Codex preferences for Scott Weisman

## Who you're working with

The user is **Scott Weisman** — not Stephen, not Steven. GitHub `sweisman`,
email sweisman@gmail.com (a handle; do not infer a first name from it).
Always use "Scott" in copyrights, licenses, attribution lines, signed
correspondence, and anything else user-facing.

## Token economy

Scott works against tight token / plan-session budgets. Wasted tokens cost real work.

- Verify the cheapest sufficient way; don't run a heavy variant when a lightweight check proves the point.
- Don't re-read a file just edited; trust successful edits.
- Keep replies tight and lead with the result.
- Before expensive actions (large builds/renders, full re-derivations, multi-agent fan-out), name the cost and ask.
- One careful pass beats iterative polishing that wasn't requested.

## Workspace privacy

Leave unfamiliar paths outside the documented project corpus alone entirely.
Use README tables, manifests, and project instructions to identify that corpus.
Do not scan or enumerate unfamiliar paths, add them to git or `.gitignore`,
document them, flag them as anomalies, or ask what to do with them.
If a directory listing happens to surface them, do not comment.

## Git operations

Do not initiate any git operations without explicit consent. This includes
adding, committing, pushing, stashing, resetting, checking out, restoring,
rebasing, tagging, creating/deleting branches, and creating PRs or issues.
If a git operation is the next step, ask first (for example, "Want me to commit and push?").
Finishing a feature is not permission to commit it.
When Scott explicitly requests an operation, proceed without another confirmation
for that operation only.

## Commit granularity

Bundle related work into one commit per logical unit, across files and sessions.
Use the final coherent state and one message describing the whole.
Only split commits when Scott requests granular commits.
If many commits were made without being asked, surface what's pending and ask
how to consolidate instead of pushing them separately.

## Shell commands

Run each step as its own shell invocation. Avoid compound expressions, chains,
pipes for trimming output, and heredoc appends when a simple command suffices.
Use tool output limits or scripts that print less.

## Development environments

- Always use `~/venv/bin/python` and its pip for Python work and tests; do not use system Python or create another environment.
- Always use the installed JDK under `~/.local` for Java/Gradle work (currently `~/.local/jdk21`), with `JAVA_HOME` set accordingly; do not use the system JDK or download another.
