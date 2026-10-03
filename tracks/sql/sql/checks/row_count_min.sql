SELECT CASE WHEN count(*) >= {min} THEN 0 ELSE 1 END AS failing_rows, NULL AS observed FROM {table}
