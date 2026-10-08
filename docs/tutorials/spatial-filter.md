# Your first spatial filter

This tutorial selects an intersecting point, excludes a disjoint point, and
observes how a null geometry behaves. Complete the
[first-filter setup](first-filter.md) first. Installing DuckDB's spatial
extension requires network access unless it is already cached.

Save this as `spatial_filter.py` and run `python spatial_filter.py`:

```python
"""Filter native DuckDB geometries and reconstruct the result with Shapely."""

import duckdb
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from pygeofilter_duckdb import to_sql_where_params
from shapely import from_wkb
from shapely.geometry import Point

# Parse a spatial predicate: the geometry property intersects point (0, 0).
root = parse({
    "op": "s_intersects",
    "args": [
        {"property": "geometry"},
        {"type": "Point", "coordinates": [0, 0]},
    ],
})
assert isinstance(root, ast.Node)
# Map the queryable property to a native GEOMETRY column. The translator
# binds the filter geometry as hexadecimal WKB in a geometry constructor.
predicate, parameters = to_sql_where_params(root, {"geometry": "geometry"})

with duckdb.connect(":memory:") as connection:
    # Install the extension if needed, then load it into this connection.
    connection.execute("INSTALL spatial")
    connection.execute("LOAD spatial")
    # Store an intersecting point, a disjoint point, and a null geometry.
    connection.execute("CREATE TABLE items (id INTEGER, geometry GEOMETRY)")
    connection.execute(
        "INSERT INTO items VALUES "
        "(1, ST_Point(0, 0)), (2, ST_Point(5, 5)), (3, NULL)"
    )
    # Apply the predicate and encode the selected geometry as WKB for Shapely.
    # NULL predicates are excluded by WHERE, just like FALSE predicates.
    rows = connection.execute(
        "SELECT id, ST_AsWKB(geometry) FROM items WHERE " + predicate,
        parameters,
    ).fetchall()

# Check the selected ID and confirm that WKB preserves the point coordinates.
assert [row[0] for row in rows] == [1]
assert from_wkb(bytes(rows[0][1])).equals(Point(0, 0))
print([row[0] for row in rows])
```

The output is `[1]`. The query exports the matching native geometry as WKB and
Shapely reconstructs the original point. Row 3's predicate evaluates to SQL NULL,
so it does not appear in the result.

For stored files, continue with [querying GeoParquet](../how-to/query-geoparquet.md).
