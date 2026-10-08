# How filters become queries

Pygeofilter parses CQL2 JSON or text into an abstract syntax tree.
`DuckDBEvaluator` extends its SQL evaluator with DuckDB-specific decorated
handlers. It resolves property and function names using application mappings,
then returns an expression suitable for a WHERE clause.

The original helper produces SQL containing rendered literals. The additional
parameterized helper uses the same evaluator approach and produces SQL plus
ordered values. This preserves the existing API while allowing applications
to bind values through DuckDB's execution API.

The application completes the pipeline: choose the table or view, load required
extensions, append the generated predicate to a trusted query structure,
execute it, and interpret results.

Translation alone cannot establish that a
column exists, that types match, or that the returned rows are correct.
Execution tests cover those properties on small, inspectable fixtures.

Property mappings describe identifiers rather than arbitrary SQL. A view is the
place to decode WKB or expose a derived column. This keeps the evaluator's
existing architecture and makes ingestion behavior explicit.

The library is not an HTTP gateway. Supported client operators, authorization,
request limits, and invalid-expression responses remain application decisions.
