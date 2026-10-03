-- fails (1 row) when {table} has fewer than {min} rows
-- TODO(M2): one row (failing_rows, observed) for this check; placeholders come from the contract
SELECT
    NULL AS failing_rows,
    NULL AS observed
