# How translation works

The translation path is:

```text
CQL2 JSON → pygeofilter parser → AST → DuckDBEvaluator → SQL predicate
```

## Parsing and execution are separate

The caller selects a pygeofilter parser and passes an AST node to `to_sql_where`.
The wrapper constructs a `DuckDBEvaluator`, evaluates the tree, checks that the
result is a string, and returns it. The caller embeds the predicate in a query
and manages the DuckDB connection.

This separation allows translation tests to run without a database, spatial
extension downloads, catalogue access, or GeoParquet files. A successful
translation does not prove that a query will execute against a particular schema.

## Reuse the SQL evaluator

`DuckDBEvaluator` inherits logical, comparison, arithmetic, property, and function
handlers from pygeofilter's `SQLEvaluator`. Only geometry, envelope, and literal
handling are specialized. Field mappings connect filter names to database
columns, and function mappings connect filter functions to SQL functions.

Shapely converts a geometry or rectangular envelope to hexadecimal WKB. The
DuckDB-specific handler wraps it in `ST_GeomFromHEXEWKB(...)`, while retaining the
base evaluator's other SQL composition behavior.

## Data preparation belongs to the application

The package does not read STAC catalogues, convert STAC responses, inspect
GeoParquet schemas, reproject coordinates, or execute SQL. The repository's
notebooks demonstrate workflows using other libraries for those responsibilities.
Geometry representation can vary with the file and DuckDB version; prepare
compatible columns before applying spatial predicates.

The translator emits SQL text rather than bound parameters. Consult the
[literal limits](../reference/operators.md#literal-and-execution-limits) when
deciding which input your application can safely translate and execute.
