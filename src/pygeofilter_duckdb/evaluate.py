"""Translate parsed OGC filters into SQL expressions for DuckDB."""

import datetime
import re

import shapely.geometry
from pygeofilter import ast, values
from pygeofilter.backends.evaluator import handle
from pygeofilter.backends.sql.evaluate import SQLEvaluator

SQLParameter = (
    str
    | int
    | float
    | bool
    | datetime.datetime
    | datetime.date
    | datetime.time
    | datetime.timedelta
)


class DuckDBEvaluator(SQLEvaluator):
    """Render filter expressions with DuckDB spatial geometry constructors."""

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute) -> str:
        """Render a mapped property as a quoted SQL identifier.

        Args:
            node: Property reference from the parsed filter.

        Returns:
            Identifier with embedded double quotes escaped.

        Raises:
            KeyError: If the property is absent from the field mapping.
        """
        field = self.attribute_map[node.name].replace('"', '""')
        return f'"{field}"'

    @handle(ast.Function)
    def function(self, node: ast.Function, *arguments: str) -> str:
        """Render a function approved by the caller's function mapping.

        Args:
            node: Function reference from the parsed filter.
            arguments: Rendered SQL expressions for its arguments.

        Returns:
            SQL call using a simple or schema-qualified function name.

        Raises:
            KeyError: If the function is absent from the function mapping.
            ValueError: If the mapped name contains SQL syntax beyond a name.
        """
        function = self.function_map[node.name]
        if not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_$]*(?:\.[A-Za-z_][A-Za-z0-9_$]*)*", function
        ):
            raise ValueError(
                "Mapped functions must be simple or schema-qualified names"
            )
        return f"{function}({','.join(arguments)})"

    @handle(ast.Like)
    def like(self, node: ast.Like, lhs: str) -> str:
        """Render a pattern predicate with escaped SQL string literals.

        Args:
            node: Pattern predicate with wildcard and escape settings.
            lhs: Rendered SQL expression to match against the pattern.

        Returns:
            LIKE or ILIKE predicate, including negation and escape settings.

        Raises:
            ValueError: If the pattern is not a string or escape settings
                cannot be represented by DuckDB.
        """
        if not isinstance(node.pattern, str):
            raise ValueError("LIKE patterns must be strings")
        if len(node.escapechar) > 1:
            raise ValueError(
                "LIKE escape characters must contain at most one character"
            )
        if len(node.wildcard) != 1 or len(node.singlechar) != 1:
            raise ValueError("LIKE wildcards must each contain one character")
        pattern = node.pattern
        if node.wildcard != "%":
            pattern = pattern.replace(node.wildcard, "%")
        if node.singlechar != "_":
            pattern = pattern.replace(node.singlechar, "_")
        operator = "ILIKE" if node.nocase and self.use_ilike else "LIKE"
        negation = "NOT " if node.not_ else ""
        return (
            f"{lhs} {negation}{operator} {self.literal(pattern)} "
            f"ESCAPE {self.literal(node.escapechar)}"
        )

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry) -> str:
        """Render a geometry literal as a DuckDB SQL expression.

        Args:
            node: Geometry literal from the parsed filter.

        Returns:
            SQL expression constructing the geometry from hexadecimal WKB.
        """
        wkb_hex = shapely.geometry.shape(node).wkb_hex
        return f"ST_GeomFromHEXEWKB('{wkb_hex}')"

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope) -> str:
        """Render a bounding envelope as a DuckDB SQL geometry expression.

        Args:
            node: Envelope containing the minimum and maximum coordinates.

        Returns:
            SQL expression constructing the rectangular envelope geometry.
        """
        wkb_hex = shapely.geometry.box(node.x1, node.y1, node.x2, node.y2).wkb_hex
        return f"ST_GeomFromHEXEWKB('{wkb_hex}')"

    @handle(*values.LITERALS)
    def literal(self, node: ast.AstType) -> str:
        """Render a filter literal for inclusion in a SQL expression.

        Args:
            node: Literal value from the parsed filter.

        Returns:
            Strings and datetimes enclosed in single quotes, or other literal
            values rendered as SQL tokens. List elements are evaluated
            individually. Embedded string quotes are doubled for SQL.
        """
        if isinstance(node, str):
            escaped = node.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(node, datetime.datetime):
            return f"'{node}'"
        elif isinstance(node, list):
            return f"[{','.join(self.evaluate(value) for value in node)}]"
        else:
            return str(node)


class _ParameterizedDuckDBEvaluator(DuckDBEvaluator):
    """Collect bound values while retaining DuckDB filter rendering handlers."""

    def __init__(
        self, field_mapping: dict[str, str], function_map: dict[str, str]
    ) -> None:
        super().__init__(field_mapping, function_map)
        self.parameters: list[SQLParameter] = []

    @handle(*values.LITERALS)
    def literal(self, node: ast.AstType) -> str:
        """Render literal values as placeholders in parameter traversal order."""
        if isinstance(node, list):
            return f"[{','.join(self.evaluate(value) for value in node)}]"
        if not isinstance(
            node,
            (str, int, float, bool, datetime.date, datetime.time, datetime.timedelta),
        ):
            raise TypeError("Unsupported bound literal type")
        self.parameters.append(node)
        return "?"

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry) -> str:
        """Construct a geometry using bound hexadecimal WKB."""
        wkb_hex = shapely.geometry.shape(node).wkb_hex
        return f"ST_GeomFromHEXEWKB({self.literal(wkb_hex)})"

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope) -> str:
        """Construct an envelope using bound hexadecimal WKB."""
        wkb_hex = shapely.geometry.box(node.x1, node.y1, node.x2, node.y2).wkb_hex
        return f"ST_GeomFromHEXEWKB({self.literal(wkb_hex)})"

    @handle(ast.BBox)
    def bbox(self, node: ast.BBox, lhs: str) -> str:
        """Render a bounding-box predicate with a bound geometry literal."""
        wkb_hex = shapely.geometry.box(
            node.minx, node.miny, node.maxx, node.maxy
        ).wkb_hex
        return f"ST_Intersects({lhs},ST_GeomFromHEXEWKB({self.literal(wkb_hex)}))"


def to_sql_where_params(
    root: ast.Node,
    field_mapping: dict[str, str],
    function_map: dict[str, str] | None = None,
) -> tuple[str, list[SQLParameter]]:
    """Translate a filter into DuckDB SQL and separately bound literal values.

    Args:
        root: Root node of the parsed filter expression.
        field_mapping: Server-controlled mapping of properties to database fields.
        function_map: Optional server-controlled allowlist of SQL function names.

    Returns:
        SQL predicate containing positional placeholders and its ordered values.
        Pass both to DuckDB execute; each call returns an independent value list.

    Raises:
        KeyError: If a property or function is absent from its mapping.
        ValueError: If a mapped function or pattern setting is invalid.
        TypeError: If a literal is unsupported or evaluation does not produce SQL.
    """
    evaluator = _ParameterizedDuckDBEvaluator(field_mapping, function_map or {})
    result = evaluator.evaluate(root)
    if not isinstance(result, str):
        raise TypeError("Filter evaluation must produce a SQL expression")
    return result, evaluator.parameters


def to_sql_where(
    root: ast.Node,
    field_mapping: dict[str, str],
    function_map: dict[str, str] | None = None,
) -> str:
    """Translate a parsed filter into a DuckDB SQL WHERE expression.

    Args:
        root: Root node of the parsed filter expression.
        field_mapping: Mapping from filter property names to database fields.
        function_map: Optional mapping from filter function names to SQL
            function names.

    Returns:
        SQL predicate to place after the WHERE keyword.

    Raises:
        KeyError: If a property or function is not present in its mapping.
        ValueError: If a function mapping or pattern setting is invalid.
        TypeError: If evaluation does not produce a SQL expression.
    """
    result = DuckDBEvaluator(field_mapping, function_map or {}).evaluate(root)
    if not isinstance(result, str):
        raise TypeError("Filter evaluation must produce a SQL expression")
    return result
