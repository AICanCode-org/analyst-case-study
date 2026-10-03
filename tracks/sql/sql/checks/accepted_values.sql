-- {values} is one of the contract lists loaded as a table (cfg_devices, cfg_channels, cfg_steps)
SELECT count(*) AS failing_rows, NULL AS observed
FROM {table}
WHERE {column} IS NULL OR {column} NOT IN (SELECT value FROM {values})
