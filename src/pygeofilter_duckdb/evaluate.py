from typing import Dict, Optional
import datetime
import shapely.geometry

from pygeofilter import ast, values
from pygeofilter.backends.evaluator import handle
from pygeofilter.backends.sql.evaluate import SQLEvaluator


class DuckDBEvaluator(SQLEvaluator):
    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        wkb_hex = shapely.geometry.shape(node).wkb_hex
        return f"ST_GeomFromHEXEWKB('{wkb_hex}')"

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        wkb_hex = shapely.geometry.box(node.x1, node.y1, node.x2, node.y2).wkb_hex
        return f"ST_GeomFromHEXEWKB('{wkb_hex}')"

    @handle(*values.LITERALS)
    def literal(self, node):
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
    return DuckDBEvaluator(field_mapping, function_map or {}).evaluate(root)
