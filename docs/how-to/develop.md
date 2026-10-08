# Develop and preview documentation

Run commands from a repository checkout. Install Hatch for package checks and
MkDocs for the documentation site:

```console
python -m pip install hatch 'mkdocs<2'
```

## Run quality checks and tests

```console
hatch run dev:format-check
hatch run dev:lint-check
hatch run dev:typecheck
hatch run dev:security
hatch run test:test
```

The first four commands are non-mutating checks. `test:test` runs the execution and spatial
suite across Python 3.10–3.14. Hatch may need network access to provision the
environments, dependencies, and DuckDB spatial extensions. Spatial fixtures also
validate STAC items against schemas that may require network access.

`hatch run dev:quality` groups the four static checks. `hatch run dev:check` adds
pytest in the development environment; it does not replace the full test matrix.
For one interpreter, use `hatch run +py=3.12 test:test`. To apply formatting and
lint fixes, use `hatch run dev:fix`.

## Build and preview the site

The restored Hatch documentation environment provides `hatch run docs:build`
and `hatch run docs:serve` (preview on `127.0.0.1:8089`). It pins the same MkDocs
version as `docs/requirements.txt` used by CI and Read the Docs.

```console
mkdocs build --strict
mkdocs serve
```

Open the local address printed by `serve`. The configuration is `mkdocs.yaml`.
The build validates documentation links and navigation and writes HTML to `site/`.
It does not execute Python examples or notebooks.

With Task and uv installed, `task build-docs` builds the site strictly and
`task serve-docs` starts the preview using an isolated MkDocs dependency.

## Maintain documentation

Keep tutorials focused on a guided exercise, how-to guides on specific tasks,
reference pages on exact behavior, and explanation pages on design context.
Check examples against the implementation and add new pages to `nav` in
`mkdocs.yaml`. Use relative links between documentation pages and run a strict
build before submitting changes.
