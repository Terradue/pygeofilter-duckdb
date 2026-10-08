# Verified operators

Execution tests use in-memory DuckDB tables and assert result sets, including
nulls and typed timestamps. The scalar execution cases run through both the
literal and parameterized helpers.

| Behavior | Examples covered |
| --- | --- |
| Comparisons | `=`, `<>`, `<`, `<=`, `>`, `>=` |
| Boolean combinations | `AND`, `OR`, `NOT`, grouped expressions |
| Inclusive ranges | `BETWEEN`, `NOT BETWEEN` |
| Membership | `IN`, `NOT IN`; strings, numbers, booleans |
| Patterns | `LIKE`, negation, escape characters; `ILIKE` with evaluator configuration |
| Null checks | `IS NULL`, `IS NOT NULL` |
| Temporal values | Timestamp equality, ordering, ranges, timezone-equivalent instants |
| Mapped functions | Allowlisted `lower` and qualified function names |
| Arrays | Literal and bound element rendering and execution |
| Spatial | Intersection; native geometry, decoded WKB, GeoParquet; bound geometry/envelope/bounding box |

Pattern `%` and `_` remain wildcards. Binding a pattern prevents SQL syntax
injection but does not turn a wildcard search into literal equality.

SQL three-valued logic applies: comparisons against NULL usually produce NULL,
and WHERE selects only TRUE. Negation does not turn an unknown comparison into
TRUE.

Use explicit null checks when null rows should be selected.

This table records verified behavior rather than asserting complete CQL
conformance. Other operator behavior can be inherited from pygeofilter's
`SQLEvaluator`; establish execution tests before relying on additional operators
in a gateway.

Parser failures and HTTP responses are separate application
contracts. See [restricting client filters](../how-to/restrict-client-filters.md).
