# CRM Data Science

A local Python analysis project for the Practice CRM Data Studio. The CRM bridge saves selected datasets under `data/raw/` and runs `analysis.py` with the selected CSV.

## Run an analysis

```powershell
python analysis.py --dataset data/raw/example.csv --output-dir outputs
```

The script writes one JSON report to stdout. Generated reports, processed datasets, charts, local IDE settings, and practice CRM exports are excluded from Git.

Open this folder in PyCharm and edit `analysis.py` to build your own analysis. The Data Studio bridge runs locally on your computer; a GitHub copy does not run Python by itself.

## Hosted analysis workflow

The CRM can trigger this repository's `CRM dataset analysis` GitHub Actions workflow. The dataset is held temporarily by the CRM API and fetched by the runner over HTTPS; it is not committed to this repository or uploaded as an Actions artifact. The workflow captures script output and sends the JSON report back to the authenticated CRM API.

Before hosted analysis is enabled, configure:

- In the CRM API host (for example, Render): `ANALYSIS_GITHUB_REPOSITORY=deven037/crm-data-science-lab`, `ANALYSIS_GITHUB_REF=main`, `ANALYSIS_GITHUB_TOKEN` (a fine-grained token with Actions: write on this repository), `ANALYSIS_WORKFLOW_SECRET` (a random secret), and `PUBLIC_API_URL` (the public base URL of the CRM API).
- In this repository's Actions settings: add `ANALYSIS_WORKFLOW_SECRET` with the same random secret. The CRM API base URL is passed in the workflow dispatch input.

Keep all credentials out of the frontend and source control. The API limits datasets to 20 MB and 50,000 rows, limits each signed-in user to ten workflow requests per hour, and expires in-memory job data after ten minutes. Analysis runs for at most 120 seconds. Workflow output files and charts are temporary and are not returned; the report is returned to the signed-in CRM user.


