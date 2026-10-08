# Query GeoParquet and raw WKB

Load the spatial extension before reading geometry data:

```python
# Prerequisite: connection is an open DuckDB connection, as in the tutorials.
# Install the extension if needed; loading enables spatial functions and types.
connection.execute("INSTALL spatial")
connection.execute("LOAD spatial")
```

For a fixed, application-controlled path, create a view:

```sql
-- Read a metadata-bearing GeoParquet file through a view named items.
CREATE VIEW items AS SELECT * FROM read_parquet('items.parquet');
-- Inspect the SQL type DuckDB exposes before applying a spatial predicate.
SELECT typeof(geometry) FROM items LIMIT 1;
```

Inspect the type before filtering. With the spatial extension loaded, the
verified GeoParquet files expose `GEOMETRY`; DuckDB 1.5.6 may expose a CRS-qualified
geometry type. They can be filtered directly.

Arrow exports can change the
representation, so inspect any re-registered table again.

If the column is raw WKB `BLOB`, create a decoding view:

```sql
-- Use this alternative view for raw WKB instead of the GeoParquet view above.
-- Keep other columns and replace the binary geometry with decoded GEOMETRY.
CREATE VIEW items AS
SELECT * EXCLUDE (geometry), ST_GeomFromWKB(geometry) AS geometry
FROM read_parquet('raw-wkb.parquet');
```

With either view created on your open `connection`, parse a spatial filter,
map its property to the view's `geometry` column, and execute the predicate:

```python
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from pygeofilter_duckdb import to_sql_where_params

# Select geometries that intersect point (0, 0). Use coordinates in the same
# CRS as your data, and replace this point with your desired search geometry.
root = parse({
    "op": "s_intersects",
    "args": [
        {"property": "geometry"},
        {"type": "Point", "coordinates": [0, 0]},
    ],
})
assert isinstance(root, ast.Node)

# The items view exposes native GEOMETRY for both ingestion paths above.
# Bind the filter geometry separately from the generated SQL predicate.
predicate, parameters = to_sql_where_params(root, {"geometry": "geometry"})

# Execute against the existing connection and view. This assumes an id column;
# replace it with your dataset's identifier column if necessary.
# Export matching geometries as WKB for binary consumers such as Shapely.
rows = connection.execute(
    "SELECT id, ST_AsWKB(geometry) AS geometry FROM items WHERE "
    + predicate
    + " ORDER BY id",
    parameters,
).fetchall()
print(rows)
```

Each result contains an ID and WKB geometry. Disjoint and null geometries are
excluded by the intersection predicate.

Field mappings are identifiers, so a value such as
`ST_GeomFromWKB(geometry)` is not a supported field mapping.

Export geometry explicitly when consumers need WKB:

```sql
-- Encode native geometry as WKB for binary consumers such as Shapely.
-- Null geometries remain NULL in the exported column.
SELECT id, ST_AsWKB(geometry) AS geometry FROM items;
```

`ST_AsWKB` encodes native geometry; `ST_GeomFromWKB` decodes WKB. Conversion does
not reproject coordinates. See [geometry storage](../explanation/geometry-storage.md)
for CRS and null behavior and the
[DuckDB spatial reference](https://duckdb.org/docs/current/core_extensions/spatial/functions)
for function details.
