"""Verify ordered DuckDB bindings without embedding client values in SQL."""

import datetime
from collections.abc import Callable

import duckdb
import pytest
from pygeofilter import ast, values
from pygeofilter.parsers.cql2_json import parse

from pygeofilter_duckdb import to_sql_where_params
from tests.test_spatial_execution import spatial_connection as spatial_connection

attribute: Callable[[str], ast.Attribute] = ast.Attribute


@pytest.mark.parametrize(
    "value",
    ["O'Brien", "' OR TRUE --", "'; DROP TABLE items; --", "quotes '\" ?", "雪\x00end"],
)
def test_bound_strings_are_data(value: str) -> None:
    root = parse({"op": "=", "args": [{"property": "name"}, value]})
    assert isinstance(root, ast.Node)
    sql, parameters = to_sql_where_params(root, {"name": "name"})
    assert sql == '("name" = ?)'
    assert parameters == [value]
    with duckdb.connect() as connection:
        connection.execute("CREATE TABLE items (id INTEGER, name VARCHAR)")
        connection.executemany(
            "INSERT INTO items VALUES (?, ?)", [(1, value), (2, "other"), (3, None)]
        )
        assert connection.execute(
            "SELECT id FROM items WHERE " + sql, parameters
        ).fetchall() == [(1,)]


def test_nested_filter_parameter_order() -> None:
    root = parse(
        {
            "op": "and",
            "args": [
                {
                    "op": "=",
                    "args": [
                        {"function": {"name": "normalize", "arguments": ["O'BRIEN"]}},
                        "o'brien",
                    ],
                },
                {
                    "op": "or",
                    "args": [
                        {"op": "between", "args": [{"property": "score"}, [10, 20]]},
                        {"op": "in", "args": [{"property": "score"}, [30, 40]]},
                    ],
                },
            ],
        }
    )
    assert isinstance(root, ast.Node)
    sql, parameters = to_sql_where_params(
        root, {"score": "score"}, {"normalize": "lower"}
    )
    assert parameters == ["O'BRIEN", "o'brien", 10, 20, 30, 40]
    with duckdb.connect() as connection:
        assert connection.execute(
            "SELECT * FROM (VALUES (15), (30), (50), (NULL)) items(score) WHERE " + sql,
            parameters,
        ).fetchall() == [(15,), (30,)]


@pytest.mark.parametrize("value", ["O'Brien", "' OR TRUE --", "café 雪"])
def test_like_pattern_and_escape_are_bound(value: str) -> None:
    root = ast.Like(attribute("name"), value, False, "%", "_", "\\", False)
    sql, parameters = to_sql_where_params(root, {"name": "name"})
    assert sql == '"name" LIKE ? ESCAPE ?'
    assert parameters == [value, "\\"]
    with duckdb.connect() as connection:
        assert connection.execute(
            "SELECT ? AS name WHERE " + sql, [value, *parameters]
        ).fetchone() == (value,)


def test_array_parameters_and_independent_calls() -> None:
    root = parse(
        {"op": "=", "args": [{"property": "names"}, ["O'Brien", "' OR TRUE --"]]}
    )
    assert isinstance(root, ast.Node)
    sql, parameters = to_sql_where_params(root, {"names": "names"})
    assert parameters == ["O'Brien", "' OR TRUE --"]
    with duckdb.connect() as connection:
        assert connection.execute(
            "SELECT ? AS names WHERE " + sql, [parameters, *parameters]
        ).fetchone() == (parameters,)
    _, independent = to_sql_where_params(root, {"names": "names"})
    parameters.clear()
    assert independent == ["O'Brien", "' OR TRUE --"]


@pytest.mark.parametrize(
    "root",
    [
        ast.GeometryIntersects(
            attribute("geometry"),
            values.Geometry({"type": "Point", "coordinates": [0, 0]}),
        ),
        ast.GeometryIntersects(attribute("geometry"), values.Envelope(-1, 1, -1, 1)),
        ast.BBox(attribute("geometry"), -1, -1, 1, 1),
    ],
)
def test_spatial_literals_are_bound(
    spatial_connection: duckdb.DuckDBPyConnection, root: ast.Node
) -> None:
    sql, parameters = to_sql_where_params(root, {"geometry": "geometry"})
    assert len(parameters) == 1
    assert "ST_GeomFromHEXEWKB(?)" in sql
    assert spatial_connection.execute(
        "SELECT id FROM geometries WHERE " + sql, parameters
    ).fetchall() == [(1,)]


def test_unknown_property_and_function_rejected() -> None:
    with pytest.raises(KeyError):
        to_sql_where_params(ast.Equal(attribute("missing"), 1), {})
    with pytest.raises(KeyError):
        to_sql_where_params(ast.Function("missing", [1]), {})
    with pytest.raises(ValueError, match="Mapped functions"):
        to_sql_where_params(
            ast.Function("allowed", [1]), {}, {"allowed": "lower); SELECT 1 --"}
        )


@pytest.mark.parametrize(
    "value",
    [
        datetime.date(2023, 2, 1),
        datetime.datetime(2023, 2, 1, tzinfo=datetime.UTC),
    ],
)
def test_temporal_values_keep_native_types(
    value: datetime.date,
) -> None:
    root = parse({"op": "=", "args": [{"property": "value"}, value]})
    assert isinstance(root, ast.Node)
    sql, parameters = to_sql_where_params(root, {"value": "value"})
    assert parameters == [value]
    with duckdb.connect() as connection:
        assert connection.execute(
            "SELECT 1 FROM (SELECT ? AS value) WHERE " + sql, [value, *parameters]
        ).fetchall() == [(1,)]
