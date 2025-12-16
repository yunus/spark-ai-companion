# ==============================================================================
# Installation & Setup
# ==============================================================================

# Install dependencies using uv package manager
install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.8.13/install.sh | sh; source $HOME/.local/bin/env; }
	uv sync --dev

playground-adk-web:
	@echo "==============================================================================="
	@echo "| 🚀 Starting your agent playground...                                        |"
	@echo "|                                                                             |"
	@echo "| 🔍 IMPORTANT: Select the 'spark_companion' folder to interact with your agent.  |"
	@echo "==============================================================================="
	uv run adk web . --port 8501 --reload_agents

playground-full-ui:
	@echo "==============================================================================="
	@echo "| 🚀 Starting your agent playground...                                        |"
	@echo "|                                                                             |"
	@echo "| 💡 Try asking: Where can I find my dataproc container logs      			 |"
	@echo "==============================================================================="
	uv run uvicorn main:app --port 8000 --reload



# ==============================================================================
# Create docker container and deploy into cloud run
# ==============================================================================

configure-docker:
	gcloud auth configure-docker \
    us-central1-docker.pkg.dev

build-container: configure-docker
		gcloud builds submit \
			--gcs-log-dir gs://co-browsing-agent-utility/cloud_build/logs \
			--service-account projects/co-browsing-agent-1463/serviceAccounts/sa-project@co-browsing-agent-1463.iam.gserviceaccount.com \
			--region=us-central1 \
			--tag us-central1-docker.pkg.dev/co-browsing-agent-1463/containers/ai-companion:latest .
			--project=co-browsing-agent-1463

deploy-cloud-run: 
		gcloud beta run deploy \
			ai-companion \
			--region=us-central1 \
			--service-account sa-project@co-browsing-agent-1463.iam.gserviceaccount.com \
			--env-vars-file="production.env" \
			--allow-unauthenticated \
			--ingress internal-and-cloud-load-balancing \
			--no-iap \
			--timeout 60m \
			--session-affinity \
			--cpu 4 \
			--memory 8Gi \
			--min-instances 1 \
			--max-instances 10 \
			--image us-central1-docker.pkg.dev/co-browsing-agent-1463/containers/ai-companion:latest

# ==============================================================================
# Cloud IAP Permissions
# ==============================================================================
# _give-iam-to-cloud-iap:
# 	gcloud run services add-iam-policy-binding ai-companion \
# 		--region=us-central1 \
# 		--member=serviceAccount:service-439592077391@gcp-sa-iap.iam.gserviceaccount.com \
# 		--role=roles/run.invoker

# give-domain-access-to-cloud-iap: _give-iam-to-cloud-iap
# 	gcloud beta iap web add-iam-policy-binding \
# 		--member=domain:google.com \
# 		--role=roles/iap.httpsResourceAccessor \
# 		--region=us-central1 \
# 		--resource-type=cloud-run \
# 		--service=ai-companion \
# 		--project=co-browsing-agent-1463

# ==============================================================================
# Testing & Code Quality
# ==============================================================================

# Run code quality checks (codespell, ruff, mypy)
lint:
	uv sync --dev --extra lint
	uv run codespell
	uv run ruff check . --fix
	uv run ruff format .
#   uv run mypy .