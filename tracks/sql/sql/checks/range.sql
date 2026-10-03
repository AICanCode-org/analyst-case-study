SELECT count(*) AS failing_rows, NULL AS observed FROM {table} WHERE {column} < {min} OR {column} > {max}
