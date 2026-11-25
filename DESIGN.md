# Design rationale

The code is split into storage, service and CLI layers, with validation at the
two boundaries where data enters (CLI arguments and CSV rows) through one
function, `validate_transaction`. The service holds the rules and never prints
or touches files, so it can be tested with plain objects; the CLI only parses
and prints. Business interpretation: `amount` is always positive and `kind`
carries the sign, which removes the "is -5 an expense or a refund?" ambiguity;
unknown categories are rejected rather than mapped to "other", because silent
fixes hide typos. For undo, the file is rewritten atomically (temp file +
`os.replace`) after every change, so the disk always equals the true state and
a crash or reload can never resurrect an undone transaction.
