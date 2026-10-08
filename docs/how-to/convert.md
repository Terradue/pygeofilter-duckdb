# Configure filter translation

Use explicit dictionaries to map CQL2 properties and functions to SQL names.
These examples translate trusted filters; they do not execute queries.

## Map properties to columns

```python
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from pygeofilter_duckdb import to_sql_where

query = {"op": "<=", "args": [{"property": "eo:cloud_cover"}, 20]}
root = parse(query)
assert isinstance(root, ast.Node)
where = to_sql_where(root, {"eo:cloud_cover": "cloud_cover"})
assert where == '("cloud_cover" <= 20)'
```

Every referenced property needs a mapping. Use the same name on both sides when
properties already match column names. Unknown properties raise `KeyError`.
Mapping values are quoted as single identifiers: `table.column` is not expanded
into a qualified name, and SQL expressions do not belong in the mapping.

## Map function names

```python
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from pygeofilter_duckdb import to_sql_where

query = {
    "op": "=",
    "args": [{"function": {"name": "lower", "arguments": [{"property": "id"}]}}, "scene-a"],
}
root = parse(query)
assert isinstance(root, ast.Node)
where = to_sql_where(root, {"id": "id"}, {"lower": "lower"})
assert where == '(lower("id") = \'scene-a\')'
```

`function_map` defaults to an empty dictionary. Missing function names raise
`KeyError`; the evaluator does not verify that the function exists in DuckDB.
Keep function mappings under application control.

## Filter timestamps

Use inclusive `between` bounds with ISO timestamp strings:

```python
query = {
    "op": "between",
    "args": [{"property": "datetime"}, ["2023-02-01T00:00:00Z", "2023-02-28T23:59:59Z"]],
}
```

Strings and Python `datetime.datetime` values are quoted; parsing or casting them
during execution is DuckDB's responsibility. The evaluator does not implement
dedicated temporal predicates such as `t_before`. See the
[operator reference](../reference/operators.md).
