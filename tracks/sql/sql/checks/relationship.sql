-- every {column} must exist in {to_table}.{to_column}
SELECT count(*) AS failing_rows, NULL AS observed
FROM {table}
WHERE {column} IS NULL OR {column} NOT IN (SELECT {to_column} FROM {to_table})
