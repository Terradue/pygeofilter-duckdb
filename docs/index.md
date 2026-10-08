# pygeofilter-duckdb

Translate parsed OGC filters into DuckDB SQL for tabular and GeoParquet queries.
The library generates a predicate; your application owns the connection, data
loading, query structure, and execution.

This documentation follows [Diátaxis](https://diataxis.fr/):

| Your goal | Start here |
| --- | --- |
| Learn by running a complete example | [Your first filter](tutorials/first-filter.md) |
| Learn spatial filtering | [Your first spatial filter](tutorials/spatial-filter.md) |
| Solve a specific task | [Query GeoParquet](how-to/query-geoparquet.md) or [run notebooks](how-to/run-notebooks.md) |
| Look up signatures and behavior | [API reference](reference/api.md) and [operators](reference/operators.md) |
| Understand the design | [Filter pipeline](explanation/filter-pipeline.md), [SQL safety](explanation/sql-safety.md), and [geometry storage](explanation/geometry-storage.md) |

Use Python 3.11 or newer. The verified dependency combinations are listed in
[compatibility](reference/compatibility.md). For client-supplied filters, prefer
`to_sql_where_params` and application-controlled property and function mappings.
