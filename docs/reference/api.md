# API reference

Both helpers are exported from `pygeofilter_duckdb`. Parse the filter using
pygeofilter before calling them; the root must be a `pygeofilter.ast.Node` that
produces a SQL expression.

## `to_sql_where_params`

```python
# Signature reference: returns a WHERE expression and ordered bound values.
# This describes the API; it is not an executable function call.
to_sql_where_params(
    root: ast.Node,  # Parsed filter expression.
    field_mapping: dict[str, str],  # Property names mapped to single columns.
    function_map: dict[str, str] | None = None,  # Optional function allowlist.
) -> tuple[str, list[SQLParameter]]
```

Returns a predicate containing positional `?` placeholders and its ordered
values. Each call returns an independent parameter list. Execute with
`connection.execute("SELECT ... WHERE " + predicate, parameters)`.
Do not interpolate the values back into the SQL.

`SQLParameter` comprises `str`, `int`, `float`, `bool`, `datetime.datetime`,
`datetime.date`, `datetime.time`, and `datetime.timedelta`. Lists are rendered
as SQL arrays whose elements are bound individually.

Geometry, envelope, and
bounding-box values use bound hexadecimal WKB passed to `ST_GeomFromHEXEWKB`.

## `to_sql_where`

```python
# Signature reference: returns a WHERE expression with rendered literals.
# This describes the API; it is not an executable function call.
to_sql_where(
    root: ast.Node,  # Parsed filter expression.
    field_mapping: dict[str, str],  # Property names mapped to single columns.
    function_map: dict[str, str] | None = None,  # Optional function allowlist.
) -> str
```

Returns a SQL predicate without the `WHERE` keyword. Strings escape embedded
apostrophes by doubling them. Values are rendered into SQL rather than returned
separately. The existing string-returning contract remains available.

## Mapping and errors

| Argument or failure | Contract |
| --- | --- |
| `field_mapping` | Application-controlled property names mapped to single database identifiers |
| `function_map` | Application-controlled allowlist; omitted means no mapped functions |
| Unknown property or function | `KeyError` |
| Invalid mapped function or pattern configuration | `ValueError` |
| Evaluation does not return SQL | `TypeError` |
| Unsupported bound literal | `TypeError` in the parameterized helper |

Neither helper connects to DuckDB, loads extensions, decodes property columns,
or catches parser and database exceptions.

## `DuckDBEvaluator`

Import from `pygeofilter_duckdb.evaluate`. It extends pygeofilter's
`SQLEvaluator` using decorated handlers. Its inherited constructor takes
`attribute_map`, optional `function_map`, and `use_ilike=False`.
Call `evaluate(root)` to obtain the SQL expression.

To request `ILIKE` for a case-insensitive `ast.Like` node, construct the evaluator
with `use_ilike=True`; the convenience helpers use the constructor default.
Do not assume that every parser option is exposed by the helpers.
