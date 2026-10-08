# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-08

### Added

- `to_sql_where_params()` returns a SQL predicate and ordered bound values for
  scalar, timestamp, array, pattern, and spatial literals.
- DuckDB execution tests for logical and comparison operators, nulls, timestamps,
  mapped functions, arrays, and spatial queries over native geometry, WKB, and
  GeoParquet data.
- MkDocs tutorials, how-to guides, API and compatibility references, and
  explanations of SQL safety and geometry storage, with Read the Docs support.
- Hatch documentation commands, strict typing, formatting, lint, and security
  checks, plus a Python 3.10–3.14 test matrix and DuckDB compatibility CI.

### Changed

- **Breaking:** Require DuckDB `>=1.1.3,<1.6.0` and pygeofilter `>=0.4.0,<0.5.0`.
  Python 3.14 and later require DuckDB `>=1.4.2,<1.6.0`.
- **Breaking:** Mapped SQL functions must use simple or schema-qualified names;
  invalid function names and unsupported LIKE settings now raise `ValueError`.
- Adopt the Apache License 2.0 with attribution in `NOTICE`.
- Document the geometry-column contract and pin notebook dependencies for
  reproducible examples.
- Publish to PyPI only on published GitHub releases, after quality and
  compatibility checks pass; validate documentation on pull requests.
- Include examples and documentation configuration in source distributions.

### Fixed

- Escape apostrophes in SQL strings and patterns, and double quotes in mapped
  identifiers.
- Render non-string literals as SQL tokens and evaluate array elements
  individually, including numeric membership and function arguments.
- Validate that filter evaluation returns a SQL expression string.
- Resolve strict typing and formatting errors, and use timezone constants
  compatible with Python 3.10 in tests.

## [0.1.0] - 2025-11-12

### Added

- Initial release

[Unreleased]: https://github.com/Terradue/pygeofilter-duckdb/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Terradue/pygeofilter-duckdb/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Terradue/pygeofilter-duckdb/releases/tag/v0.1.0
