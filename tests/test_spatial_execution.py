"""Verify spatial predicates and explicit WKB conversion with DuckDB spatial.

The spatial extension must be downloadable or already installed. Set
PYGEOFILTER_SPATIAL_EXTENSION_DIRECTORY to use a custom extension cache.
"""

import datetime
import json
import os
from collections.abc import Iterator
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pystac
import pytest
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse
from shapely import wkb
from shapely.geometry import Point, box, mapping
from stac_geoparquet.arrow import parse_stac_items_to_arrow, to_parquet

from pygeofilter_duckdb import to_sql_where


@pytest.fixture
def spatial_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    """Load spatial and provide matching, disjoint, and null geometries."""
    with duckdb.connect(":memory:") as connection:
        directory = os.environ.get("PYGEOFILTER_SPATIAL_EXTENSION_DIRECTORY")
        if directory:
            connection.execute("SET extension_directory = ?", [directory])
        connection.install_extension("spatial")
        connection.load_extension("spatial")
        connection.execute("CREATE TABLE geometries (id INTEGER, geometry GEOMETRY)")
        connection.executemany(
            "INSERT INTO geometries VALUES (?, ST_GeomFromWKB(?::BLOB))",
            [(1, Point(0, 0).wkb), (2, Point(5, 5).wkb), (3, None)],
        )
        yield connection


@pytest.mark.parametrize("storage", ["native", "wkb"])
def test_intersects_and_wkb_round_trip(
    spatial_connection: duckdb.DuckDBPyConnection, storage: str
) -> None:
    if storage == "wkb":
        spatial_connection.execute(
            "CREATE TABLE stored_wkb AS "
            "SELECT id, ST_AsWKB(geometry)::BLOB AS geometry FROM geometries"
        )
        assert spatial_connection.execute(
            "SELECT typeof(geometry) FROM stored_wkb LIMIT 1"
        ).fetchone() == ("BLOB",)
        spatial_connection.execute(
            "CREATE VIEW items AS SELECT id, ST_GeomFromWKB(geometry) "
            "AS geometry FROM stored_wkb"
        )
    else:
        spatial_connection.execute("CREATE VIEW items AS SELECT * FROM geometries")

    root = parse(
        {
            "op": "s_intersects",
            "args": [
                {"property": "geometry"},
                {"type": "Point", "coordinates": [0, 0]},
            ],
        }
    )
    assert isinstance(root, ast.Node)
    predicate = to_sql_where(root, {"geometry": "geometry"})
    rows = spatial_connection.execute(
        "SELECT id, ST_AsWKB(geometry) FROM items WHERE " + predicate
    ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == 1
    assert wkb.loads(bytes(rows[0][1])).equals(Point(0, 0))
    assert spatial_connection.execute(
        "SELECT ST_AsWKB(geometry) FROM items WHERE id = 3"
    ).fetchone() == (None,)


def test_raw_wkb_requires_explicit_geometry_conversion(
    spatial_connection: duckdb.DuckDBPyConnection,
) -> None:
    with pytest.raises(duckdb.BinderException):
        spatial_connection.execute(
            "SELECT ST_Intersects(ST_AsWKB(geometry)::BLOB, geometry) FROM geometries"
        )


@pytest.mark.parametrize("storage", ["geoparquet", "raw-wkb-parquet"])
def test_geoparquet_predicate_results_and_round_trip(
    spatial_connection: duckdb.DuckDBPyConnection, tmp_path: Path, storage: str
) -> None:
    geometries = [Point(0.5, 0.5), Point(1, 0.5), box(0.75, 0.75, 2, 2), Point(5, 5)]
    items = [
        pystac.Item(
            id=str(index),
            geometry=mapping(geometry),
            bbox=list(geometry.bounds),
            datetime=datetime.datetime(2023, 2, 1, tzinfo=datetime.UTC),
            properties={},
        )
        for index, geometry in enumerate(geometries, start=1)
    ]
    items.append(
        pystac.Item(
            id="5",
            geometry=mapping(Point(9, 9)),
            bbox=[9, 9, 9, 9],
            datetime=datetime.datetime(2023, 2, 1, tzinfo=datetime.UTC),
            properties={},
        )
    )
    for item in items:
        item.add_asset(
            "data",
            pystac.Asset(
                href="https://example.com/data.tif", media_type=pystac.MediaType.GEOTIFF
            ),
        )
        item.validate()
    table = parse_stac_items_to_arrow(items).read_all()
    # stac-geoparquet 0.8.2 cannot parse null STAC geometries. Add a null to
    # the Arrow storage fixture to verify DuckDB's nullable geometry reads.
    geometry_values = table.column("geometry").to_pylist()
    geometry_values[-1] = None
    table = table.set_column(
        table.schema.get_field_index("geometry"),
        table.schema.field("geometry"),
        pa.array(geometry_values, type=pa.binary()),
    )
    path = tmp_path / "items.parquet"
    to_parquet(table, path)
    stored = pq.read_table(path)
    assert pa.types.is_binary(stored.schema.field("geometry").type)
    metadata = json.loads(stored.schema.metadata[b"geo"])
    assert metadata["primary_column"] == "geometry"
    assert metadata["columns"]["geometry"]["encoding"] == "WKB"
    assert stored.equals(table)

    if storage == "raw-wkb-parquet":
        raw_path = tmp_path / "raw.parquet"
        pq.write_table(stored.replace_schema_metadata(None), raw_path)
        spatial_connection.read_parquet(str(raw_path)).create_view("raw_items")
        assert spatial_connection.execute(
            "SELECT typeof(geometry) FROM raw_items LIMIT 1"
        ).fetchone() == ("BLOB",)
        spatial_connection.execute(
            "CREATE VIEW items AS SELECT id, ST_GeomFromWKB(geometry) "
            "AS geometry FROM raw_items"
        )
    else:
        spatial_connection.read_parquet(str(path)).create_view("items")
    exposed_type = spatial_connection.execute(
        "SELECT typeof(geometry) FROM items LIMIT 1"
    ).fetchone()
    # Newer DuckDB releases preserve the GeoParquet CRS in the geometry type.
    assert exposed_type in (("GEOMETRY",), ("GEOMETRY('EPSG:4326')",))

    root = parse(
        {
            "op": "s_intersects",
            "args": [
                {"property": "geometry"},
                mapping(box(0, 0, 1, 1)),
            ],
        }
    )
    assert isinstance(root, ast.Node)
    predicate = to_sql_where(root, {"geometry": "geometry"})
    rows = spatial_connection.execute(
        "SELECT id, ST_AsWKB(geometry) FROM items WHERE " + predicate + " ORDER BY id"
    ).fetchall()
    assert [row[0] for row in rows] == ["1", "2", "3"]
    for row, expected in zip(rows, geometries[:3], strict=True):
        assert wkb.loads(bytes(row[1])).equals(expected)
    assert spatial_connection.execute(
        "SELECT " + predicate + ", ST_AsWKB(geometry) FROM items WHERE id = '5'"
    ).fetchone() == (None, None)
