# Translate your first filter

Create a cloud-cover filter, translate it into SQL, and execute it against an
in-memory DuckDB table. No catalogue or spatial extension is needed.

## 1. Install the package

```console
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pygeofilter-duckdb
```

On Windows, activate with `.venv\Scripts\activate` instead. From a repository
checkout, use `python -m pip install -e .` to test the local version.

## 2. Translate a filter

Save this as `first_filter.py`:

```python
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from pygeofilter_duckdb import to_sql_where

query = {"op": "<=", "args": [{"property": "eo:cloud_cover"}, 20]}
root = parse(query)
assert isinstance(root, ast.Node)
where = to_sql_where(root, {"eo:cloud_cover": "cloud_cover"})
print(where)
```

Run `python first_filter.py`. The output is:

```text
("cloud_cover" <= 20)
```

The field mapping connects the CQL2 property to the database column. The parser
can also return standalone values, so the assertion narrows its result to the
AST node accepted by `to_sql_where`.

## 3. Execute the predicate

Append this to the same file:

```python
import duckdb

with duckdb.connect() as connection:
    connection.execute("CREATE TABLE items (id VARCHAR, cloud_cover DOUBLE)")
    connection.executemany("INSERT INTO items VALUES (?, ?)", [("clear", 5), ("cloudy", 80)])
    rows = connection.execute(f"SELECT id FROM items WHERE {where} ORDER BY id").fetchall()
print(rows)
```

The final line is:

```text
[('clear',)]
```

This example constructs its filter from trusted constants. The evaluator emits
SQL text without bind parameters or string escaping; see the
[operator limits](../reference/operators.md#literal-and-execution-limits) before
accepting filter input from users.

Continue with [querying GeoParquet](../how-to/search.md) or
[configuring field mappings](../how-to/convert.md).
