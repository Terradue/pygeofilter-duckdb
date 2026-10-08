"""Translate parsed OGC filters into SQL expressions for DuckDB."""

from typing import Dict, Optional
import datetime
import shapely.geometry

from pygeofilter import ast, values
from pygeofilter.backends.evaluator import handle
from pygeofilter.backends.sql.evaluate import SQLEvaluator


class DuckDBEvaluator(SQLEvaluator):
    """Render filter expressions with DuckDB spatial geometry constructors."""

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        """Render a geometry literal as a DuckDB SQL expression.

        Args:
            node: Geometry literal from the parsed filter.

        Returns:
            SQL expression constructing the geometry from hexadecimal WKB.
        """
        wkb_hex = shapely.geometry.shape(node).wkb_hex
        return f"ST_GeomFromHEXEWKB('{wkb_hex}')"

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        """Render a bounding envelope as a DuckDB SQL geometry expression.

        Args:
            node: Envelope containing the minimum and maximum coordinates.

        Returns:
            SQL expression constructing the rectangular envelope geometry.
        """
        wkb_hex = shapely.geometry.box(node.x1, node.y1, node.x2, node.y2).wkb_hex
        return f"ST_GeomFromHEXEWKB('{wkb_hex}')"

    @handle(*values.LITERALS)
    def literal(self, node):
        """Render a filter literal for inclusion in a SQL expression.

        Args:
            node: Literal value from the parsed filter.

        Returns:
            Strings and datetimes enclosed in single quotes, or other literal
            values unchanged. Embedded string quotes are doubled for SQL.
        """
        if isinstance(node, str):
            escaped = node.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(node, datetime.datetime):
            return f"'{node}'"
        else:
            return node


def to_sql_where(
    root: ast.Node,
    field_mapping: Dict[str, str],
    function_map: Optional[Dict[str, str]] = None,
) -> str:
    """Translate a parsed filter into a DuckDB SQL WHERE expression.

    Args:
        root: Root node of the parsed filter expression.
        field_mapping: Mapping from filter property names to database fields.
        function_map: Optional mapping from filter function names to SQL
            function names.

    Returns:
        SQL predicate to place after the WHERE keyword.
    """
    return DuckDBEvaluator(field_mapping, function_map or {}).evaluate(root)
