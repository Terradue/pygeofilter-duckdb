# Your first filter

In this tutorial you will create an in-memory table, parse a CQL2 JSON filter,
and execute a query with separately bound values.

This example introduces the DuckDB query workflow used for both attribute and
spatial filters. Here you select rows by a string property; in the
[spatial tutorial](spatial-filter.md), you use the same parser, SQL translator,
and execution API to select rows by geometry intersection.

From a checkout of this repository, create a Python 3.11 environment:

```bash
# Create and activate an isolated Python environment.
python3.11 -m venv .venv
. .venv/bin/activate
# Install this checkout so the example uses its evaluator implementation.
python -m pip install -e .
```

Save the following as `first_filter.py` and run `python first_filter.py`:

```python
"""Translate a CQL2 attribute filter and execute it against DuckDB rows."""

import duckdb
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from pygeofilter_duckdb import to_sql_where_params

# Pygeofilter parses the CQL2 JSON expression into an abstract syntax tree.
# This expression means: the property named "name" equals the value "O'Brien".
root = parse({"op": "=", "args": [{"property": "name"}, "O'Brien"]})
assert isinstance(root, ast.Node)

# Pygeofilter-duckdb translates the tree into a DuckDB WHERE predicate.
# The application maps the exposed property "name" to the database column
# "name". The returned SQL contains a ? placeholder; its value stays separate.
predicate, parameters = to_sql_where_params(root, {"name": "name"})

# DuckDB stores and queries the example data in a temporary in-memory database.
with duckdb.connect(":memory:") as connection:
    connection.execute("CREATE TABLE items (id INTEGER, name VARCHAR)")
    connection.executemany(
        "INSERT INTO items VALUES (?, ?)",
        [(1, "O'Brien"), (2, "alpha"), (3, "' OR TRUE --")],
    )
    # Append the generated predicate to an application-controlled query and
    # pass the values separately so DuckDB treats them as data, including quotes.
    rows = connection.execute(
        "SELECT id FROM items WHERE " + predicate + " ORDER BY id",
        parameters,
    ).fetchall()

print(predicate)
print(parameters)
print(rows)
# Only the row whose name equals the requested literal value should match.
assert rows == [(1,)]
```

Expected output, in order: the generated SQL predicate, its separately bound
value list, and the matching row IDs:

```text
("name" = ?)
["O'Brien"]
[(1,)]
```

Change the filter value to `"' OR TRUE --"` and the final assertion to
`assert rows == [(3,)]`. Running the script again selects that literal value.

Next, try [spatial filtering](spatial-filter.md), or look up the
[API contract](../reference/api.md).
