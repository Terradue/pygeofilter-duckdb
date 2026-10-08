# Run the example notebooks

Use Python 3.11 and install the pinned notebook environment from the repository
root:

```bash
# Create and activate the Python environment used by the notebook baseline.
python3.11 -m venv .venv
. .venv/bin/activate
# Install this checkout and the pinned notebook dependencies together.
python -m pip install -e . -r example/requirements.txt
# Register this environment as a selectable kernel in your notebook editor.
python -m ipykernel install --user --name pygeofilter-duckdb
# Use this working directory so notebook-relative input/output paths resolve.
cd example
```

Open the notebooks in your notebook editor and select the
`pygeofilter-duckdb` kernel. Run with `example/` as the working directory:

1. `01-Create a geoparquet with STAC Items.ipynb`: convert local STAC Items to GeoParquet.
2. `02-Create a geoparquet file.ipynb`: obtain Sentinel-2 Items from Planetary Computer and write GeoParquet.
3. `03-DuckDB and geoparquet.ipynb`: query the file created by notebook 02.
4. `Query-STAC-Geoparquet.ipynb`: query a separate remote GeoParquet file.

Notebook 02 contacts a live STAC API; the separate query notebook downloads
remote data.

Spatial extension installation also needs network access unless
cached. Generated files are written relative to the working directory.
Remote availability and changing datasets can affect execution and results.

The pins in `example/requirements.txt` define a reproducible notebook baseline;
they do not narrow the library's declared dependency range. See
[compatibility](../reference/compatibility.md) for the versions verified.
