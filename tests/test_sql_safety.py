"""Execute filters with adversarial identifiers, patterns, and function mappings."""

from collections.abc import Callable

import duckdb
import pyarrow as pa
import pytest
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse

from pygeofilter_duckdb import to_sql_where
from pygeofilter_duckdb.evaluate import DuckDBEvaluator

# The upstream Attribute constructor is untyped.
attribute: Callable[[str], ast.Attribute] = ast.Attribute


@pytest.mark.parametrize(
    "field", ["ordinary", 'a"b', 'name") OR TRUE --', 'x"; DROP TABLE items; --']
)
def test_mapped_identifier_is_one_column(field: str) -> None:
    root = parse({"op": "=", "args": [{"property": "public"}, "match"]})
    assert isinstance(root, ast.Node)
    predicate = to_sql_where(root, {"public": field})
    with duckdb.connect() as connection:
        connection.register(
            "items", pa.table({"id": [1, 2], field: ["match", "other"]})
        )
        assert connection.execute(
            "SELECT id FROM items WHERE " + predicate
        ).fetchall() == [(1,)]


@pytest.mark.parametrize(
    "pattern", ["O'Brien", "' OR TRUE --", "'; DROP TABLE items; --", "café's"]
)
def test_quoted_like_patterns_match_only_data(pattern: str) -> None:
    root = parse({"op": "like", "args": [{"property": "name"}, pattern]})
    assert isinstance(root, ast.Node)
    predicate = to_sql_where(root, {"name": "name"})
    with duckdb.connect() as connection:
        connection.register(
            "items", pa.table({"id": [1, 2, 3], "name": [pattern, "other", None]})
        )
        assert connection.execute(
            "SELECT id FROM items WHERE " + predicate
        ).fetchall() == [(1,)]


@pytest.mark.parametrize(
    ("pattern", "escape", "value"),
    [("O'%Brien", "'", "O%Brien"), ("a!_b", "!", "a_b"), ("a%", "", "abc")],
)
def test_like_escape_character_execution(pattern: str, escape: str, value: str) -> None:
    node = ast.Like(attribute("name"), pattern, False, "%", "_", escape, False)
    predicate = to_sql_where(node, {"name": "name"})
    with duckdb.connect() as connection:
        assert connection.execute(
            "SELECT ? AS name WHERE " + predicate, [value]
        ).fetchall() == [(value,)]


@pytest.mark.parametrize(
    ("nocase", "negated", "expected"),
    [(False, False, []), (True, False, [(1,)]), (True, True, [(2,)])],
)
def test_like_case_and_negation(
    nocase: bool, negated: bool, expected: list[tuple[int]]
) -> None:
    node = ast.Like(attribute("name"), "O'B%", nocase, "%", "_", "\\", negated)
    evaluator = DuckDBEvaluator({"name": "name"}, {}, use_ilike=True)
    predicate = evaluator.evaluate(node)
    with duckdb.connect() as connection:
        connection.register(
            "items", pa.table({"id": [1, 2, 3], "name": ["o'brien", "other", None]})
        )
        assert (
            connection.execute("SELECT id FROM items WHERE " + predicate).fetchall()
            == expected
        )


def test_allowlisted_function_escapes_arguments() -> None:
    root = parse(
        {
            "op": "=",
            "args": [
                {"function": {"name": "normalize", "arguments": ["O'BRIEN"]}},
                "o'brien",
            ],
        }
    )
    assert isinstance(root, ast.Node)
    predicate = to_sql_where(root, {}, {"normalize": "lower"})
    with duckdb.connect() as connection:
        assert connection.execute("SELECT 1 WHERE " + predicate).fetchall() == [(1,)]


def test_qualified_function_mapping() -> None:
    root = ast.Function("normalize", ["O'BRIEN"])
    sql = to_sql_where(root, {}, {"normalize": "main.lower"})
    with duckdb.connect() as connection:
        assert connection.execute("SELECT " + sql).fetchone() == ("o'brien",)


@pytest.mark.parametrize("name", ["missing", 'name") OR TRUE --'])
def test_unknown_property_rejected(name: str) -> None:
    root = ast.Equal(attribute(name), "value")
    with pytest.raises(KeyError) as error:
        to_sql_where(root, {"allowed": "name"})
    assert error.value.args == (name,)


@pytest.mark.parametrize("name", ["missing", "lower); SELECT 1 --"])
def test_unknown_function_rejected(name: str) -> None:
    with pytest.raises(KeyError) as error:
        to_sql_where(ast.Function(name, ["value"]), {}, {"allowed": "lower"})
    assert error.value.args == (name,)


@pytest.mark.parametrize(
    "mapped",
    [
        "",
        "lower); SELECT 1 --",
        "lower /* comment */",
        "lower(value)",
        "lower; DROP TABLE items",
        '"lower"',
    ],
)
def test_function_mapping_rejects_sql_fragments(mapped: str) -> None:
    with pytest.raises(ValueError, match="Mapped functions"):
        to_sql_where(ast.Function("allowed", ["value"]), {}, {"allowed": mapped})


@pytest.mark.parametrize("pattern", [7, attribute("name")])
def test_non_string_like_pattern_rejected(pattern: int | ast.Attribute) -> None:
    root = ast.Like(attribute("name"), pattern, False, "%", "_", "\\", False)
    with pytest.raises(ValueError, match="LIKE patterns"):
        to_sql_where(root, {"name": "name"})


def test_multiple_escape_characters_rejected() -> None:
    root = ast.Like(attribute("name"), "value", False, "%", "_", "ab", False)
    with pytest.raises(ValueError, match="escape characters"):
        to_sql_where(root, {"name": "name"})


@pytest.mark.parametrize(
    "value", ["O'Brien", "' OR TRUE --", "both '\" quotes", r"\' OR TRUE --"]
)
def test_array_elements_escape_string_literals(value: str) -> None:
    root = parse({"op": "=", "args": [{"property": "names"}, [value]]})
    assert isinstance(root, ast.Node)
    predicate = to_sql_where(root, {"names": "names"})
    with duckdb.connect() as connection:
        connection.register(
            "items", pa.table({"id": [1, 2], "names": [[value], ["other"]]})
        )
        assert connection.execute(
            "SELECT id FROM items WHERE " + predicate
        ).fetchall() == [(1,)]
