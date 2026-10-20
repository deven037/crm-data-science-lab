# CRM Data Science

A local Python analysis project for the Practice CRM Data Studio. The CRM bridge saves selected datasets under `data/raw/` and runs `analysis.py` with the selected CSV.

## Run an analysis

```powershell
python analysis.py --dataset data/raw/example.csv --output-dir outputs
```

The script writes one JSON report to stdout. Generated reports, processed datasets, charts, local IDE settings, and practice CRM exports are excluded from Git.

Open this folder in PyCharm and edit `analysis.py` to build your own analysis. The Data Studio bridge runs locally on your computer; a GitHub copy does not run Python by itself.
