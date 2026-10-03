-- every {column} must exist in {to_table}.{to_column}
-- TODO(M2): one row (failing_rows, observed) for this check; placeholders come from the contract
SELECT
    NULL AS failing_rows,
    NULL AS observed
