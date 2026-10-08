# Restrict client properties and functions

Define queryable names and SQL function mappings in application code:

```python
"""Translate an allowlisted function and property without executing a query."""

from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from pygeofilter_duckdb import to_sql_where_params

# These mappings belong to the application, not the incoming client request.
# The exposed cloud_cover property maps to a column whose name contains a colon.
fields = {"name": "name", "cloud_cover": "eo:cloud_cover"}
# Only the lower function is available to this filter.
functions = {"lower": "lower"}
# Parse the condition lower(name) = 'alpha'. JSON function nodes use
# "arguments" for their operands in the supported pygeofilter parser.
root = parse({
    "op": "=",
    "args": [{"function": {"name": "lower", "arguments": [{"property": "name"}]}}, "alpha"],
})
assert isinstance(root, ast.Node)
# Resolve names through the allowlists and bind "alpha" separately from SQL.
# The result is (lower("name") = ?) with parameters ["alpha"].
predicate, parameters = to_sql_where_params(root, fields, functions)
```

Keep both mappings under application control; clients supply filter expressions,
while your application decides which columns and functions they can access.

The mapping rules are:

- **Properties:** each value identifies one column. Embedded double quotes are
  escaped, and a value containing dots is treated as one column name.
- **Functions:** each value must be a name such as `lower` or `main.lower`.
  SQL fragments and quoted function names are rejected.
- **Derived columns:** expose them through a view, then map the property to the
  view's column. Field mappings cannot contain SQL expressions.

Handle failures at the stage where they occur:

| Stage | Failure to handle |
| --- | --- |
| Parsing | Invalid filter syntax reported by the parser |
| Translation | `KeyError` for an unmapped property or function |
| Translation | `ValueError` for an invalid function mapping or pattern setting |
| Translation | `TypeError` for an unsupported bound literal or a root that does not produce SQL |
| Execution | DuckDB errors for missing columns, incompatible types, or unavailable functions |

If you expose this library through a gateway, define its supported operators,
validation rules, and HTTP responses in the application. This repository does
not contain a gateway or specify HTTP status codes.

See [SQL safety](../explanation/sql-safety.md) for the reasoning behind these rules.
