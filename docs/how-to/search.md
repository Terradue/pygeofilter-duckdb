# Query GeoParquet

The application owns the DuckDB connection, file access, extension setup, and
result handling. `to_sql_where` supplies the filter expression.

## Query ordinary columns

This example expects `items.parquet` with `id` and `eo:cloud_cover` columns:

```python
import duckdb
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from pygeofilter_duckdb import to_sql_where

query = {"op": "between", "args": [{"property": "eo:cloud_cover"}, [0, 21]]}
root = parse(query)
assert isinstance(root, ast.Node)
where = to_sql_where(root, {"eo:cloud_cover": "eo:cloud_cover"})

with duckdb.connect() as connection:
    rows = connection.execute(
        f"SELECT id FROM read_parquet(?) WHERE {where}", ["items.parquet"]
    ).fetchall()
print(rows)
```

The file path is bound separately. The generated predicate itself is SQL text and
must come from trusted input; it is not a parameterized filter.

## Add a spatial predicate

Spatial predicates require DuckDB's spatial extension. Install it once in an
environment with network access, then load it on each connection:

```python
import duckdb

with duckdb.connect() as connection:
    connection.execute("INSTALL spatial")
    connection.execute("LOAD spatial")
```

Use a CQL2 spatial filter such as:

```python
query = {
    "op": "s_intersects",
    "args": [
        {"property": "geometry"},
        {"type": "Point", "coordinates": [12.5, 41.9]},
    ],
}
```

Parse and translate it with `{"geometry": "geometry"}`, and execute the query on
a connection where `spatial` is loaded. Geometry literals become
`ST_GeomFromHEXEWKB(...)` expressions. The geometry column must have a type accepted
by that DuckDB version's spatial functions. If a file exposes WKB as a BLOB,
convert it to a geometry in a view with `ST_GeomFromWKB(geometry)` and query the
view. Field mappings name columns; they do not insert SQL expressions.

The translator does not inspect GeoParquet metadata, normalize coordinate systems,
or load extensions. Check the file's coordinate system and column types before
running spatial queries. See [architecture](../explanation/architecture.md).
