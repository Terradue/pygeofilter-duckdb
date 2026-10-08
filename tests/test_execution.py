"""Execute parsed filters against typed DuckDB rows to verify result semantics."""

from collections.abc import Callable, Iterator

import duckdb
import pytest
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse as parse_json
from pygeofilter.parsers.cql2_text import parse

from pygeofilter_duckdb import to_sql_where, to_sql_where_params

# The text parser is untyped; validate its result before SQL conversion.
parse_text: Callable[[str], object] = parse


@pytest.fixture
def connection() -> Iterator[duckdb.DuckDBPyConnection]:
    """Provide typed rows with inclusive boundaries and nullable properties."""
    with duckdb.connect(":memory:") as database:
        database.execute(
            "CREATE TABLE items (id INTEGER, score INTEGER, name VARCHAR, "
            "active BOOLEAN, observed TIMESTAMPTZ)"
        )
        database.executemany(
            "INSERT INTO items VALUES (?, ?, ?, ?, ?)",
            [
                (1, 10, "alpha", True, "2023-02-01T00:00:00Z"),
                (2, 20, "alpine", False, "2023-02-02T00:00:00Z"),
                (3, 30, "beta", True, "2023-02-03T00:00:00Z"),
                (4, None, None, None, None),
                (5, 0, "", False, "2023-01-31T23:59:59Z"),
            ],
        )
        yield database


@pytest.mark.parametrize("parameterized", [False, True])
@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("score = 20", [2]),
        ("score <> 20", [1, 3, 5]),
        ("score < 20", [1, 5]),
        ("score <= 20", [1, 2, 5]),
        ("score > 20", [3]),
        ("score >= 20", [2, 3]),
        ("score >= 10 AND score <= 20", [1, 2]),
        ("score < 10 OR score > 20", [3, 5]),
        ("NOT (score = 20)", [1, 3, 5]),
        ("(score = 10 OR score = 20) AND active = TRUE", [1]),
        ("score BETWEEN 10 AND 20", [1, 2]),
        ("score NOT BETWEEN 10 AND 20", [3, 5]),
        ("name IN ('alpha', 'beta')", [1, 3]),
        ("name NOT IN ('alpha', 'beta')", [2, 5]),
        ("score NOT IN (10, 20)", [3, 5]),
        ("score IN (10.0, 20.0, 20.5)", [1, 2]),
        ("score IN (-1, 0, 10)", [1, 5]),
        ("active IN (TRUE, FALSE)", [1, 2, 3, 5]),
        ("score IS NULL", [4]),
        ("score IS NOT NULL", [1, 2, 3, 5]),
        ("name = ''", [5]),
        ("active = TRUE", [1, 3]),
        ("active = FALSE", [2, 5]),
        ("score = 20 OR score IS NULL", [2, 4]),
        (
            "observed BETWEEN TIMESTAMP('2023-02-01T00:00:00Z') "
            "AND TIMESTAMP('2023-02-02T00:00:00Z')",
            [1, 2],
        ),
        ("observed = TIMESTAMP('2023-02-01T01:00:00+01:00')", [1]),
        ("observed > TIMESTAMP('2023-02-02T00:00:00Z')", [3]),
        ("observed IS NULL", [4]),
    ],
)
def test_filter_result_ids(
    connection: duckdb.DuckDBPyConnection,
    expression: str,
    expected: list[int],
    parameterized: bool,
) -> None:
    root = parse_text(expression)
    assert isinstance(root, ast.Node)
    fields = {name: name for name in ("score", "name", "active", "observed")}
    if parameterized:
        predicate, parameters = to_sql_where_params(root, fields)
    else:
        predicate, parameters = to_sql_where(root, fields), []
    rows = connection.execute(
        "SELECT id FROM items WHERE " + predicate + " ORDER BY id", parameters
    ).fetchall()
    assert rows == [(identifier,) for identifier in expected]


@pytest.mark.parametrize("parameterized", [False, True])
@pytest.mark.parametrize(
    ("pattern", "expected"), [("al%", [1, 2]), ("bet_", [3]), ("missing%", [])]
)
def test_pattern_matching(
    connection: duckdb.DuckDBPyConnection,
    pattern: str,
    expected: list[int],
    parameterized: bool,
) -> None:
    root = parse_json({"op": "like", "args": [{"property": "name"}, pattern]})
    assert isinstance(root, ast.Node)
    if parameterized:
        predicate, parameters = to_sql_where_params(root, {"name": "name"})
    else:
        predicate, parameters = to_sql_where(root, {"name": "name"}), []
    rows = connection.execute(
        "SELECT id FROM items WHERE " + predicate + " ORDER BY id", parameters
    ).fetchall()
    assert rows == [(identifier,) for identifier in expected]


@pytest.mark.parametrize("parameterized", [False, True])
def test_numeric_membership(connection: duckdb.DuckDBPyConnection, parameterized: bool) -> None:
    root = parse_text("score IN (10, 20)")
    assert isinstance(root, ast.Node)
    if parameterized:
        predicate, parameters = to_sql_where_params(root, {"score": "score"})
    else:
        predicate, parameters = to_sql_where(root, {"score": "score"}), []
    assert connection.execute(
        "SELECT id FROM items WHERE " + predicate + " ORDER BY id", parameters
    ).fetchall() == [(1,), (2,)]
