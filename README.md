# AI Companion

## Setup:
```sh
# create venv envitonment
python3 -m venv .venv

pip install -r requirements.txt

```

The application uses Vertex AI search tool, it requires to use Google Cloud Vertex AI endpoints and not the AI studio.
For that reason, you need to set application-default login. Also in .env file you should set the vertex ai endpoint. In .env.example there is already an example.


```sh
# Runt the code:
uvicorn main:app --reload

# navigate in your browser to localhost:8000
```

## Adding new cases

To make it easier to add new cases, we have created a [sheet](https://docs.google.com/spreadsheets/d/1y3ZBCgio05DUl--Vd_z-ORiv3JyVp_8gxTYPVBYqGOo/edit?gid=0#gid=0) where you can add more.
The sheet is loaded to a BigQuery external table. There is a [tiny pipeline](https://pantheon.corp.google.com/bigquery?e=13802955&inv=1&invt=Ab3nKg&mods=dm_deploy_from_gcs&project=ai-companion-pso-hack&ws=!1m6!1m5!19m4!1m3!1sai-companion-pso-hack!2seurope-west4!3s7ff392bf-e2e1-4d69-aec7-bab11f7fca58) which loads data from external table to a native table. It runs nightly but you can trigger manually when you have a new change.

After loading to the native table, you should also update the [vertex ai search](https://pantheon.corp.google.com/gen-app-builder/locations/global/engines/ai-companion-kb_1752576550130/data/documents?e=13802955&inv=1&invt=Ab3nKg&mods=dm_deploy_from_gcs&project=ai-companion-pso-hack) to re-index the data. That also happens nightly but you can manually trigger it.