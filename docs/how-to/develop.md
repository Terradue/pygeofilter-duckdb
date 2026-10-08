# Develop and build documentation

Install Hatch, then run the project's non-mutating quality gates:

```bash
# Check formatting and lint rules without rewriting source files.
hatch run dev:format-check
hatch run dev:lint-check
# Verify static types, scan production code, and run the test suite.
hatch run dev:typecheck
hatch run dev:security
hatch run test:test
```

Confirm test discovery with `hatch run test:pytest --collect-only -q`.
Spatial tests install and load the DuckDB spatial extension and fail if it cannot
be loaded. To share an existing extension cache, set
`PYGEOFILTER_SPATIAL_EXTENSION_DIRECTORY` to its directory.

Build or preview this site from the repository root:

```bash
# Generate site/ and fail on documentation warnings.
hatch run docs:build
# Preview locally at http://127.0.0.1:8089 with automatic rebuilds.
hatch run docs:serve
```

Alternatively, install `docs/requirements.txt` and run
`mkdocs build --strict` or `mkdocs serve`. The generated site is in `site/` and
is ignored by Git.

Keep documentation in the relevant Diátaxis section:
tutorials teach through complete exercises, how-to guides solve tasks,
reference specifies contracts, and explanation describes design choices.

The root `.readthedocs.yaml` configures Read the Docs to build `mkdocs.yml` with
Python 3.11 and the pinned documentation requirements.

To host the site, import
the repository into a Read the Docs project and enable its repository integration.
Adding this configuration alone does not create or publish a hosted project.
