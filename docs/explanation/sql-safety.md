# Values, identifiers, and functions

SQL values and SQL structure have different contracts. An apostrophe inside a
string must remain data: the literal API doubles apostrophes, so `O'Brien`
becomes `'O''Brien'`.

Execution tests include quoted and injection-shaped values and assert that they
match only the stored literal data.

The parameterized API separates literal values from SQL syntax: SQL contains
`?` placeholders, and DuckDB receives the values in a separate list. Geometry
constructors also use bound values. This avoids assembling SQL string literals
for client values, while leaving the original string API available.

Parameters bind values; names in the query require separate controls:

- **Properties** resolve through an application-controlled mapping to one
  quoted identifier, with embedded double quotes doubled.
- **Functions** resolve through an allowlist of ordinary or dot-qualified SQL
  names.
- **Unknown properties or functions** are rejected during translation.

These protections do not replace authorization. An allowlisted function can
still be inappropriate for a public endpoint, and expensive expressions can
consume resources. Applications own the mappings, surrounding query, and
supported operator contract.

Tests establish the covered cases; they do not constitute a complete security
audit of every inherited evaluator path.

For application setup, see [restrict client filters](../how-to/restrict-client-filters.md).
