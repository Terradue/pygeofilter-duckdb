# pygeofilter-duckdb

Translate parsed CQL2 filters into SQL predicates for DuckDB. The package extends
pygeofilter's SQL evaluator with DuckDB geometry constructors and timestamp literals.
It returns the expression used after `WHERE`; your application executes the query.

For client-supplied filters, prefer `to_sql_where_params` to keep literal values
separate from SQL, with application-controlled property and function mappings.

## Start here

| Goal | Guide |
| --- | --- |
| Translate and execute a filter | [First filter tutorial](tutorials/first-filter.md) |
| Query a GeoParquet file | [Query GeoParquet](how-to/search.md) |
| Map properties and functions | [Configure translation](how-to/convert.md) |
| Run checks or preview documentation | [Development guide](how-to/develop.md) |
| Look up exact behavior | [Python API](reference/api.md) and [operators](reference/operators.md) |
| Build a distribution | [Package builds](reference/packaging.md) |
| Understand the evaluator | [Architecture](explanation/architecture.md) |

## Installation and compatibility

```console
python -m pip install pygeofilter-duckdb
```

The project requires Python 3.10 or later and requires `pygeofilter>=0.4.0,<0.5.0`.
The configured test matrix covers Python 3.10–3.14.

| Python | DuckDB dependency |
| --- | --- |
| 3.10–3.13 | `>=1.1.3,<1.6.0` |
| 3.14 and later | `>=1.4.2,<1.6.0` |

These constraints come from `pyproject.toml`. The Python 3.14 constraint avoids
building the older DuckDB dependency from source. The tests execute scalar and spatial queries across representative dependency
versions; see [verified compatibility](reference/compatibility.md).

The [example notebooks](https://github.com/Terradue/pygeofilter-duckdb/tree/develop/example)
show STAC Items, GeoParquet creation, and DuckDB queries. They may need additional
dependencies and network access.
