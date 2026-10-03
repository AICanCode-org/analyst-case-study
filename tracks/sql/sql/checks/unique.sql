-- failing rows = rows whose {column} value appears more than once
SELECT coalesce(sum(n), 0) AS failing_rows, NULL AS observed
FROM (SELECT count(*) AS n FROM {table} GROUP BY {column} HAVING count(*) > 1)
