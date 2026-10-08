# Operator reference

The evaluator inherits SQL handlers from pygeofilter 0.4.0 and overrides geometry,
envelope, and literal handling. This describes implemented AST handlers, not full
CQL2 conformance. Accepted input syntax belongs to the chosen parser.

## Logical and comparison expressions

| Expression | SQL form |
| --- | --- |
| AND / OR | `(left AND right)` / `(left OR right)` |
| NOT | `NOT expression` |
| Comparisons | `=`, `<>`, `<`, `<=`, `>`, `>=` |
| Between | `column BETWEEN low AND high`, optionally `NOT BETWEEN` |
| Like | `LIKE` with an `ESCAPE` clause |
| Null test | `column IS NULL`, optionally `IS NOT NULL` |
| Membership | `column IN (...)`, optionally `NOT IN` |
| Arithmetic | Parenthesized `+`, `-`, `*`, `/` |
| Function | `mapped_name(arguments)` |

Properties are double-quoted column names looked up in the field mapping.
Function names require an explicit function mapping.

## Spatial expressions

| Predicate | DuckDB function |
| --- | --- |
| Intersects | `ST_Intersects` |
| Disjoint | `ST_Disjoint` |
| Contains | `ST_Contains` |
| Within | `ST_Within` |
| Touches | `ST_Touches` |
| Crosses | `ST_Crosses` |
| Overlaps | `ST_Overlaps` |
| Equals | `ST_Equals` |

Geometry and envelope literals use `ST_GeomFromHEXEWKB` with Shapely-generated
hexadecimal WKB. The inherited BBox handler creates a polygon with
`ST_GeomFromText` and tests intersection. Executing spatial expressions requires
the spatial extension and compatible geometry columns.

## Temporal expressions

Use comparisons and inclusive `between` bounds for timestamp columns. Python
`datetime.datetime` values and strings are single-quoted without timezone
normalization. Dedicated temporal predicates and interval nodes have no SQL
handler and can raise `NotImplementedError`.

## Literal and execution limits

- Strings are enclosed in single quotes without escaping embedded quotes.
  Generated SQL is unsuitable for executing arbitrary untrusted filter input.
- Column identifiers are double-quoted without escaping embedded double quotes.
  Keep property and function mappings under application control.
- Numeric, boolean, list, date, time, and timedelta values are returned unchanged
  by the literal handler. Surrounding handlers may format them into SQL, but
  this does not guarantee valid SQL for every type.
- Inherited membership and function handlers join string arguments. Numeric
  literals in those positions can raise `TypeError` rather than producing SQL.
- Translation does not check column types, function availability, coordinate
  systems, or query results. The suite tests translation and result-type
  validation, not exhaustive execution against DuckDB.
