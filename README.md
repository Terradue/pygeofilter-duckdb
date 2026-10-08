# pygeofilter-duckdb

[![PyPI - Version](https://img.shields.io/pypi/v/pygeofilter-duckdb.svg)](https://pypi.org/project/pygeofilter-duckdb)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pygeofilter-duckdb.svg)](https://pypi.org/project/pygeofilter-duckdb)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/terradue/pygeofilter-duckdb/package.yaml?branch=develop&event=push&label=build&logo=githubactions)](https://github.com/terradue/pygeofilter-duckdb/actions/workflows/package.yaml?query=branch%3Adevelop)
[![Code coverage](https://img.shields.io/codecov/c/github/terradue/pygeofilter-duckdb/develop?logo=codecov)](https://app.codecov.io/gh/terradue/pygeofilter-duckdb/tree/develop)

Documentation lives in [docs/](docs/index.md), organized into tutorials, how-to
guides, reference, and explanation. Preview it with `hatch run docs:serve`, or
validate the site with `hatch run docs:build`. Read the Docs configuration is
provided in `.readthedocs.yaml`.

This repo is an evolution of [https://github.com/DLR-terrabyte/pygeofilter-duckdb](https://github.com/DLR-terrabyte/pygeofilter-duckdb).

We have changed the orginal implementation to:
- make it a standalone library
- support DuckDB >=1.1.3,<1.6.0 (>=1.4.2 on Python 3.14 and later)
- added more examples to cover the process STAC Items -> geoparquet -> Duckdb
- use hatch

## Introduction

This is an extension for [pygeofilter](https://github.com/geopython/pygeofilter) to support SQL queries in DuckDB based on Geoparquet files. 

pygeofilter allows to parse several filter encoding standards (e.g., CQL JSON, CQL Text) and to convert them to queries for several backends (e.g., SQL, Django, Pandas). 

Geometry properties used in spatial filters must resolve to DuckDB `GEOMETRY`
columns. The evaluator constructs geometry literals and passes mapped property
columns directly to spatial functions; it does not decode stored WKB.

The notebooks write GeoParquet 1.1 with WKB geometry encoding. With the spatial
extension loaded, the verified DuckDB 1.1.3 baseline reads these metadata-bearing
files as `GEOMETRY`, even though Arrow exposes the stored geometry as binary.
Native `GEOMETRY` columns and these GeoParquet reads can be filtered directly.
DuckDB 1.5.6 additionally preserves the GeoParquet CRS in the exposed type,
reported as `GEOMETRY('EPSG:4326')` for these files.

For raw WKB `BLOB` columns, including Parquet files without geometry metadata,
decode the column in a view before applying the generated predicate:

```sql
INSTALL spatial;
LOAD spatial;

CREATE VIEW items AS
SELECT * EXCLUDE (geometry), ST_GeomFromWKB(geometry) AS geometry
FROM read_parquet('raw-wkb.parquet');
```

Inspect the exposed type with `SELECT typeof(geometry) FROM items LIMIT 1` to
choose the appropriate ingestion path. These conversions assume WKB bytes;
arbitrary binary data is not a valid geometry.

Use `ST_AsWKB(geometry)` when exporting query results to Arrow or Shapely. On
DuckDB 1.1.3 it returns `WKB_BLOB`, which Arrow exposes as binary. Spatial
predicates and WKB export propagate null geometries as SQL NULL; a WHERE clause
excludes rows whose predicate is NULL. Input and filter geometries must use the
same coordinate reference system; WKB conversion does not reproject coordinates.

The pinned `stac-geoparquet` 0.8.2 Item-to-Arrow converter rejects STAC Items
whose geometry is null. Nullable geometry reads are tested using an Arrow
storage fixture with a null WKB value inserted after Item conversion.

This extension originated from https://github.com/geopython/pygeofilter/issues/90.

## Example

Run the notebooks in the folder example:

Install the pinned notebook dependencies from the repository root using Python
3.11: `python -m pip install -e . -r example/requirements.txt`. Run the numbered
notebooks in order with `example` as the working directory. Notebook 02 uses the
live Planetary Computer STAC API, and notebook 03 reads the file it creates.
The separate query notebook downloads a remote GeoParquet file. Spatial
extension installation also requires network access unless already cached.

## Dependency compatibility

The library requires `duckdb>=1.1.3,<1.6.0` and
`pygeofilter>=0.4.0,<0.5.0`. The minimum DuckDB version is the oldest tested
baseline, replacing the unverified 0.2.0 minimum. The upper bounds stop at the
next minor releases, which need a new compatibility review.

CI runs the execution and spatial tests on Python 3.11 and 3.12 with DuckDB
1.1.3, 1.2.0, and 1.5.6, paired with pygeofilter 0.4.0. These representative
versions cover the minimum, the previously excluded 1.2.0 boundary, and the
modern target; they do not verify every intervening release. Publication waits
for this matrix to pass.

Local verification passed all 152 tests in each of the six supported
combinations. All four notebooks also executed successfully for each
combination, reusing previously fetched STAC Items for notebook 02. The matrix
used the matching spatial extension for each DuckDB version.

Pygeofilter 0.2.4 was also evaluated, but fails the suite's CQL2 Text negation
cases before SQL execution. Pygeofilter 0.4.0 is the oldest verified baseline
for the supported expressions. Inherited SQL handlers make upstream parser and
evaluator changes part of the compatibility review.

Notebook requirements remain pinned to DuckDB 1.1.3 for a reproducible example
environment. Their fixed Arrow/STAC stack is separate from the library's
dependency range. The compatibility matrix exercises actual GeoParquet reads
and spatial extensions, rather than checking SQL strings alone.

## Usage

For client-supplied filters, pass explicit, server-controlled property and
function mappings. For example, `{"cloud_cover": "eo:cloud_cover"}` exposes
only that property. `IdempotentDict()` in the example below accepts arbitrary
property names and is intended for datasets whose queryable fields are already
controlled by the caller.

Mapped property names are quoted as single identifiers, with embedded double
quotes escaped. Function mappings form an allowlist and must contain simple
or schema-qualified names such as `lower` or `main.lower`, rather than SQL
fragments. Quoted function identifiers are not supported. Unknown properties
and functions raise `KeyError`; invalid mapped function names and invalid LIKE
settings raise `ValueError` before SQL execution. Applications should translate
these exceptions into their own client-error responses.

String values, LIKE patterns and escape characters, and array elements receive
SQL literal escaping. LIKE wildcards still have their pattern meaning: escaping
SQL quotes does not make `%` or `_` literal pattern characters. Function
allowlisting controls access to functions; syntactically valid names alone do
not establish that a function is appropriate for a particular gateway.

```python
from pygeofilter.parsers.cql2_json import parse as json_parse
from pygeofilter_duckdb import to_sql_where
from pygeofilter.util import IdempotentDict

start = '2023-02-01T00:00:00Z'
end = '2023-02-28T23:59:59Z'

cql2_filter = {
  "op": "and",
  "args": [
    {
      "op": "between",
      "args": [
        {
          "property": "eo:cloud_cover"
        },
        [0, 21]
      ]
    },
      {
      "op": "between",
      "args": [
        {
          "property": "datetime"
        },
        [start, end]
      ]
    },
    {
        "op": "s_intersects",
        "args": [
          { "property": "geometry" } ,
          {
            "type": "Polygon", # Baden-Württemberg
            "coordinates": [[
                [7.5113934084, 47.5338000528],
    			[10.4918239143, 47.5338000528],
    			[10.4918239143, 49.7913749328],
    			[7.5113934084, 49.7913749328],
    			[7.5113934084, 47.5338000528]
            ]]
          }
        ]
      }
  ]
}

sql_where = to_sql_where(json_parse(cql2_filter), IdempotentDict())
print(sql_where)
```

This results in the following output

```
((("eo:cloud_cover" BETWEEN 0 AND 21) AND ("datetime" BETWEEN '2023-02-01T00:00:00Z' AND '2023-02-28T23:59:59Z')) AND ST_Intersects("geometry",ST_GeomFromHEXEWKB('0103000000010000000500000034DFB1B6AA0B1E4085B0648F53C44740509E1658D0FB244085B0648F53C44740509E1658D0FB244006A017C64BE5484034DFB1B6AA0B1E4006A017C64BE5484034DFB1B6AA0B1E4085B0648F53C44740')))
```

## Parameterized filters

Use `to_sql_where_params()` to keep filter values separate from SQL. It returns
the predicate and an ordered list to pass as DuckDB execute parameters. For
example, given a connection with an `items` table:

```python
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from pygeofilter_duckdb import to_sql_where_params

root = parse({"op": "=", "args": [{"property": "name"}, "O'Brien"]})
assert isinstance(root, ast.Node)
predicate, parameters = to_sql_where_params(root, {"name": "name"})
# predicate: ("name" = ?)
# parameters: ["O'Brien"]
rows = connection.execute(
    "SELECT * FROM items WHERE " + predicate, parameters
).fetchall()
```

Scalars, timestamps, array elements, LIKE patterns and escape characters, and
geometry literals use positional bindings. Each call produces its own parameter
list. Preserve that list's order and pass the values separately to DuckDB;
formatting them back into the SQL string discards the binding protection.
Identifiers and function names still require server-controlled mappings. The
existing `to_sql_where()` continues to return a single SQL string.

## License

[![Apache License, Version 2.0](https://img.shields.io/badge/license-Apache%20License%202.0-blue)](https://www.apache.org/licenses/LICENSE-2.0)
