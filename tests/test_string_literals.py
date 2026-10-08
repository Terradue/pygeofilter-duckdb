"""Verify SQL literal rendering and execution against an in-memory DuckDB."""

import datetime

import duckdb
import pytest
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse

from pygeofilter_duckdb import to_sql_where
from pygeofilter_duckdb.evaluate import DuckDBEvaluator


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("plain", "'plain'"),
        ("", "''"),
        ("O'Brien", "'O''Brien'"),
        ("'leading", "'''leading'"),
        ("trailing'", "'trailing'''"),
        ("''", "''''''"),
        ("it's 'quoted'", "'it''s ''quoted'''"),
        ('double "quotes"', "'double \"quotes\"'"),
        ("café 雪's", "'café 雪''s'"),
        ("line\nbreak\ttab", "'line\nbreak\ttab'"),
        (r"C:\folder\file", r"'C:\folder\file'"),
        ("' OR TRUE --", "''' OR TRUE --'"),
        ("'; DROP TABLE items; --", "'''; DROP TABLE items; --'"),
        (r"\' OR TRUE --", r"'\'' OR TRUE --'"),
    ],
)
def test_string_literal_rendering(value: str, expected: str) -> None:
    evaluator = DuckDBEvaluator({}, {})
    assert evaluator.evaluate(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "plain",
        "",
        "O'Brien",
        "'leading",
        "trailing'",
        "''",
        "it's 'quoted'",
        'double "quotes"',
        "café 雪's",
        "line\nbreak\ttab",
        r"C:\folder\file",
        "' OR TRUE --",
        "'; DROP TABLE items; --",
        r"\' OR TRUE --",
    ],
)
def test_parsed_string_filter_matches_only_exact_value(value: str) -> None:
    root = parse({"op": "=", "args": [{"property": "name"}, value]})
    assert isinstance(root, ast.Node)
    predicate = to_sql_where(root, {"name": "name"})

    with duckdb.connect(":memory:") as connection:
        connection.execute("CREATE TABLE items (id INTEGER, name VARCHAR)")
        connection.executemany(
            "INSERT INTO items VALUES (?, ?)",
            [(1, value), (2, "unrelated"), (3, value + "suffix"), (4, None)],
        )
        rows = connection.execute("SELECT id FROM items WHERE " + predicate).fetchall()
        assert rows == [(1,)]
        assert connection.execute("SELECT count(*) FROM items").fetchone() == (4,)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (7, "7"),
        (1.25, "1.25"),
        (True, "True"),
        (False, "False"),
        (
            datetime.datetime(2023, 2, 1, tzinfo=datetime.timezone.utc),
            "'2023-02-01 00:00:00+00:00'",
        ),
    ],
)
def test_non_string_literals_render_as_sql_tokens(
    value: int | float | bool | datetime.datetime,
    expected: str,
) -> None:
    evaluator = DuckDBEvaluator({}, {})
    assert evaluator.evaluate(value) == expected
