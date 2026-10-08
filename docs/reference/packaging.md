# Package build reference

The repository builds Python wheels and source distributions with Hatchling.
It does not currently contain a Dockerfile or a container publishing workflow.

## Build locally

From a checkout with Hatch installed:

```console
hatch build
```

Artifacts are written to `dist/`. The version is read from
`src/pygeofilter_duckdb/__about__.py`. The wheel contains the
`pygeofilter_duckdb` package; the source distribution also includes documentation,
tests, and license files as configured in `pyproject.toml`.

## Continuous integration and releases

`.github/workflows/package.yaml` runs formatting, lint, typing, security, and
coverage checks on Python 3.10–3.14. Releases use a strict `vX.Y.Z` tag whose
version must match `hatch version`. After the build jobs pass, the release job
builds distributions and publishes them to PyPI through trusted publishing.

`.github/workflows/docs.yaml` handles the documentation site separately. Building
the documentation locally does not publish either a package or a website.
