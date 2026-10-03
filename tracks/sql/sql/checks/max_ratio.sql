-- issue rows / denominator rows must be at most {max}; {of_table} is raw_<table> or the clean table
WITH x AS (
    SELECT
        (SELECT n FROM issues WHERE issue = '{issue}') AS n,
        (SELECT count(*) FROM {of_table}) AS d
)
SELECT
    CASE WHEN n / nullif(d, 0) > {max} THEN n ELSE 0 END AS failing_rows,
    coalesce(n / nullif(d, 0), 0.0) AS observed
FROM x
