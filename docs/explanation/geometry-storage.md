# Geometry storage is an input contract

A GeoParquet geometry encoding and a DuckDB SQL type are different layers.
GeoParquet can store WKB bytes in a binary column and attach `geo` metadata.
With the spatial extension loaded, DuckDB can expose that column as native
`GEOMETRY` when it reads the file.

Raw binary without this metadata remains `BLOB` and must be decoded before
spatial filtering.

The evaluator constructs geometry literals, but passes mapped property columns
directly to spatial predicates. It does not inspect or decode those columns.
A spatial property must therefore resolve to native geometry, either stored
natively, exposed by a GeoParquet read, or created in a decoding view.

The two conversion functions serve opposite purposes:

| Function | Conversion | Use |
| --- | --- | --- |
| `ST_GeomFromWKB` | WKB → native geometry | Decode a stored binary column before filtering |
| `ST_AsWKB` | Native geometry → WKB | Export results to Arrow or Shapely |

A successful round trip verifies encoding and coordinate preservation. Input
and filter coordinates must still use the same CRS because WKB conversion does
not reproject them.

The reviewed DuckDB 1.5.6 GeoParquet path can expose a CRS-qualified geometry
type, unlike the older baseline.

Spatial predicates propagate null geometry as SQL NULL. WHERE excludes these
rows; output WKB is also null.

The pinned stac-geoparquet 0.8.2 Item-to-Arrow
converter rejects STAC Items with null geometry, so nullable storage tests insert
a null WKB value into Arrow after converting validated PySTAC Items.

Spatial execution tests cover intersecting, boundary, overlapping, disjoint,
and null cases, actual GeoParquet reads, raw WKB decoding, and a Shapely round
trip.

See [query GeoParquet](../how-to/query-geoparquet.md) for the ingestion steps
and [DuckDB's spatial functions](https://duckdb.org/docs/current/core_extensions/spatial/functions)
for conversion signatures.
