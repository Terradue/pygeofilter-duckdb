# SPDX-FileCopyrightText: 2025-present Fabrice Brito <fabrice.brito@terradue.com>
#
# SPDX-License-Identifier: MIT

"""Expose conversion of parsed OGC filters to DuckDB SQL predicates."""

from pygeofilter_duckdb.evaluate import to_sql_where

__all__ = ["to_sql_where"]
