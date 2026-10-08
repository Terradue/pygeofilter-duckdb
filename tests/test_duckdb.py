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

import pytest
from pygeofilter import ast
from pygeofilter.parsers.cql2_json import parse as json_parse

from pygeofilter_duckdb import to_sql_where
from pygeofilter_duckdb.evaluate import DuckDBEvaluator


def test_duckdb() -> None:
    start = "2023-02-01T00:00:00Z"
    end = "2023-02-28T23:59:59Z"

    cql2_filter = {
        "op": "and",
        "args": [
            {"op": "between", "args": [{"property": "eo:cloud_cover"}, [0, 21]]},
            {"op": "between", "args": [{"property": "datetime"}, [start, end]]},
            {
                "op": "s_intersects",
                "args": [
                    {"property": "geometry"},
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [7.5113934084, 47.5338000528],
                                [10.4918239143, 47.5338000528],
                                [10.4918239143, 49.7913749328],
                                [7.5113934084, 49.7913749328],
                                [7.5113934084, 47.5338000528],
                            ]
                        ],
                    },
                ],
            },
        ],
    }

    root = json_parse(cql2_filter)
    assert isinstance(root, ast.Node)
    field_mapping = {name: name for name in ("eo:cloud_cover", "datetime", "geometry")}
    sql_where = to_sql_where(root, field_mapping)

    expected = "(((\"eo:cloud_cover\" BETWEEN 0 AND 21) AND (\"datetime\" BETWEEN '2023-02-01T00:00:00Z' AND '2023-02-28T23:59:59Z')) AND ST_Intersects(\"geometry\",ST_GeomFromHEXEWKB('0103000000010000000500000034DFB1B6AA0B1E4085B0648F53C44740509E1658D0FB244085B0648F53C44740509E1658D0FB244006A017C64BE5484034DFB1B6AA0B1E4006A017C64BE5484034DFB1B6AA0B1E4085B0648F53C44740')))"

    assert sql_where == expected


def test_rejects_non_string_evaluation_result(monkeypatch: pytest.MonkeyPatch) -> None:
    def evaluate(self: DuckDBEvaluator, node: ast.AstType, adopt_result: bool = True) -> int:
        return 1

    monkeypatch.setattr(DuckDBEvaluator, "evaluate", evaluate)

    with pytest.raises(TypeError, match="Expected a SQL expression string"):
        to_sql_where(ast.Equal(1, 1), {})
