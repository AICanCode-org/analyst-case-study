## What & why
<!-- One or two sentences. Link the issue: "Closes #12" -->

## Track(s)
- [ ] Python  - [ ] SQL  - [ ] R  - [ ] Shared (contract / dashboard / docs / CI)

## How I tested it
<!-- Commands you ran and their result, e.g. `make test` → 81 passed; `python3 scripts/parity.py ...` → IDENTICAL -->

## Numbers check
<!-- Did any number in answers.json change? If yes: which, why, and does parity with the golden file and the other
     tracks still hold? A changed number without a reason in the contract is a bug, not a result.
     "No numbers changed" is a fine answer. -->

## AI assistance
<!-- Which tool, what it drafted, what you changed or rejected, how you verified it. "None" is fine.
     Add a matching entry to AI_LOG.md. -->

## Self-review checklist
- [ ] CI is green
- [ ] Tests cover the new behaviour (including at least one bad-data case)
- [ ] Behaviour matches `contract/questions.md` (or the contract is updated in this PR, with a version bump)
- [ ] No secrets, `.env` files or row-level personal data in commits, logs or prompts
- [ ] Docs / CHANGELOG updated if a reader of the results would notice the change
- [ ] I can explain every line of this diff, and every number it changes, without the AI's help
