SELECT count(*) AS failing_rows, NULL AS observed
FROM {table}
WHERE CAST({column} AS DATE) NOT BETWEEN getvariable('period_start') AND getvariable('period_end')
