# Python API reference

## `pygeofilter_duckdb.to_sql_where`

```python
from pygeofilter_duckdb import to_sql_where
```

Signature: `to_sql_where(root: ast.Node, field_mapping: dict[str, str], function_map: dict[str, str] | None = None) -> str`.

| Parameter | Meaning |
| --- | --- |
| `root` | Parsed pygeofilter AST node. Parse CQL2 separately. |
| `field_mapping` | Required dictionary mapping property names to SQL column names. |
| `function_map` | Optional dictionary mapping function names to SQL function names; defaults to an empty mapping. |

Returns a SQL expression without the `WHERE` keyword. It does not open a
connection or execute SQL.

| Failure | Cause |
| --- | --- |
| `KeyError` | A referenced property or function has no mapping. |
| `NotImplementedError` | The AST contains a node without an evaluator handler. |
| `TypeError` | Evaluation returns something other than a SQL expression string, or an inherited handler receives an incompatible literal. |

Parser errors occur before this function is called. Shapely errors can propagate
when a supplied geometry cannot be converted.

`parse` from `pygeofilter.parsers.cql2_json` returns a union of AST nodes and
literal values. Narrow it with `isinstance(root, ast.Node)` for strict typing.
The [tutorial](../tutorials/first-filter.md) demonstrates this.

## `pygeofilter_duckdb.evaluate.DuckDBEvaluator`

A subclass of pygeofilter 0.4.0's `SQLEvaluator`. Its inherited constructor accepts
`attribute_map`, `function_map`, and `use_ilike=False`. Prefer `to_sql_where` for
ordinary translation; the wrapper also checks the final result type.

| Handler | Behavior |
| --- | --- |
| `geometry(node: values.Geometry) -> str` | Converts GeoJSON geometry to hexadecimal WKB with Shapely and emits `ST_GeomFromHEXEWKB(...)`. |
| `envelope(node: values.Envelope) -> str` | Builds a rectangular polygon and emits the same constructor. |
| `literal(node: Literal) -> Literal` | Quotes strings and datetime values; preserves other literal values. |

`Literal` covers lists, strings, numbers, booleans, dates, times, and timedeltas.
Logical, comparison, arithmetic, property, and function handlers are inherited.
See the [operator reference](operators.md) for limitations.
