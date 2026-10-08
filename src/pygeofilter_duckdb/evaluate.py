# Copyright 2025 Terradue
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Translate pygeofilter expressions into DuckDB SQL predicates."""

from __future__ import annotations

import datetime
from typing import TypeAlias

import shapely.geometry
from pygeofilter import ast, values
from pygeofilter.backends.evaluator import handle
from pygeofilter.backends.sql.evaluate import SQLEvaluator

Literal: TypeAlias = (
    list[object] | str | float | int | bool | datetime.date | datetime.time | datetime.timedelta
)


class DuckDBEvaluator(SQLEvaluator):
    """Render SQL expressions with DuckDB geometry and timestamp literals."""

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry) -> str:
        """Render a geometry as a DuckDB hexadecimal WKB constructor."""
        wkb_hex = shapely.geometry.shape(node).wkb_hex
        return f"ST_GeomFromHEXEWKB('{wkb_hex}')"

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope) -> str:
        """Render an envelope as a DuckDB polygon constructor."""
        wkb_hex = shapely.geometry.box(node.x1, node.y1, node.x2, node.y2).wkb_hex
        return f"ST_GeomFromHEXEWKB('{wkb_hex}')"

    @handle(*values.LITERALS)
    def literal(self, node: Literal) -> Literal:
        """Quote strings and timestamps, preserving other literal values."""
        if isinstance(node, (str, datetime.datetime)):
            return f"'{node}'"
        return node


def to_sql_where(
    root: ast.Node,
    field_mapping: dict[str, str],
    function_map: dict[str, str] | None = None,
) -> str:
    """Render an expression as a DuckDB SQL WHERE clause without the keyword.

    Args:
        root: Parsed filter expression.
        field_mapping: Mapping from filter properties to SQL column names.
        function_map: Mapping from filter functions to SQL function names.

    Raises:
        TypeError: If evaluation does not produce a SQL expression string.
    """
    result = DuckDBEvaluator(field_mapping, function_map or {}).evaluate(root)
    if not isinstance(result, str):
        raise TypeError("Expected a SQL expression string from the filter evaluator")
    return result
