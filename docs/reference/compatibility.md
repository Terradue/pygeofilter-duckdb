# Dependencies and verified compatibility

The project declares Python `>=3.10`, DuckDB `>=1.1.3,<1.6.0`, and pygeofilter
`>=0.4.0,<0.5.0`. Python 3.14 and later require DuckDB `>=1.4.2,<1.6.0`
to use compatible wheels. The CI compatibility matrix is:

| Python | DuckDB | pygeofilter |
| --- | --- | --- |
| 3.11, 3.12 | 1.1.3 | 0.4.0 |
| 3.11, 3.12 | 1.2.0 | 0.4.0 |
| 3.11, 3.12 | 1.5.6 | 0.4.0 |

These representative releases cover the oldest tested DuckDB baseline, the
previously excluded 1.2 boundary, and the modern target reviewed on 2026-10-08.

A separate Hatch matrix checks Python 3.10–3.14 with resolved dependencies.
These checks do not prove compatibility with every intervening dependency release. Upper bounds reserve the next minor dependency releases for
another review.

Pygeofilter 0.2.4 failed four parser cases covering negated membership/ranges.
Version 0.4.0 is the oldest tested passing baseline; this does not establish
which intermediate release first fixed those cases.

Most operator behavior is
inherited from pygeofilter, so it participates in the compatibility matrix.

The separate `example/requirements.txt` pins the full notebook environment,
including DuckDB 1.1.3, pygeofilter 0.4.0, stac-geoparquet 0.8.2, and upstream
PySTAC 1.15.2.

`docs/requirements.txt` pins the documentation builder. Runtime
requirements and development or notebook pins serve different purposes.

When changing a dependency boundary, run collected execution and spatial tests
on the old baseline, the boundary version, and the intended target with
compatible Python versions. Rerun notebooks when changing their baseline.
